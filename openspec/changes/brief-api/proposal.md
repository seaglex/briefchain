## Why

User API 已经落地，但项目目前缺少 BriefChain 核心的 brief 生命周期 API。为了实现 MVP 中 brief 的创建、流转、版本追溯和反馈闭环，需要基于 FastAPI 实现 `/briefs`、`/briefs/:brief_id/versions`、`/briefs/:brief_id/transfers`、`/briefs/:brief_id/feedbacks`、`/feedbacks/:feedback_id` 和 `/chains` 等相关接口。

## What Changes

- 扩展 `src/briefchain/api/` 模块，新增 brief 相关路由和 Pydantic schema。
- 实现 `/briefs` 路由：创建、列表查询、详情获取、更新、状态流转（submit/send/accept/reject/cancel/complete）。
- 实现 `/briefs/:brief_id/versions` 路由：列出 brief 的所有版本。
- 实现 `/briefs/:brief_id/transfers` 路由：列出 brief 的流转历史。
- 实现 `/briefs/:brief_id/feedbacks` 路由：创建和列出反馈。
- 实现 `/feedbacks/:feedback_id` 路由：获取单个反馈详情。
- 实现 `/chains` 路由：列出 chains 和获取 chain 详情（含树形结构）。
- 复用已有的 JWT 认证、当前用户依赖和统一错误响应模型。
- 补充单元测试，覆盖正常流程、权限控制和状态机约束。

## Capabilities

### New Capabilities

- `brief-crud`: Brief 的创建、列表查询、详情获取和更新。
- `brief-lifecycle`: Brief 状态流转（submit、send、accept、reject、cancel、complete）。
- `brief-versions`: Brief 版本列表与历史版本内容查看。
- `brief-transfers`: Brief 流转历史查询。
- `brief-feedbacks`: Brief 反馈的创建、列表与详情查看。
- `brief-chains`: Chain 列表与树形详情查询。

### Modified Capabilities

- 无

## Impact

- 新增 FastAPI 路由和 Pydantic schema，扩展 `src/briefchain/api/` 模块。
- 新增 `/api/v1/briefs`、`/api/v1/feedbacks`、`/api/v1/chains` 路由。
- 复用已实现的 JWT 认证与依赖注入，不改动现有 SQLAlchemy 模型表结构。
- 不实现 Arbiter LLM 自动审查、文件上传、内部 Kanban 状态和跨系统互操作（MVP 后续）。
