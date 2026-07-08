# Arbiter 异步审核 API 设计

> 最后更新：2026-07-08
> 基础路径：`/api/v1`

## 1. 设计原则

- **异步解耦**——API 层只负责接收请求并入队，不直接调用 LLM
- **最小侵入**——在现有 brief 操作流程上增加审核环节，不改变已有的状态机
- **callback 通知**——后台处理完毕后通过 webhook 通知前端，前端也可主动轮询
- **与已有 `03-api-design.md` 的关系**：本文档新增端点，已有的 editing/transfer/upstream-actions/downstream-actions 端点不变

## 2. 触发时机

审核在 brief 的 **send 流程**中触发——upstream 执行 `submit-review` 时入队：

```
editing ──(patch)──→ editing  （修改内容，不触发审核）
editing ──(submit-review)──→ 触发异步审核，入队
          ↓（审核完成后）
          reviewed ──(send)──→ sent
```

审核是 send 的前置条件：只有审核通过（或 force-skip）的 brief 才能 send。

## 3. API 端点

### 3.1 触发审核（异步）

`POST /api/v1/briefs/:brief_id/reviews`

```json
// Request（请求体可选，不传则使用默认 skill 集）
{
  "skill_ids": ["completeness-review@v2", "ambiguity-review@v1"],
  "webhook_url": "https://my-app.com/webhooks/reviews"  // 可选，覆盖默认 webhook
}

// Response 202
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "brief_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "reviewing",
  "skill_ids": ["completeness-review@v2", "ambiguity-review@v1"],
  "created_at": "2026-07-08T10:30:00Z"
}
```

**权限**：必须是 brief 的 `created_by`（upstream）

**内部流程**：

```
1. 验证 brief 存在 + 权限
2. 验证 skill_ids 合法（SkillRegistry 中存在对应版本）
3. 在 brief_arbiter_reviews 中创建一条 status=reviewing 的记录
4. 在 arbiter_review_tasks 中入队（status=pending）
5. 返回 202 + review_id

API 在此结束，不等待 LLM 执行
```

### 3.2 查询审核状态（轮询）

`GET /api/v1/briefs/:brief_id/reviews/:review_id`

```json
// Response 200 — 还在处理中
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "brief_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "reviewing",
  "created_at": "2026-07-08T10:30:00Z"
}

// Response 200 — 审核完成
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "brief_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "passed",
  "arbiter_id": "async-arbiter-v1",
  "score": 78,
  "issues": ["缺少非功能需求描述", "验收标准不量化"],
  "suggestions": [
    "建议补充性能指标（如响应时间 < 200ms）",
    "建议用 Given/When/Then 格式重写验收标准"
  ],
  "reviewed_at": "2026-07-08T10:30:35Z",
  "skill_results": {
    "completeness-review@v2": {
      "status": "done",
      "completeness_score": 70,
      "missing_dimensions": ["非功能需求"],
      "suggestions": ["补充性能指标"]
    },
    "ambiguity-review@v1": {
      "status": "done",
      "ambiguity_score": 85,
      "issues": ["验收标准不量化"],
      "suggestions": ["用 GWT 格式重写"]
    }
  }
}

// Response 200 — 审核失败
{
  "review_id": "...",
  "status": "review_failed",
  "error": "LLM call failed after 3 retries: rate_limit_exceeded",
  "created_at": "2026-07-08T10:30:00Z"
}
```

### 3.3 列出某 brief 的审核历史

`GET /api/v1/briefs/:brief_id/reviews`

```json
// Response 200
{
  "reviews": [
    {
      "review_id": "550e8400...",
      "brief_version": 3,
      "status": "passed",
      "score": 78,
      "reviewed_at": "2026-07-08T10:30:35Z"
    },
    {
      "review_id": "440e8400...",
      "brief_version": 2,
      "status": "failed",
      "score": 45,
      "reviewed_at": "2026-07-08T09:15:00Z"
    }
  ]
}
```

### 3.4 跳过审核（force-skip）

`POST /api/v1/briefs/:brief_id/reviews/skip`

```json
// Request
{
  "reason": "紧急上线，已口头对齐"  // 可选
}

// Response 201
{
  "review_id": "...",
  "status": "force_skipped",
  "created_at": "2026-07-08T10:31:00Z"
}
```

**权限**：必须是 brief 的 `created_by`

### 3.5 查询可用 Skills

`GET /api/v1/reviews/skills`

```json
// Response 200
{
  "skills": [
    {
      "skill_id": "completeness-review",
      "name": "需求完备性审查",
      "description": "审查 brief 是否覆盖了背景、目标、范围、验收标准、非功能需求",
      "versions": ["v1", "v2"],
      "latest": "v2"
    },
    {
      "skill_id": "ambiguity-review",
      "name": "需求歧义审查",
      "description": "检测 brief 中的模糊表述和歧义语言",
      "versions": ["v1"],
      "latest": "v1"
    }
  ]
}
```

## 4. Webhook 回调

### 4.1 配置

在 `QueueService` 层注册回调，不污染 API 路由层：

```python
# src/briefchain/api/main.py 中的 lifespan
from src.briefchain.arbiter.webhook import WebhookService

@app.on_event("startup")
async def startup():
    webhook = WebhookService()
    queue.register_callback(TaskStatus.DONE, webhook.notify_review_done)
    queue.register_callback(TaskStatus.FAILED, webhook.notify_review_failed)
```

### 4.2 Webhook 请求格式

```json
// POST {webhook_url}
// Content-Type: application/json
// X-BriefChain-Signature: sha256=...（可选，用于验签）

{
  "event": "review.completed",
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "brief_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "passed",
  "score": 78,
  "timestamp": "2026-07-08T10:30:35Z"
}
```

```json
// review.failed 事件
{
  "event": "review.failed",
  "review_id": "...",
  "brief_id": "...",
  "status": "review_failed",
  "error": "LLM call failed after 3 retries",
  "timestamp": "2026-07-08T10:32:00Z"
}
```

### 4.3 Webhook 发送策略

| 维度 | 策略 |
|------|------|
| URL 来源 | 请求中传入的 `webhook_url`（优先）或系统默认配置的 webhook endpoint |
| 重试 | MVP 阶段不重试（前端轮询兜底）。后续可加 outbox 模式 |
| 失败处理 | 静默丢弃 + 记录日志，不阻塞队列处理 |
| 事务安全 | 永远在 `mark_done` commit **之后**才发送 |

### 4.4 前端接收模式

```
┌──────────┐                  ┌──────────┐                  ┌──────────┐
│  前端     │                  │   API    │                  │  Worker  │
└────┬─────┘                  └────┬─────┘                  └────┬─────┘
     │                             │                             │
     │ POST /briefs/:id/reviews    │                             │
     │ ──────────────────────────▶ │                             │
     │ ◀── 202 + review_id         │                             │
     │                             │                             │
     │  [前端开始轮询]              │   [worker 消费队列, 调LLM]   │
     │                             │                             │
     │ GET /briefs/:id/reviews/:id │                             │
     │ ──────────────────────────▶ │                             │
     │ ◀── status: "reviewing"     │                             │
     │                             │                             │
     │                             │  [LLM完成]                   │
     │                             │ ◀── mark_done + commit       │
     │                             │                             │
     │  [或: webhook 主动推送]      │                             │
     │ ◀── POST /webhook           │ ◀────────────────────────── │
     │     event: review.completed  │                             │
     │                             │                             │
     │ GET /briefs/:id/reviews/:id │                             │
     │ ──────────────────────────▶ │                             │
     │ ◀── status: "passed"        │                             │
```

## 5. 错误响应

```json
// 400 — skill 不存在
{
  "error": {
    "code": "INVALID_SKILL",
    "message": "Skill not found: completeness-review@v99. Available versions: v1, v2",
    "details": {}
  }
}

// 400 — brief 状态不允许审核（已经是 final 状态等）
{
  "error": {
    "code": "INVALID_BRIEF_STATE",
    "message": "Brief is already in final state: cancelled",
    "details": { "current_state": "cancelled" }
  }
}

// 409 — 已有审核在处理中
{
  "error": {
    "code": "REVIEW_ALREADY_IN_PROGRESS",
    "message": "A review for this brief version is already in progress",
    "details": { "existing_review_id": "..." }
  }
}
```

## 6. 与现有 `send` 流程的集成

现有的 `submit-review` 端点（`POST /briefs/:id/editing?action=submit-review`）需要改造为异步：

```python
# src/briefchain/api/routes/briefs.py — 原有端点
@brief_router.post("/briefs/{brief_id}/editing")
async def brief_editing(
    brief_id: UUID,
    action: Annotated[str, Query(pattern="^(patch|submit-review)$")],
    ...
):
    if action == "submit-review":
        # 改造前（同步，force_skip）：
        # return brief_service.review_brief(session, brief_id, user_id, request)

        # 改造后（异步）：
        review = brief_service.create_async_review(
            session, brief_id, user_id, request.skill_ids
        )
        queue_service.enqueue(
            review_id=review.id,
            brief_id=brief_id,
            skill_ids=request.skill_ids,
        )
        return JSONResponse(
            status_code=202,
            content={
                "review_id": str(review.id),
                "status": "reviewing",
                "brief_id": str(brief_id),
            },
        )
```

## 7. 完整的 brief 创建到 send 流程（含审核）

```
upstream 创建 brief
    │
    ├── POST /briefs          → 创建 brief（editing, 无下游）
    ├── POST .../editing?action=patch        → 修改内容（可多次）
    ├── POST .../editing?action=submit-review → 触发异步审核
    │   └── 后端：创建 BriefArbiterReview(status=reviewing)
    │        + 入队 arbiter_review_tasks
    │        + 返回 202
    │
    ├── [Worker 异步执行 LLM 审核]
    │   ├── 执行各 skill
    │   ├── 聚合结果写入 brief_arbiter_reviews
    │   ├── 标记 brief_arbiter_reviews.status = passed/failed
    │   └── Webhook 通知前端
    │
    ├── [前端拿到审核结果]
    │   ├── 如果 passed：显示"可以发送"
    │   └── 如果 failed：显示问题列表，允许修改后重新 submit-review
    │
    └── POST .../transfer?action=send
        └── 此时 brief_arbiter_reviews 已有审核记录
            brief_version.status → reviewed
            发送给 downstream
```

## 8. 配置清单

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 默认 skill 集 | `ARBITER_DEFAULT_SKILLS` | `"completeness-review@v2"` | API 请求不传 skill_ids 时的默认值 |
| 默认 webhook URL | `ARBITER_WEBHOOK_URL` | — | 系统级默认回调地址（请求可覆盖） |
| 轮询间隔 | `ARBITER_WORKER_POLL_INTERVAL` | `2.0` | worker 空轮询间隔（秒） |
| 可见性超时 | `ARBITER_WORKER_VISIBILITY_TIMEOUT` | `300` | processing 任务回收时间（秒） |
| 审核超时 | `ARBITER_REVIEW_TIMEOUT` | `60` | 单个 skill 的 LLM 调用超时（秒） |
