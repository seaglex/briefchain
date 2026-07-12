## Why

当前 brief 的 `submit-review` 是同步 force-skip，无法真正评估需求质量，导致下游收到的内容参差不齐。为了让 upstream 在 send 前获得结构化的 LLM 审核反馈，并在高延迟模型调用下不阻塞 API，需要引入异步 Arbiter 审核机制。

## What Changes

- 新增通用异步任务队列 `task_queue`，MVP 使用数据库实现，未来可替换为 Redis / MQ。
- 扩展 `brief_arbiter_reviews` 业务表：新增 `processing` / `rejected` / `failed` 状态、`attempt_count`、`last_attempt_at`、`error`、`webhook_url` 字段，接管审核全生命周期。
- 新增 Arbiter Worker 子进程，由 FastAPI 主进程拉起，消费队列并按 `type` 分发；MVP 内置 `review` 处理器，使用 `src/briefchain/skills/brief-review` skill 调用 LLM。
- 新增异步审核 API：`POST /api/v1/briefs/:brief_id/reviews` 触发审核，`GET /api/v1/briefs/:brief_id/reviews/:review_id` 查询状态。
- 改造现有 `submit-review` action：从同步 force-skip 改为异步入队，返回 202。
- 支持通过环境变量配置第三方 LLM API：`LLM_API_KEY`（或按 provider 命名）、`LLM_BASE_URL`、`LLM_MODEL`。
- 新增 `SKIP_REVIEW` 环境变量开关：设为 `true` 时 worker 不调用 LLM skill，直接将 review 标记为 `force_skipped`。
- Worker 执行完成后通过 webhook 推送结果，失败静默丢弃，前端可轮询兜底。

## Capabilities

### New Capabilities

- `brief-arbiter-review`: 基于 LLM 的 brief 内容质量审核，使用 `brief-review` skill 从 Why / What / Goals / Hypothesis 四个维度评估，输出 passed / rejected 结论及问题与建议。
- `task-queue`: 通用 FIFO 任务队列，支持 enqueue / dequeue，MVP 基于数据库，接口与实现解耦。
- `arbiter-worker`: 后台异步任务执行器，负责任务分发、重试、健康回收、webhook 通知。
- `arbiter-review-api`: 审核相关的异步 REST API，包括触发审核与查询审核状态。

### Modified Capabilities

- `brief-send-flow`: `submit-review` 从同步 force-skip 改为异步触发审核；只有通过审核（`passed`）的 brief 才能执行 send。

## Impact

- **数据库**：新增 `task_queue` 表；扩展 `brief_arbiter_reviews` 表（新增字段与状态值）。
- **API**：新增 `POST/GET /briefs/:id/reviews`；修改 `POST /briefs/:id/editing?action=submit-review` 响应为 202。
- **后台进程**：FastAPI 主进程启动时拉起 worker 子进程，退出时负责终止。
- **依赖**：新增 Google ADK 用于 skill 加载；通过环境变量接入第三方 LLM API，不锁定具体模型供应商。
- **配置**：新增 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`QUEUE_BACKEND`、`WORKER_*`、`ARBITER_WEBHOOK_URL`、`SKIP_REVIEW` 等环境变量。
- **部署**：需要确保 worker 子进程随主进程启停，MVP 阶段无需额外队列中间件。
