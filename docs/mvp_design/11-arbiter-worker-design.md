# Arbiter 后台 Worker 设计

> 最后更新：2026-07-08

## 1. 设计目标

单线程后台进程，从任务队列消费任务并执行 LLM 审核。核心要求：

- **Skill 驱动**——审核能力以「Skill」为单元组织，每个 Skill 有独立版本
- **最小依赖**——不依赖 Celery 等外部调度框架
- **优雅退出**——收到 SIGTERM 后完成当前任务再退出
- **容错**——单个 Skill 失败不影响同任务的其他 Skill，worker 本身崩溃可由系统进程管理器恢复

## 2. Skill 设计

### 2.1 Skill 定义

Skill 是 LLM 驱动的审核能力单元，包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `skill_id` | `str` | 唯一标识，如 `"completeness-review"` |
| `version` | `str` | 语义化版本，如 `"v1"`, `"v1.1"` |
| `name` | `str` | 人类可读名称，如 `"需求完备性审查"` |
| `description` | `str` | 说明该 skill 审查什么维度的质量 |
| `system_prompt` | `str` | LLM 系统提示词 |
| `model` | `str` | 使用的模型，如 `"gpt-4o"`, `"claude-3.5-sonnet"` |
| `temperature` | `float` | 温度参数 |
| `output_schema` | `type[BaseModel]` | Pydantic 模型，定义结构化输出格式 |
| `dependencies` | `list[str]` | 依赖的其他 skill_id（可选，用于串联执行） |

### 2.2 Skill 版本管理

版本管理不依赖数据库表，直接通过文件系统组织：

```
src/briefchain/arbiter/skills/
├── __init__.py
├── registry.py                   # SkillRegistry：加载/发现 skills
├── completeness/
│   ├── __init__.py
│   ├── v1.py                     # completeness_review_v1
│   └── v2.py                     # completeness_review_v2
├── ambiguity/
│   └── v1.py                     # ambiguity_review_v1
└── acceptance_criteria/
    └── v1.py                     # acceptance_criteria_review_v1
```

每个 skill 版本是一个 Python 模块，导出 `SkillDescriptor`：

```python
# src/briefchain/arbiter/skills/completeness/v2.py
from pydantic import BaseModel, Field

from src.briefchain.arbiter.skill_protocol import SkillDescriptor


class CompletenessOutput(BaseModel):
    thinking: str = Field(description="逐步推理过程")
    is_complete: bool = Field(description="需求是否完备")
    completeness_score: int = Field(ge=0, le=100)
    missing_dimensions: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


skill = SkillDescriptor(
    skill_id="completeness-review",
    version="v2",
    name="需求完备性审查",
    description="审查 brief 是否覆盖了背景、目标、范围、验收标准、非功能需求",
    system_prompt="""你是一个需求完备性审查专家。请审查以下需求文档，判断是否覆盖了关键维度：
1. 背景与动机
2. 目标与范围
3. 验收标准
4. 非功能需求（性能、安全、兼容性）
5. 风险与假设
对每个缺失的维度给出具体建议。""",
    model="gpt-4o",
    temperature=0.3,
    output_schema=CompletenessOutput,
    dependencies=[],  # 该 skill 不依赖其他 skill 的结果
)
```

### 2.3 SkillRegistry

```python
# src/briefchain/arbiter/skills/registry.py
from dataclasses import dataclass
from typing import Iterable
from src.briefchain.arbiter.skill_protocol import SkillDescriptor


@dataclass(frozen=True)
class SkillSelector:
    """skill_id + version 的唯一选择器。"""
    skill_id: str
    version: str

    @classmethod
    def from_string(cls, s: str) -> "SkillSelector":
        """从 "completeness-review@v2" 格式解析。"""
        skill_id, _, version = s.partition("@")
        if not version:
            raise ValueError(f"Skill selector must include version: {s}")
        return cls(skill_id=skill_id, version=version)


class SkillRegistry:
    """管理所有已注册的 Skill 版本。

    在模块加载时通过 `load_all()` 自动发现 `skills/` 目录下的所有 skill。
    """

    def __init__(self):
        self._skills: dict[SkillSelector, SkillDescriptor] = {}

    def register(self, descriptor: SkillDescriptor) -> None:
        key = SkillSelector(skill_id=descriptor.skill_id, version=descriptor.version)
        self._skills[key] = descriptor

    def resolve(self, selector: SkillSelector) -> SkillDescriptor:
        """按 skill_id@version 解析。不存在则抛 KeyError。"""
        return self._skills[selector]

    def list_all(self) -> Iterable[SkillDescriptor]:
        return self._skills.values()

    def latest_version(self, skill_id: str) -> str:
        """返回指定 skill 的最新版本。"""
        candidates = [
            (s.version, s)
            for s in self._skills.values()
            if s.skill_id == skill_id
        ]
        if not candidates:
            raise KeyError(f"Skill not found: {skill_id}")
        # 语义化排序取最新
        candidates.sort(key=lambda x: _parse_version(x[0]), reverse=True)
        return candidates[0][0]
```

## 3. Worker 设计

### 3.1 架构概览

```
                    ┌────────────────────────┐
                    │     ArbiterWorker       │
                    │                         │
  QueueService ────▶│  1. dequeue             │
                    │  2. resolve skill(s)    │
                    │  3. call LLM (per skill)│
                    │  4. aggregate results   │
                    │  5. update review       │──▶ brief_arbiter_reviews
                    │  6. mark task done      │
                    │                         │
                    │  [after commit]         │
                    │  7. fire webhook        │──▶ frontend
                    └────────────────────────┘
```

### 3.2 Worker 循环

```python
# src/briefchain/arbiter/worker.py
import signal
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from src.briefchain.arbiter.skill_protocol import SkillDescriptor, SkillResult
from src.briefchain.arbiter.skills.registry import SkillRegistry, SkillSelector
from src.briefchain.queue.base import AbstractQueueService, QueueTask


@dataclass
class WorkerConfig:
    poll_interval_seconds: float = 2.0
    visibility_timeout_seconds: int = 300
    lock_refresh_interval_seconds: int = 60     # 长任务定期刷新锁
    webhook_callback: Callable[[UUID, str], None] | None = None


class ArbiterWorker:
    """单线程后台 worker，消费队列并执行 LLM 审核。

    Usage:
        worker = ArbiterWorker(queue_service, skill_registry, config)
        worker.run()
    """

    def __init__(
        self,
        queue_service: AbstractQueueService,
        skill_registry: SkillRegistry,
        config: WorkerConfig | None = None,
    ):
        self._queue = queue_service
        self._registry = skill_registry
        self._config = config or WorkerConfig()
        self._running = False

        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        while self._running:
            task = self._queue.dequeue(
                visibility_timeout_seconds=self._config.visibility_timeout_seconds
            )
            if task is None:
                time.sleep(self._config.poll_interval_seconds)
                continue

            try:
                self._process_one(task)
            except Exception:
                # _process_one 内部已有错误处理，此处兜底
                pass
        print("Worker shut down gracefully.")

    def _process_one(self, task: QueueTask) -> None:
        """处理单个队列任务。"""
        try:
            # 1. 解析并执行 skills
            results = self._execute_skills(task)

            # 2. 聚合结果写入 brief_arbiter_reviews
            self._update_review(task.review_id, results)

            # 3. 标记任务完成（事务内）
            self._queue.mark_done(task.id)

            # 4. 事务提交后：webhook 通知
            self._queue.execute_callbacks(task, TaskStatus.DONE)

        except Exception as e:
            # 记录失败原因，自动重试逻辑由 queue.mark_failed 处理
            self._queue.mark_failed(task.id, error=str(e))
            self._queue.execute_callbacks(task, TaskStatus.FAILED)

    def _execute_skills(self, task: QueueTask) -> dict[str, "SkillResult"]:
        """执行任务要求的全部 skills。每个 skill 独立运行，失败不影响其他。"""
        results: dict[str, SkillResult] = {}

        for selector_str in task.skill_ids:
            selector = SkillSelector.from_string(selector_str)
            descriptor = self._registry.resolve(selector)

            try:
                result = self._run_skill(descriptor, task.brief_id)
                results[selector_str] = result
            except Exception as e:
                results[selector_str] = SkillResult(
                    skill_id=selector_str,
                    status="error",
                    error=str(e),
                )

        return results
```

### 3.3 Skill 执行

```python
    def _run_skill(self, descriptor: SkillDescriptor, brief_id: UUID) -> SkillResult:
        """执行单个 skill：加载 brief → 构造 prompt → 调 LLM → 解析输出。"""
        # 加载 brief 内容
        brief_content = _load_brief_for_review(brief_id)

        # 使用 langchain/langgraph 调用 LLM
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=descriptor.model,
            temperature=descriptor.temperature,
        ).bind_tools(
            response_format=descriptor.output_schema,
        )

        # structured_output 是 Pydantic model 实例
        structured_output = llm.invoke(
            [
                {"role": "system", "content": descriptor.system_prompt},
                {"role": "user", "content": brief_content},
            ]
        )

        return SkillResult(
            skill_id=f"{descriptor.skill_id}@{descriptor.version}",
            status="done",
            data=_pydantic_to_dict(structured_output),
        )
```

### 3.4 结果聚合与回写

```python
    def _update_review(
        self,
        review_id: UUID,
        results: dict[str, SkillResult],
    ) -> None:
        """将 skill 执行结果聚合写入 brief_arbiter_reviews。

        事务内执行：UPDATE brief_arbiter_reviews SET ...
        """
        # 综合评分：各 skill 分数的平均值
        scores = [
            r.data.get("completeness_score", 0)
            for r in results.values()
            if r.status == "done" and r.data
        ]
        overall_score = sum(scores) // len(scores) if scores else None

        # 汇总 issues 和 suggestions
        all_issues = []
        all_suggestions = []
        for r in results.values():
            if r.status != "done" or not r.data:
                continue
            if missing := r.data.get("missing_dimensions"):
                all_issues.extend(missing)
            if suggestions := r.data.get("suggestions"):
                all_suggestions.extend(suggestions)

        # 判断通过/失败：所有 skill 均 done 且整体评分 >= 阈值
        all_done = all(r.status == "done" for r in results.values())
        passed = all_done and (overall_score is not None and overall_score >= 60)

        with self._session_factory() as session:
            review = session.get(BriefArbiterReview, review_id)
            if review is None:
                raise ValueError(f"Review not found: {review_id}")

            review.status = ArbiterReviewStatus.PASSED if passed else ArbiterReviewStatus.FAILED
            review.score = overall_score
            review.issues = all_issues
            review.suggestions = all_suggestions
            review.reviewed_at = datetime.utcnow()
            review.arbiter_id = "async-arbiter-v1"  # 区别于 force_skip

            session.commit()
```

## 4. 启动与运维

### 4.1 入口命令

```bash
# 作为独立进程启动（uv 运行）
uv run python -m src.briefchain.arbiter.worker

# 或通过 systemd / supervisord 守护
```

### 4.2 进程管理

| 场景 | 处理方式 |
|------|---------|
| 正常启动 | `ArbiterWorker.run()` 进入循环 |
| SIGTERM / SIGINT | 设置 `_running=False`，当前任务处理完后退出 |
| 进程崩溃 | systemd/supervisord 自动重启 |
| 崩溃时卡在 processing 的任务 | 健康回收：locked_at > 5min → 被下次 dequeue 重新认领 |

### 4.3 配置项

```python
# 环境变量控制
ARBITER_WORKER_POLL_INTERVAL=2.0    # 无任务时空闲轮询间隔（秒）
ARBITER_WORKER_VISIBILITY_TIMEOUT=300   # processing 任务超时回收时间（秒）
ARBITER_WORKER_LOCK_REFRESH=60      # 长任务定期刷新锁间隔（秒）
```

## 5. 错误处理矩阵

| 错误阶段 | 处理策略 |
|---------|---------|
| dequeue 失败 | 记录日志，sleep 后重试 |
| skill 不存在（SkillSelector 解析失败） | 立即 mark_failed，不重试（配置错误不会自动恢复） |
| 单个 skill 执行失败 | 记录进 results，同任务其他 skill 正常执行 |
| 全部 skill 执行失败 | mark_failed，retry_count < max_retries 则重试 |
| update_review 失败 | mark_failed（LLM 结果无法持久化，等效于任务失败） |
| webhook 发送失败 | 记录日志并静默丢弃（回调 = 尽力而为，前端可轮询兜底） |

## 6. Skill 结果数据结构

### 6.1 `SkillResult`

```python
@dataclass
class SkillResult:
    skill_id: str           # "completeness-review@v2"
    status: str             # "done" | "error" | "skipped"
    data: dict | None = None   # Pydantic model 序列化结果
    error: str | None = None
```

### 6.2 存储策略

- Skill 执行结果不建独立表存储（避免过度设计），聚合后直接写入 `brief_arbiter_reviews.issues` 和 `brief_arbiter_reviews.suggestions`
- 如需追溯各 skill 的原始输出：在 `brief_arbiter_reviews` 新增 `skill_results` JSON 字段

```python
# 可选扩展：brief_arbiter_reviews 新增字段
skill_results: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
# 格式：{"completeness-review@v2": {...SkillResult.data...}, ...}
```

## 7. 紧耦合 vs 松耦合权衡

当前设计将 worker 和 QueueService 放在同一进程空间：

| 维度 | 同进程 worker | 独立进程 worker |
|------|-------------|----------------|
| 部署复杂度 | 一个启动命令 | 独立 deploy + 独立监控 |
| 资源共享 | 共享数据库连接池、Skill 模块 | 需要各自配置 |
| 故障隔离 | worker crash = 进程 crash | worker crash 不影响 API |
| 当前阶段适用 | **推荐**（简单，够用） | 等 worker 变复杂或有独立扩缩容需求时再拆 |

MVP 阶段推荐同进程启动（`ArbiterWorker` 在 FastAPI 的 `lifespan` 中启动），后续可拆为独立进程。
