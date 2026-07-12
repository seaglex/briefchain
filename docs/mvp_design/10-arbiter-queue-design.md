# 通用异步任务队列设计

> 最后更新：2026-07-12

## 1. 设计目标

- **通用**——不绑定特定业务。当前服务于 Arbiter 审核（type=review），未来可扩展任务进度总结（type=summary）等
- **与实现无关**——队列接口抽象，MVP 用数据库实现，将来可无缝替换为 Redis / MQ / Kafka
- **最少外部依赖**——MVP 阶段不引入中间件，直接使用现有数据库
- **极简语义**——队列只管投递和取出，不管理任务生命周期。dequeue 即删除——取走就没了
- **业务层兜底**——重试、超时回收、重复执行防护全部在业务层（`brief_arbiter_reviews` + worker）实现

## 2. 数据模型

### 2.1 通用队列表：`task_queue`

队列只存最小必要信息，不记录状态、不记录重试次数、不记录错误。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID PK | 任务 ID |
| `type` | VARCHAR(32) | 任务类型：`review` / `summary` / ... |
| `ref_id` | UUID | 引用业务实体 ID（如 `brief_arbiter_reviews.id`） |
| `created_at` | TIMESTAMPTZ | 入队时间（用于 FIFO 排序） |

索引：

| 索引 | 用途 |
|------|------|
| `idx_queue_fetch (created_at)` | 按 FIFO 顺序取最早任务 |

> 没有 `status`——任务只有一种存在形式：在队列里。被 dequeue 后行即删除，不需要 `processing` / `done` / `failed` 等状态。
> 没有 `retry_count`、`locked_at`、`error`、`finished_at`——这些都是业务层（`brief_arbiter_reviews`）关心的事。

### 2.2 队列的生命周期

```
enqueue → [在表中] → dequeue → [已删除，不再存在]
```

队列没有状态机。任务要么在表里等着被取，要么已经被取走删掉了。

### 2.3 `brief_arbiter_reviews` 扩展

队列的极简化意味着业务表需要接管所有生命周期管理。`brief_arbiter_reviews` 扩展如下：

**状态枚举：**

| 状态 | 含义 | 是否新增 |
|------|------|---------|
| `processing` | 已入队，异步处理中 | **新增** |
| `passed` | 审核通过（内容质量合格） | 原有 |
| `rejected` | 审核未通过（内容质量问题，需修改） | **新增** |
| `failed` | 执行失败（技术错误，已达重试上限） | **含义变更** |
| `force_skipped` | 强制跳过 | 原有（MVP 不启用） |

**新增字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `attempt_count` | INTEGER DEFAULT 0 | 执行尝试次数（worker 用于判断重试上限） |
| `last_attempt_at` | TIMESTAMPTZ | 最近一次尝试时间（worker 健康检查用） |
| `error` | TEXT | 最近一次错误原因 |
| `webhook_url` | VARCHAR(512) | 回调地址（可选，为空则使用系统默认） |

> `max_retries` 是 worker 配置项（环境变量），不在数据表中。

业务表状态流转：

```
创建 review → status = processing
    │
    ├── worker 执行成功，内容合格 → passed
    ├── worker 执行成功，内容不合格 → rejected
    ├── worker 执行失败，attempt_count < max_retries → 重新 enqueue，attempt_count + 1
    ├── worker 执行失败，attempt_count ≥ max_retries → failed（终态）
    └── 用户强制跳过 → force_skipped（MVP 暂不实现）
```

## 3. 队列接口

### 3.1 接口定义（伪代码）

```
interface TaskQueue:

    enqueue(type, ref_id) → task_id
        插入 task_queue 记录 (type, ref_id)
        提交事务
        返回 task_id
        // 不防重——重复执行防护在业务层
        // 不记录状态——队列不关心任务后续生命周期

    dequeue() → task | null
        取最早的记录，删除并返回
        提交事务
        返回 task（含 id, type, ref_id）
        无记录返回 null
        // dequeue 即删除——取走就没了，无需 ack
        // 如果 worker 崩溃，业务层健康检查负责重新 enqueue
```

### 3.2 实现无关性

接口中没有任何数据库特定概念。具体实现负责适配：

| 实现 | dequeue 方式 | 适用阶段 |
|------|-------------|---------|
| PostgreSQL | `DELETE ... ORDER BY created_at RETURNING *` | 生产环境 |
| SQLite | `DELETE ... ORDER BY created_at RETURNING *` | 开发 / MVP |
| Redis（未来） | `BRPOP` 阻塞弹出 | 高吞吐场景 |
| Kafka / MQ（未来） | consumer group offset | 事件驱动架构 |

切换实现时，只需替换 `TaskQueue` 的具体类，调用方代码不变。

### 3.3 实现选择

```
create_queue_service(config) → TaskQueue:
    根据 config.queue_backend 选择实现
    "database" → DatabaseTaskQueue（PostgreSQL 或 SQLite，自动检测）
    "redis"    → RedisTaskQueue（未来）
    默认 "database"
```

## 4. 数据库实现（MVP）

### 4.1 PostgreSQL

`dequeue` 核心：`DELETE ... ORDER BY created_at RETURNING *`，删除最早的一条记录并返回：

```
dequeue():
    BEGIN
    DELETE FROM task_queue
      WHERE id = (
        SELECT id FROM task_queue
        ORDER BY created_at
        LIMIT 1
      )
      RETURNING *                     -- 返回被删除的行
    COMMIT
    return task | null
```

### 4.2 SQLite

SQLite 同样支持 `DELETE ... ORDER BY ... LIMIT ... RETURNING`（3.35+）：

```
dequeue():
    BEGIN IMMEDIATE
    DELETE FROM task_queue
      WHERE id = (
        SELECT id FROM task_queue
        ORDER BY created_at
        LIMIT 1
      )
      RETURNING *
    COMMIT
    return task | null
```

> `BEGIN IMMEDIATE` 获取写锁，防止并发 delete 同一条记录。单 worker 场景下无竞争，多 worker 场景下由数据库串行化保证不重复。

### 4.3 Redis（未来参考）

```
enqueue:  LPUSH queue:pending {json_string}
dequeue:  BRPOP queue:pending {timeout}
```

两个原生命令，不需要 Lua 脚本，不需要 processing 列表。

## 5. 事务边界

**绝不在数据库事务内调用 LLM 或发送 HTTP 请求。**

```
dequeue 事务                      LLM 调用（无事务）
┌──────────────┐                 ┌──────────────┐
│ BEGIN         │                 │              │
│ DELETE ...    │  删除，取走任务  │ 执行 skill    │
│ RETURNING *   │                 │ 调 LLM       │
│ COMMIT        │                 │ (5-30s)      │
└──────────────┘                 │              │
                                 └──────┬───────┘
                                        │
                         ┌──────────────▼──────────┐
                         │ 更新业务表 + webhook      │
                         │                          │
                         │ 如果成功:                 │
                         │   review.status = passed  │
                         │   或 rejected             │
                         │   → 事务提交              │
                         │                          │
                         │ 如果失败:                 │
                         │   attempt_count + 1       │
                         │   未达上限 → re-enqueue    │
                         │   已达上限 → failed        │
                         │   → 事务提交              │
                         │                          │
                         │ 事务提交后: webhook 通知    │
                         └──────────────────────────┘
```

## 6. 职责分离

### 6.1 task_queue vs brief_arbiter_reviews

| 维度 | task_queue | brief_arbiter_reviews |
|------|-----------|----------------------|
| 职责 | **投递**——FIFO 缓冲，取走即删 | **业务全生命周期**——状态、重试、结论、回调 |
| 数据结构 | id, type, ref_id, created_at | status, attempt_count, score, issues, webhook_url, ... |
| 通用性 | 通用（type=review / summary / ...） | review 专属 |
| 生命周期 | 入队 → 出队（删除） | 创建 → 处理中 → 终态（永久保留） |
| 读写模式 | 写多读多（入队/出队频繁） | 写少读多（用户查看审核结果） |

### 6.2 重复执行防护

队列层不防重（`enqueue` 不检查是否已有相同任务）。防重在**业务层**：

```
API 收到审核请求:
    检查 brief_arbiter_reviews 是否已有 status = processing 的记录
    if 已存在:
        返回 409 REVIEW_ALREADY_IN_PROGRESS
    else:
        创建 brief_arbiter_reviews (status = processing, attempt_count = 0, webhook_url = ...)
        queue.enqueue(type=review, ref_id=review.id)
        返回 202
```

Worker 层面也做幂等检查——消费任务后发现 review 已处于终态则跳过。

### 6.3 健康回收

队列没有 `locked_at` 和 `processing` 状态，因此崩溃恢复不在队列层。由 worker 启动时扫描 `brief_arbiter_reviews` 中长时间停留在 `processing` 且 `last_attempt_at` 超时的记录，重新 `enqueue`。

> 详细逻辑见 [11-arbiter-worker-design.md](11-arbiter-worker-design.md) 第 3 节。

### 6.4 各层职责总结

| 层 | 关心什么 | 不关心什么 |
|----|---------|-----------|
| **task_queue** | type, ref_id, FIFO 顺序 | 状态、重试、业务结果、健康回收、webhook |
| **brief_arbiter_reviews** | 审核状态（processing/passed/rejected/failed）、attempt_count、webhook_url、结论详情、防重 | 队列实现细节 |
| **worker** | skill 执行、重试决策、健康回收、webhook 通知 | 队列实现细节 |
| **API** | 创建 review、防重检查、入队、返回 202 | LLM 执行过程 |

### 6.5 为什么不需要 ack / nack

`dequeue` 删除记录后，如果 worker 执行成功——不需要 ack，任务已经不存在了。如果 worker 执行失败——重新 `enqueue` 即可，不需要 nack，因为 nack 的本质是"放回队列"，而 `enqueue` 就是"放回队列"。

队列本身只管"有没有新任务要处理"。任务处理完了还是失败了，是业务层的事。
