# Arbiter 后台 Worker 设计

> 最后更新：2026-07-12

## 1. 设计目标

后台独立子进程，由 FastAPI 主进程拉起，从通用任务队列消费任务并执行。核心职责全部在 worker 层：

- **子进程模式**——FastAPI 启动时通过 `subprocess.Popen` 拉起，共享代码库和配置，零运维成本
- **按 type 分发**——worker 从 `task_queue` 取任务（dequeue 即删除），按 `type` 分发到对应处理器
- **Skill 驱动**——审核能力以 Skill 为单元组织，采用 Claude Code / OpenClaw 通用模式（prompt 模板 + 模型配置 + 输出结构）。MVP 仅一个 skill：`brief-review`
- **后端决定 skill**——worker 根据任务 type 选择对应 skill，前后端无需指定
- **重试管理**——`max_retries` 是 worker 配置，重试次数和状态在 `brief_arbiter_reviews.attempt_count` 中追踪
- **健康回收**——worker 启动时和周期性扫描卡在 `processing` 的 review，重新入队
- **最小依赖**——不依赖 Celery 等外部调度框架

## 2. Skill 设计

### 2.1 Skill 定义

Skill 是 LLM 驱动的审核能力单元。MVP 只有一个 skill，由 worker 内部决定调用。

| 属性 | 说明 |
|------|------|
| `skill_name` | 唯一标识，如 `brief-review` |
| `version` | 语义化版本，如 `v1`、`v2` |
| `system_prompt` | LLM 系统提示词 |
| `model` | 使用的模型（如 `gpt-4o`、`claude-3.5-sonnet`） |
| `temperature` | 温度参数 |
| `output_schema` | 结构化输出格式（Pydantic BaseModel） |

### 2.2 版本管理

采用 Claude Code / OpenClaw 通用模式：Skill 以文件形式组织，版本通过目录结构管理，不需要数据库表。

```
src/briefchain/skills/
├── brief-review/
│   ├── skill.md
```

每个 Skill 版本文件包含：system prompt、model 配置、temperature、输出结构定义。

### 2.3 Skill 选择

- Worker 内部根据 `type` 硬编码选择 skill。MVP 中 `type=review` → `brief-review@latest`
- Skill 信息不存储在队列或 review 记录中——worker 启动时加载，运行中使用
- 前端和 API 无需关心用哪个 skill——这是 worker 的内部实现细节

## 3. Worker 主循环

### 3.1 概览

```
                               ┌──────────────────────────────────┐
                               │           ArbiterWorker           │
                               │                                   │
                               │  ┌─ ① 健康回收                     │
                               │  │   扫描卡住的 review             │
                               │  │   → 重新 enqueue               │
                               │  │                                 │
  TaskQueue ──────────────────▶│  ├─ ② dequeue                     │
                               │  │   取最早任务（DELETE 后返回）    │
                               │  │                                 │
                               │  ├─ ③ 幂等检查                     │
                               │  │   review 已终态 → skip          │
                               │  │                                 │
                               │  ├─ ④ 重试上限检查                 │
                               │  │   attempt_count ≥ max_retries   │
                               │  │   → mark failed + webhook       │
                               │  │                                 │
                               │  ├─ ⑤ 按 type 分发 handler         │
                               │  │   type=review → ReviewHandler   │
                               │  │   (skill 由 handler 内部决定)    │
                               │  │                                 │
                               │  └─ ⑥ 执行成功 / 失败处理          │
                               │      成功 → update review + webhook │
                               │      失败 → re-enqueue 或 mark fail │
                               └──────────────────────────────────┘
```

### 3.2 主循环（伪代码）

```
health_check_interval = 60          // 每 60 秒做一次健康检查

worker.run():
    running = true
    注册信号处理（SIGTERM / SIGINT → running = false）

    last_health_check = 0

    while running:

        // ① 周期性健康回收：扫描卡住的 review
        if elapsed_since(last_health_check) >= health_check_interval:
            health_recovery()
            last_health_check = now()

        // ② 取任务（阻塞或短超时轮询）
        task = queue.dequeue()
        if task is null:
            sleep(poll_interval)
            continue

        // ③ 加载业务对象
        review = load brief_arbiter_reviews by task.ref_id

        // ④ 幂等：已完成则跳过
        if review.status in (passed, rejected, failed):
            continue

        // ⑤ 重试上限
        if review.attempt_count >= max_retries:
            review.status = failed
            review.error = "max retries exceeded"
            review.save()
            notify_webhook(review.webhook_url, review.id, status=failed)
            continue

        // ⑥ 递增尝试次数
        review.attempt_count += 1
        review.last_attempt_at = now()
        review.save()

        // ⑦ 分发执行
        handler = resolve_handler(task.type)

        try:
            handler.execute(review)
            // handler 内部已完成业务表更新（passed / rejected）
            notify_webhook(review.webhook_url, review.id, status=review.status)

        except TransientError as e:
            // 瞬时失败（LLM 超时、限流等）→ 重新入队
            review.error = str(e)
            review.save()
            queue.enqueue(type=task.type, ref_id=task.ref_id)

        except Exception as e:
            // 非瞬时失败 → 记录并重试
            review.error = str(e)
            review.save()
            queue.enqueue(type=task.type, ref_id=task.ref_id)

    log("Worker shut down gracefully.")
```

### 3.3 健康回收

扫描长时间卡在 `processing` 的 review 记录，重新入队：

```
health_recovery():
    stuck_reviews = find all brief_arbiter_reviews
      WHERE status = processing
        AND last_attempt_at < now() - processing_timeout

    for review in stuck_reviews:
        queue.enqueue(type=review, ref_id=review.id)
```

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 健康检查间隔 | `WORKER_HEALTH_CHECK_INTERVAL` | `60` | 扫描周期（秒） |
| 处理超时 | `WORKER_PROCESSING_TIMEOUT` | `300` | review 卡在 processing 多久视为异常（秒） |

> 健康回收的代价是**非精确**——worker 崩溃后最多等 `WORKER_HEALTH_CHECK_INTERVAL` 秒才会重新入队。MVP 单 worker 阶段这个延迟完全可接受。

### 3.4 ReviewHandler（伪代码）

```
ReviewHandler.execute(review):
    // 1. 加载关联数据
    brief = load brief by review.brief_id

    // 2. 加载 skill（worker 内部决定）
    skill = load_skill("brief-review", "latest")

    // 3. 调用 LLM
    result = invoke_llm(
        system_prompt = skill.system_prompt,
        user_content = brief.content,
        model = skill.model,
        output_schema = skill.output_schema
    )

    // 4. LLM 调用本身失败（超时、限流等）
    if result.error:
        raise TransientError(result.error)

    // 5. 更新 review 记录（独立事务）
    if result.passed:
        review.status = passed
    else:
        review.status = rejected
    review.score = result.score
    review.issues = result.issues
    review.suggestions = result.suggestions
    review.reviewed_at = now()
    review.save()
```

> `ReviewHandler` 内部不处理重试——如果 LLM 调用失败，底层抛出 `TransientError`，由主循环统一处理 re-enqueue。如果更新业务表失败（DB 异常），同样向上抛，由主循环重试。

### 3.5 处理器注册

```
resolve_handler(type) → Handler:
    "review"  → ReviewHandler
    "summary" → SummaryHandler（未来）
    unknown   → raise UnsupportedTaskType
```

新增任务类型只需实现 Handler 接口并注册，不影响队列和 worker 主循环。

## 4. 重试策略

| 配置项 | 归属 | 说明 |
|--------|------|------|
| `max_retries` | worker 配置（`WORKER_MAX_RETRIES`） | 最大重试次数，默认 3 |
| `attempt_count` | `brief_arbiter_reviews` 字段 | 已执行次数，每次尝试 +1 |
| `error` | `brief_arbiter_reviews` 字段 | 最近一次失败原因 |

重试决策流程：

```
任务执行失败
    │
    ├── 是否 transient（LLM 超时、限流）？
    │   └── 是 → review.attempt_count + 1
    │            → queue.enqueue（重新入队）
    │            → 下轮 dequeue 后 attempt_count ≥ max_retries → mark failed
    │
    └── 是否非 transient（DB 异常等）？
        └── 同样 re-enqueue——靠 attempt_count 上限兜底
```

> **关键区分**：`rejected`（审核未通过）不是错误，是正常结论。Handler 直接设置 `review.status = rejected`，不会抛异常。只有 LLM 调用异常或 DB 异常才会触发重试。

## 5. 错误处理矩阵

| 错误场景 | 处理方式 |
|---------|---------|
| dequeue 返回 null | sleep poll_interval 后继续 |
| handler 不存在（未知 type） | 记录日志，跳过（不自动恢复的任务不应卡住队列） |
| review 已处于终态（幂等） | 跳过，不处理 |
| attempt_count ≥ max_retries | review.status = failed，webhook 通知 |
| LLM 调用失败（超时 / 限流） | re-enqueue（attempt_count + 1 在 re-enqueue 前完成） |
| LLM 返回 rejected | 正常处理：review.status = rejected，通过（不是错误） |
| 更新业务表失败（DB 异常） | re-enqueue 重试 |
| webhook 发送失败 | 记录日志并静默丢弃（前端可轮询兜底） |
| worker 进程崩溃 | 主进程检测到子进程退出后自动重启；启动时健康回收扫描 stuck reviews |

## 6. 启动与运维

### 6.1 子进程模式

FastAPI 主进程启动时通过 `subprocess.Popen` 拉起 worker 子进程，共享同一个虚拟环境和配置：

```
# FastAPI 主进程启动时
main():
    // ... 初始化队列、数据库等共享资源 ...

    worker_process = subprocess.Popen([
        sys.executable,
        "-m", "src.briefchain.arbiter.worker"
    ])

    // 启动 FastAPI
    uvicorn.run(app, ...)

    // 退出时等待子进程
    worker_process.terminate()
    worker_process.wait()
```

### 6.2 Worker 启动流程

```
1. 加载所有 skill 版本
2. 健康回收：扫描 stuck reviews 并重新入队
3. 进入主循环
```

### 6.3 进程管理

| 场景 | 处理方式 |
|------|---------|
| 正常启动 | 主进程拉起 → worker 执行启动流程 → 进入主循环 |
| 主进程 SIGTERM | 转发 SIGTERM 给 worker → 完成当前任务后退出 |
| worker 崩溃 | 主进程检测子进程退出 → 自动重启（带退避） |
| 崩溃时正在处理的任务 | 重启后的健康回收扫描 → 重新入队 |

### 6.4 配置项汇总

| 配置 | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| 轮询间隔 | `WORKER_POLL_INTERVAL` | `2.0` | 无任务时空闲间隔（秒） |
| 最大重试 | `WORKER_MAX_RETRIES` | `3` | 任务失败最大重试次数 |
| 健康检查间隔 | `WORKER_HEALTH_CHECK_INTERVAL` | `60` | 扫描 stuck reviews 周期（秒） |
| 处理超时 | `WORKER_PROCESSING_TIMEOUT` | `300` | review 卡在 processing 多久视为异常（秒） |
| 默认 skill | `BRIEF_REVIEW_SKILL` | `brief-review` | worker 内部使用的 skill 名称 |
| 系统 webhook URL | `ARBITER_WEBHOOK_URL` | — | 默认回调地址（review 未指定时使用） |
