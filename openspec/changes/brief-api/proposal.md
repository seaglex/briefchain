## Why

User API 已经落地，但项目目前缺少 BriefChain 核心的 brief 生命周期 API。为了实现 MVP 中 brief 的创建、流转、版本追溯和反馈闭环，需要基于 FastAPI 实现 `/briefs`、编辑阶段端点、transfer 端点、upstream/downstream action 端点、`/briefs/:brief_id/versions`、 `/briefs/:brief_id/transfers`、 `/briefs/:brief_id/feedbacks`、 `/feedbacks/:feedback_id` 和 `/chains` 等相关接口，并与最新的双状态数据模型对齐。

## What Changes

- 扩展 `src/briefchain/api/` 模块，新增/调整 brief 相关路由和 Pydantic schema。
- 实现 `/briefs` 路由：创建、列表查询（按 `upstream_state` / `downstream_state` / `role` / `root_id` 过滤）、详情获取（`?version=`）。
- 实现 `/briefs/:brief_id/editing?action=patch|review`：编辑阶段内容修改和提交审查。
- 实现 `/briefs/:brief_id/transfer?action=send|accept|reject`：邀约阶段流转，支持 registered 和 temporary 两种接收方式。
- 实现 `/briefs/:brief_id/upstream-actions?action=cancel|suspend|resume|approve|reject_submit|update`：上游合约期操作。
- 实现 `/briefs/:brief_id/downstream-actions?action=process|submit|open|delegate|block`：下游合约期操作。
- 实现 `/briefs/:brief_id/versions` 路由：列出所有版本（含 `status`）。
- 实现 `/briefs/:brief_id/transfers` 路由：列出流转历史（含收发人名字快照）。
- 实现 `/briefs/:brief_id/feedbacks` 路由：反馈列表（支持 `type` / `is_to_down` 过滤）。
- 实现 `/feedbacks/:feedback_id` 路由：单个反馈详情。
- 实现 `/chains` 路由：chain 列表（含 `owner_id` / `owner_name` / `priority`）与详情（含树形结构）。
- 复用已有的 JWT 认证、当前用户依赖和统一错误响应模型。
- 补充单元测试，覆盖正常流程、权限控制和状态机约束。

## Capabilities

### New Capabilities

- `brief-crud`: Brief 的创建、列表查询、详情获取、editing 阶段 patch/review。
- `brief-lifecycle`: Brief 合约期状态流转（upstream-actions / downstream-actions）。
- `brief-transfer`: Brief 邀约阶段流转（send / accept / reject），支持临时用户邀请。
- `brief-versions`: Brief 版本列表与历史版本内容查看。
- `brief-transfers`: Brief 流转历史查询。
- `brief-feedbacks`: Brief 反馈的列表与详情查看。
- `brief-chains`: Chain 列表与树形详情查询。

### Modified Capabilities

- 无上游外部能力变更（本 change 只扩展 Brief 子系统 API，不修改 User 子系统）。

## Impact

- 新增/调整 FastAPI 路由和 Pydantic schema，扩展 `src/briefchain/api/` 模块。
- 新增 `/api/v1/briefs/:id/editing`、 `/api/v1/briefs/:id/transfer`、 `/api/v1/briefs/:id/upstream-actions`、 `/api/v1/briefs/:id/downstream-actions`、 `/api/v1/briefs`、 `/api/v1/feedbacks`、 `/api/v1/chains` 路由。
- 复用已实现的 JWT 认证与依赖注入；依赖 `brief-model` 的双状态和冗余字段变更。
- 不实现 Arbiter LLM 自动审查、文件上传、内部 Kanban / Task 子系统和跨系统互操作（MVP 后续）。
