## Context

User API (`/auth`、`/users`) 已经实现，SQLAlchemy 模型（`Brief`、`BriefVersion`、`BriefTransferHistory`、`BriefChain`、`Feedback` 等）和 Alembic 迁移也已落地。API 设计文档 `docs/mvp_design/03-api-design.md` 已定义 `/briefs`、`/briefs/:brief_id/versions`、`/briefs/:brief_id/transfers`、`/briefs/:brief_id/feedbacks`、`/feedbacks/:feedback_id` 和 `/chains` 的接口规范。本 change 需要将这些接口实现为可运行的 FastAPI 路由，覆盖 brief 的 CRUD、状态流转、版本追溯、流转历史、反馈和 chain 查询。

## Goals / Non-Goals

**Goals:**
- 基于 FastAPI 实现 `/api/v1/briefs` 路由：创建、列表、详情、更新、状态流转。
- 实现 `/api/v1/briefs/:brief_id/versions` 路由：列出所有版本。
- 实现 `/api/v1/briefs/:brief_id/transfers` 路由：列出流转历史。
- 实现 `/api/v1/briefs/:brief_id/feedbacks` 和 `/api/v1/feedbacks/:feedback_id` 路由：反馈的创建、列表与详情。
- 实现 `/api/v1/chains` 路由：chain 列表与详情（含树形结构）。
- 复用已有的 JWT 认证、`get_current_user`、`get_db_session` 和统一错误响应。
- 遵循 `created_by` 拥有读写权限、其他人只读的 MVP 权限模型。
- 编写覆盖主流程和权限控制的单元测试。

**Non-Goals:**
- 不实现 Arbiter LLM 自动审查（MVP 跳过，直接转 reviewed）。
- 不实现文件上传（`/files`），attachments 字段只存储 URL 元数据。
- 不实现内部 Kanban / 工作状态管理。
- 不实现跨系统互操作（`bc://` 协议）。
- 不实现 feedback 的 Arbiter 审查和自动汇总。

## Decisions

- **路由组织**：
  - `src/briefchain/api/routes/briefs.py`：`/briefs` 主路由，包含 CRUD 和 lifecycle 子路由。
  - `src/briefchain/api/routes/brief_versions.py`：`/briefs/:brief_id/versions`（列表）和 `/briefs/:brief_id/versions/:version`（详情）。
  - `src/briefchain/api/routes/brief_transfers.py`：`/briefs/:brief_id/transfers`。
  - `src/briefchain/api/routes/feedbacks.py`：`/briefs/:brief_id/feedbacks` 和 `/feedbacks/:feedback_id`。
  - `src/briefchain/api/routes/chains.py`：`/chains`。
  - `src/briefchain/api/main.py`：注册上述路由。
- **Service 层**：
  - `src/briefchain/api/services/briefs.py`：封装 brief 的 CRUD、版本管理、状态机和权限校验，供 routes 调用。
  - 路由层只负责 HTTP 请求解析、调用 service、返回响应；业务逻辑和状态流转集中在 service。
- **Schema 组织**：
  - `src/briefchain/api/schemas/briefs.py`：brief 请求/响应模型（列表、详情、版本、创建、更新）。
  - `src/briefchain/api/schemas/transfers.py`：流转记录响应。
  - `src/briefchain/api/schemas/feedbacks.py`：反馈请求/响应。
  - `src/briefchain/api/schemas/chains.py`：chain 响应（含树形结构）。
- **权限模型**：
  - 创建者（`created_by`）拥有读写权限。
  - 被分配者（`assigned_to`）可接受/拒绝/完成 brief。
  - 其他已认证用户只读（列表/详情/版本/历史/反馈/chain）。
- **版本管理**：
  - 创建 brief 时同步创建 `BriefVersion` v1。
  - 更新 brief（PATCH）时创建新版本，并递增 `Brief.current_version`。
  - 详情接口通过 `?version=` 参数返回指定版本内容，默认返回当前版本。
- **状态流转**：
  - `submit`: draft → reviewed
  - `send`: reviewed → sent，创建 `BriefTransferHistory`
  - `accept`: sent → accepted，更新 transfer.accepted_at
  - `reject`: sent → draft，更新 transfer.rejected_at 和 rejection_reason
  - `cancel`: 任意非 done 状态 → cancelled
  - `complete`: accepted → done
- **响应模式**：
  - 列表模式包含 `brief_id`, `title`, `status`, `priority`, `created_by`, `assigned_to`, `updated_at`。
  - 详情模式额外包含 `content`, `attachments`, `current_version`, `version`, `is_current`。
- **错误处理**：复用统一的 `{ "error": { "code": "...", "message": "...", "details": {} } }` 格式。
- **分页**：列表接口使用 cursor-based 分页（`page_cursor` + `page_size`）。MVP 阶段使用基于 `updated_at` + `brief_id` 的游标，降低实现复杂度。

## Risks / Trade-offs

- **Cursor 分页实现复杂度** → 缓解：MVP 使用 `updated_at` + `brief_id` 简单游标，后续可替换为更复杂的排序方案。
- **Brief 树形结构查询性能** → 缓解：chain 详情先查询所有 `WHERE root_id = chain_id` 的 briefs，在内存中构建树，MVP 数据量小可接受。
- **状态机权限分散在路由中** → 缓解：每个 lifecycle 路由显式检查当前状态和操作者身份，测试覆盖边界情况。
- **版本更新与 transfer 的 brief_version 不一致** → 缓解：send 操作记录发送时的 `current_version`，后续更新不影响历史 transfer。

## Migration Plan

- 本 change 为纯新增 API，不改动现有数据库表结构。
- 新增路由和 schema 文件，注册到现有 FastAPI app。
- 升级后即可调用新的 brief 相关接口。

## Open Questions

- Chain 列表是否只返回当前用户参与的 chain？（MVP 返回全部 chain，后续按权限过滤。）
- Feedback 的 `confirmed_at` 在 MVP 中是否使用？（MVP 不实现 auto-generated feedback，confirmed_at 固定为 null。）
