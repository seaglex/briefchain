# Arbiter 异步任务队列设计

> 最后更新：2026-07-08

## 1. 设计目标

基于数据库实现异步任务队列，支持 Arbiter 审核的异步处理。核心要求：

- **最少外部依赖**——不引入 Redis、RabbitMQ 等中间件，直接使用现有数据库
- **接口抽象**——队列接口封装良好，与具体数据库解耦，可替换实现
- **事务安全**——取任务、完成任务、失败重试均在独立事务内，LLM 调用不持有数据库事务
- **健康回收**——worker 崩溃后，卡在 `processing` 状态的任务可被重新认领

## 2. 数据模型

### 2.1 队列表：`arbiter_review_tasks`

```sql
CREATE TABLE arbiter_review_tasks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),   -- PostgreSQL
    -- id        TEXT PRIMARY KEY,                              -- SQLite fallback
    review_id    UUID NOT NULL,                                -- FK → brief_arbiter_reviews.id
    brief_id     UUID NOT NULL,                                -- FK → briefs.brief_id（冗余，方便查询）
    skill_ids    JSON NOT NULL DEFAULT '[]',                   -- 需执行的 skill id 列表
    status       VARCHAR(16) NOT NULL DEFAULT 'pending',       -- pending / processing / done / failed
    retry_count  INTEGER NOT NULL DEFAULT 0,
    max_retries  INTEGER NOT NULL DEFAULT 3,
    error        TEXT,
    locked_at    TIMESTAMPTZ,
    finished_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 高效取 pending 任务
CREATE INDEX idx_tasks_pending ON arbiter_review_tasks (created_at)
    WHERE status = 'pending';

-- 健康回收：认领超时的 processing 任务
CREATE INDEX idx_tasks_processing_locked
    ON arbiter_review_tasks (locked_at)
    WHERE status = 'processing';
```

### 2.2 任务状态机

```
              ┌──────────┐
              │  pending  │
              └─────┬─────┘
                    │ dequeue（取任务）
                    ▼
              ┌──────────────┐
          ┌───│  processing  │───┐  locked_at > now() - 5min
          │   └──────┬───────┘   │  （健康回收 → 回到 pending）
          │          │           │
          │   ┌──────┴──────┐    │
          │   ▼              ▼    │
          │ ┌────┐        ┌──────┐│ retry_count < max_retries
          │ │done│        │failed ├│ （重置为 pending + 清空 locked_at）
          │ └────┘        └──┬───┘│
          │                  │    │
          │   retry_count >= max_retries
          │                  │
          │             ┌────▼────┐
          └─────────────│ failed  │（终态）
                        └─────────┘
```

## 3. 接口抽象

### 3.1 `AbstractQueueService`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


@dataclass
class QueueTask:
    """队列任务，跨越 DB 事务边界传输的最小数据单元。"""
    id: UUID
    review_id: UUID
    brief_id: UUID
    skill_ids: list[str]  # ["skill-completeness@v2", "skill-ambiguity@v1"]
    retry_count: int
    max_retries: int
    error: str | None = None


class AbstractQueueService(ABC):
    """数据库无关的异步任务队列接口。

    所有方法均在自己的数据库事务内执行。
    实现方需处理 FOR UPDATE SKIP LOCKED 的数据库差异。
    """

    @abstractmethod
    def enqueue(
        self,
        review_id: UUID,
        brief_id: UUID,
        skill_ids: list[str],
    ) -> QueueTask:
        """创建任务并入队。返回创建的 task。

        事务内：
        1. INSERT INTO arbiter_review_tasks (review_id, brief_id, skill_ids, status='pending')
        2. COMMIT
        """

    @abstractmethod
    def dequeue(self, visibility_timeout_seconds: int = 300) -> QueueTask | None:
        """取出一个待处理任务并标记为 processing。

        事务内：
        1. SELECT ... WHERE status='pending'
              OR (status='processing' AND locked_at < now() - visibility_timeout)
           ORDER BY created_at LIMIT 1
           FOR UPDATE SKIP LOCKED
        2. UPDATE SET status='processing', locked_at=now()
        3. COMMIT
        4. 返回 QueueTask（用于事务外处理）
        5. 无任务返回 None
        """

    @abstractmethod
    def mark_done(self, task_id: UUID) -> None:
        """标记任务完成。事务内 UPDATE + COMMIT。"""

    @abstractmethod
    def mark_failed(self, task_id: UUID, error: str) -> None:
        """标记任务失败（需重试或终态失败）。

        事务内：
        1. 如果 retry_count < max_retries：
           UPDATE SET status='pending', retry_count+1, error=?, locked_at=NULL
        2. 如果 retry_count >= max_retries：
           UPDATE SET status='failed', error=?, finished_at=now()
        3. COMMIT
        """

    @abstractmethod
    def touch_lock(self, task_id: UUID) -> None:
        """刷新锁时间，用于长时间执行的 task 避免被健康回收。
        事务内：UPDATE SET locked_at=now() WHERE id=?
        """
```

### 3.2 实现分派

通过配置动态选择实现，不依赖硬编码：

```python
# src/briefchain/queue/__init__.py
from src.briefchain.queue.base import AbstractQueueService
from src.briefchain.queue.postgres import PostgresQueueService
from src.briefchain.queue.sqlite import SQLiteQueueService


def create_queue_service(session_factory) -> AbstractQueueService:
    """根据数据库 URL 自动选择队列实现。"""
    from src.briefchain.api.config import get_settings
    db_type = get_settings().database_url.split("://")[0]

    if db_type == "postgresql":
        return PostgresQueueService(session_factory)
    if db_type == "sqlite":
        return SQLiteQueueService(session_factory)
    raise ValueError(f"Unsupported database type: {db_type}")
```

## 4. 数据库差异适配

### 4.1 PostgreSQL 实现

```python
class PostgresQueueService(AbstractQueueService):
    def dequeue(self, visibility_timeout_seconds: int = 300) -> QueueTask | None:
        with self.session_factory() as session:
            cutoff = datetime.utcnow() - timedelta(seconds=visibility_timeout_seconds)

            row = session.execute(
                select(ArbiterReviewTask)
                .where(
                    or_(
                        ArbiterReviewTask.status == TaskStatus.PENDING,
                        and_(
                            ArbiterReviewTask.status == TaskStatus.PROCESSING,
                            ArbiterReviewTask.locked_at < cutoff,
                        ),
                    )
                )
                .order_by(ArbiterReviewTask.created_at)
                .limit(1)
                .with_for_update(skip_locked=True)  # ← PostgreSQL 原生支持
            ).scalar_one_or_none()

            if row is None:
                session.commit()
                return None

            row.status = TaskStatus.PROCESSING
            row.locked_at = datetime.utcnow()
            session.commit()

            return QueueTask(
                id=row.id,
                review_id=row.review_id,
                brief_id=row.brief_id,
                skill_ids=row.skill_ids,
                retry_count=row.retry_count,
                max_retries=row.max_retries,
            )
```

### 4.2 SQLite 实现

SQLite 不支持 `FOR UPDATE SKIP LOCKED`，使用 `BEGIN IMMEDIATE` 事务 + 乐观锁：

```python
class SQLiteQueueService(AbstractQueueService):
    def dequeue(self, visibility_timeout_seconds: int = 300) -> QueueTask | None:
        from src.briefchain.queue.sqlite import _now_iso

        cutoff = _now_iso(offset=-visibility_timeout_seconds)

        with self.session_factory() as session:
            # SQLite 的 BEGIN IMMEDIATE 会立即获取写锁，等效于串行化
            # 单 worker 场景下无竞争；多 worker 场景下 natural serialization
            session.execute(text("BEGIN IMMEDIATE"))

            row = session.execute(
                select(ArbiterReviewTask)
                .where(
                    or_(
                        ArbiterReviewTask.status == TaskStatus.PENDING,
                        and_(
                            ArbiterReviewTask.status == TaskStatus.PROCESSING,
                            ArbiterReviewTask.locked_at < cutoff,
                        ),
                    )
                )
                .order_by(ArbiterReviewTask.created_at)
                .limit(1)
            ).scalar_one_or_none()

            if row is None:
                session.commit()
                return None

            # 以 status 作为乐观锁条件，防止多 worker 竞争
            result = session.execute(
                update(ArbiterReviewTask)
                .where(
                    ArbiterReviewTask.id == row.id,
                    ArbiterReviewTask.status == row.status,  # ← 乐观锁
                )
                .values(status=TaskStatus.PROCESSING, locked_at=_now_iso())
            )
            if result.rowcount == 0:
                # 被其他 worker 抢先了，回退
                session.commit()
                return None

            session.commit()
            return _to_queue_task(row)
```

## 5. 事务边界（关键约束）

**绝不在数据库事务内调用 LLM 或发送 HTTP 请求。**

```
取任务事务（dequeue）         LLM 调用（无事务）        完成任务事务（mark_done）
┌──────────────────┐        ┌──────────────┐        ┌──────────────────┐
│ BEGIN             │        │              │        │ BEGIN             │
│ SELECT ... FOR UP │        │ call_llm()   │        │ UPDATE task=done  │
│ UPDATE processing │        │   (5-30s)    │        │ UPDATE review=... │
│ COMMIT ← 事务结束  │        │              │        │ COMMIT            │
└──────────────────┘        └──────────────┘        └──────┬───────────┘
                                                           │
                                             ┌─────────────▼──────────┐
                                             │ fire_webhook(review_id) │
                                             │ （事务外，不阻塞）       │
                                             └────────────────────────┘
```

## 6. 与现有模型的集成

### 6.1 与 `brief_arbiter_reviews` 的关系

`arbiter_review_tasks` 是队列表，`brief_arbiter_reviews` 是结论表：

| 维度 | arbiter_review_tasks | brief_arbiter_reviews |
|------|---------------------|-----------------------|
| 用途 | 工作队列（取任务、重试、回收） | 审核结论（读给用户、关联 brief） |
| 生命周期 | done 后可归档清理 | 永久保留 |
| 读写模式 | 写多读少（worker 持续消费） | 写少读多（用户查看审核结果） |
| 索引 | status + created_at | brief_id + reviewed_at |

### 6.2 `brief_arbiter_reviews.status` 扩展

原有的 `ArbiterReviewStatus` 枚举需扩展以支持异步审查的中间态：

```python
class ArbiterReviewStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    FORCE_SKIPPED = "force_skipped"
    REVIEWING = "reviewing"        # ← 新增：已入队，等待异步处理
    REVIEW_FAILED = "review_failed" # ← 新增：异步处理失败（终态）
```

## 7. 事件钩子

### 7.1 Webhook 通知

`QueueService` 本身不直接发送 webhook——它只负责队列操作。Webhook 发送由 worker 在事务提交后触发，通过 `AbstractQueueService` 的 **callback 机制**：

```python
class AbstractQueueService(ABC):
    @abstractmethod
    def register_callback(
        self,
        status: TaskStatus,
        callback: Callable[[QueueTask], None],
    ) -> None:
        """注册任务完成/失败后的回调。

        典型用法：
        queue.register_callback(
            TaskStatus.DONE,
            lambda task: webhook_service.notify(task.review_id)
        )
        """

    @abstractmethod
    def execute_callbacks(self, task: QueueTask, status: TaskStatus) -> None:
        """事务提交后调用回调（不抛异常，只记录日志）。"""
```

### 7.2 回调实现约束

- 回调内部不得持有数据库事务
- 回调失败不影响队列状态（队列 = 唯一真实状态，回调 = 尽力而为通知）
- 回调抛出的异常被捕获并记录，不向上传播
