# Arbiter 异步审核 API 设计

> 最后更新：2026-07-12
> 基础路径：`/api/v1`

## 1. 设计原则

- **异步解耦**——API 层只负责创建 review + 入队，不直接调用 LLM
- **防重在业务层**——API 创建 review 时检查是否已有 `processing` 状态的记录，队列层不防重
- **后端决定 skill**——前端无需指定审核策略，由 worker 内部根据任务类型选择
- **webhook 存在业务表**——`webhook_url` 随 review 创建写入 `brief_arbiter_reviews`，worker 执行后读取
- **与已有 `03-api-design.md` 的关系**：本文档新增端点，已有的 editing / transfer / upstream-actions / downstream-actions 端点不变

## 2. 触发时机

审核在 brief 的 **send 流程**中触发——upstream 执行 `submit-review` 时入队：

```
editing ──(patch)──→ editing          （修改内容，不触发审核）
editing ──(submit-review)──→ 触发异步审核，入队
          ↓（审核完成后）
          reviewed ──(send)──→ sent    （只有 passed 才能 send）
```

## 3. API 端点

### 3.1 触发审核（异步）

`POST /api/v1/briefs/:brief_id/reviews`

```json
// Request
{
  "webhook_url": "https://my-app.com/webhooks/reviews"  // 可选，写入 review 记录
}

// Response 202
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "brief_id": "660e8400-e29b-41d4-a716-446655440001",
  "brief_version": 3,
  "status": "processing",
  "created_at": "2026-07-12T10:30:00Z"
}
```

**权限**：必须是 brief 的 `created_by`（upstream）

**内部流程**：

```
1. 验证 brief 存在 + 权限
2. 防重检查：是否已有 status=processing 的 review？
   └── 是 → 返回 409 REVIEW_ALREADY_IN_PROGRESS
3. 创建 brief_arbiter_reviews 记录（status=processing, attempt_count=0, webhook_url=...）
4. queue.enqueue(type=review, ref_id=review.id)
5. 返回 202 + review_id + brief_version

API 在此结束，不等待 LLM 执行
```

### 3.2 查询审核状态（轮询）

`GET /api/v1/briefs/:brief_id/reviews/:review_id`

```json
// Response 200 — 处理中
{
  "review_id": "550e8400-...",
  "brief_id": "660e8400-...",
  "brief_version": 3,
  "status": "processing",
  "attempt_count": 1,
  "created_at": "2026-07-12T10:30:00Z"
}

// Response 200 — 审核通过
{
  "review_id": "550e8400-...",
  "brief_id": "660e8400-...",
  "brief_version": 3,
  "status": "passed",
  "arbiter_id": "async-arbiter-v1",
  "score": 78,
  "issues": [],
  "suggestions": [],
  "reviewed_at": "2026-07-12T10:30:35Z"
}

// Response 200 — 审核未通过（内容质量问题）
{
  "review_id": "550e8400-...",
  "brief_id": "660e8400-...",
  "brief_version": 3,
  "status": "rejected",
  "arbiter_id": "async-arbiter-v1",
  "score": 45,
  "issues": ["缺少非功能需求描述", "验收标准不量化"],
  "suggestions": [
    "建议补充性能指标（如响应时间 < 200ms）",
    "建议用 Given/When/Then 格式重写验收标准"
  ],
  "reviewed_at": "2026-07-12T10:30:35Z"
}

// Response 200 — 执行失败（已达重试上限）
{
  "review_id": "550e8400-...",
  "brief_id": "660e8400-...",
  "brief_version": 3,
  "status": "failed",
  "error": "LLM call failed after 3 attempts: rate_limit_exceeded",
  "attempt_count": 3,
  "created_at": "2026-07-12T10:30:00Z"
}
```

## 4. `brief_arbiter_reviews` 状态

| 状态 | 含义 | 是否终态 | 可否 send |
|------|------|---------|----------|
| `processing` | 异步处理中 | 否 | 否 |
| `passed` | 审核通过 | 是 | 是 |
| `rejected` | 审核未通过（内容质量问题） | 是 | 否（需修改后重新 submit-review） |
| `failed` | 执行失败（已达重试上限） | 是 | 否（可重新触发审核） |
| `force_skipped` | 强制跳过 | 是 | 是（MVP 暂不实现） |

> `rejected` 是审核结论（内容不合格），不是执行错误。`failed` 是技术执行失败（如 LLM 调用超时，且已达 `max_retries`）。两者语义不同：`rejected` 需用户修改 brief 内容，`failed` 可直接重新触发审核。

## 5. Webhook 回调

### 5.1 URL 来源

`webhook_url` 随审核请求写入 `brief_arbiter_reviews` 表。Worker 执行时从 review 记录读取，为空则使用系统默认配置。

### 5.2 触发时机

Worker 更新 `brief_arbiter_reviews` 事务提交**之后**触发，不在事务内。

### 5.3 请求格式

```json
// POST {webhook_url}
// Content-Type: application/json

// 审核完成（passed 或 rejected）
{
  "event": "review.completed",
  "review_id": "550e8400-...",
  "brief_id": "660e8400-...",
  "status": "passed",            // 或 "rejected"
  "score": 78,
  "timestamp": "2026-07-12T10:30:35Z"
}

// 审核执行失败（已达重试上限）
{
  "event": "review.failed",
  "review_id": "...",
  "brief_id": "...",
  "status": "failed",
  "error": "LLM call failed after 3 attempts",
  "timestamp": "2026-07-12T10:32:00Z"
}
```

### 5.4 发送策略

| 维度 | 策略 |
|------|------|
| URL 来源 | `brief_arbiter_reviews.webhook_url`（优先）或系统默认配置 `ARBITER_WEBHOOK_URL` |
| 重试 | MVP 不重试（前端轮询兜底） |
| 失败处理 | 静默丢弃 + 记录日志，不阻塞队列处理 |
| 事务安全 | 永远在事务提交**之后**发送 |

### 5.5 前端接收模式

```
┌──────────┐                  ┌──────────┐                  ┌──────────┐
│  前端     │                  │   API    │                  │  Worker  │
└────┬─────┘                  └────┬─────┘                  └────┬─────┘
     │ POST /briefs/:id/reviews    │                             │
     │  { webhook_url? }           │                             │
     │ ──────────────────────────▶ │                             │
     │ ◀── 202 + review_id         │                             │
     │     + brief_version         │  enqueue                    │
     │                             │ ──────────────────────────▶ │
     │                             │                             │
     │  [轮询]                      │                             │ [执行 LLM]
     │ GET .../reviews/:id          │                             │
     │ ──────────────────────────▶ │                             │
     │ ◀── status: "processing"    │                             │
     │                             │                             │
     │                             │  [更新 review + commit]     │
     │                             │ ◀────────────────────────── │
     │                             │                             │
     │  [或: webhook 推送]          │                             │
     │ ◀── POST /webhook           │ ◀────────────────────────── │
     │     event: review.completed  │                             │
     │                             │                             │
     │ GET .../reviews/:id          │                             │
     │ ──────────────────────────▶ │                             │
     │ ◀── status: "passed"        │                             │
```

## 6. 错误响应

```json
// 409 — 已有审核在处理中
{
  "error": {
    "code": "REVIEW_ALREADY_IN_PROGRESS",
    "message": "A review for this brief version is already in progress",
    "details": { "existing_review_id": "..." }
  }
}
```

## 7. 与现有 `send` 流程的集成

现有的 `submit-review` 端点（`POST /briefs/:id/editing?action=submit-review`）改造为异步：

```
submit-review 改造前（同步，force_skip）:
    直接创建 force_skipped review → 返回 200

submit-review 改造后（异步）:
    1. 防重检查（已有 processing → 409）
    2. 创建 brief_arbiter_reviews (status=processing, attempt_count=0, webhook_url=...)
    3. queue.enqueue(type=review, ref_id=review.id)
    4. 返回 202 + review_id + brief_version
```

完整的 brief 创建到 send 流程：

```
upstream 创建 brief
    │
    ├── POST /briefs                        → 创建 brief（editing）
    ├── POST .../editing?action=patch       → 修改内容（可多次）
    ├── POST .../editing?action=submit-review → 触发异步审核
    │   └── 返回 202，review.status = processing
    │
    ├── [Worker 异步执行]
    │   ├── 加载 brief-review skill → 调 LLM
    │   ├── 结论 passed → review.status = passed
    │   ├── 结论 rejected → review.status = rejected
    │   └── 执行失败 → re-enqueue（未达上限）或 failed（已达上限）
    │
    ├── [前端拿到结果]
    │   ├── passed → 可以 send
    │   ├── rejected → 显示问题，修改后重新 submit-review
    │   └── failed → 可重新触发审核
    │
    └── POST .../transfer?action=send       → 发送给 downstream
```

## 8. 配置清单

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 系统 webhook URL | `ARBITER_WEBHOOK_URL` | — | 默认回调地址（review 未指定时使用） |
| 队列后端 | `QUEUE_BACKEND` | `database` | 队列实现（database / redis） |
