## Context

User API (`/auth`、`/users`) 已经实现，SQLAlchemy 模型（`Brief`、`BriefVersion`、`BriefTransferHistory`、`BriefChain`、`Feedback` 等）已按 `docs/mvp_design/01-brief-feedback-design.md` 更新为双状态模型（`upstream_state` + `downstream_state`）并增加了冗余名字段。API 设计文档 `docs/mvp_design/03-api-design.md` 已按新状态模型重新组织为 4 组端点：`/briefs/:id/editing`、`/briefs/:id/transfer`、`/briefs/:id/upstream-actions`、`/briefs/:id/downstream-actions`。本 change 需要把这些新 API 规范落到 OpenSpec，并后续实现为可运行的 FastAPI 路由。

## Goals / Non-Goals

**Goals:**
- 基于 FastAPI 实现 `/api/v1/briefs` 路由：创建、列表、详情（含 `unfinalized_version`）、editing 阶段操作（patch / submit-review）。
- 实现 `/api/v1/briefs/:brief_id/transfer?action=send|accept|reject`：邀约阶段流转，支持临时用户发送。
- 实现 `/api/v1/briefs/:brief_id/upstream-actions?action=cancel|suspend|resume|approve|reject_submit|update`：上游合约期操作。
- 实现 `/api/v1/briefs/:brief_id/downstream-actions?action=process|submit|open|delegate|block`：下游合约期操作。
- 实现 `/api/v1/briefs/:brief_id/versions`：列出所有版本（含 `status`）。
- 实现 `/api/v1/briefs/:brief_id/transfers`：列出流转历史（含收发人名字快照）。
- 实现 `/api/v1/briefs/:brief_id/feedbacks` 和 `/api/v1/feedbacks/:feedback_id`：反馈列表与详情（含 `is_to_down`、方向相关 type、收发人名字快照）。
- 实现 `/api/v1/chains`：chain 列表与详情（含 `owner_id` / `owner_name` / `priority`）。
- 复用已有的 JWT 认证、`get_current_user`、`get_db_session` 和统一错误响应。
- 遵循 `created_by` 拥有读写权限、`assigned_to` 拥有下游操作权限、其他人只读的 MVP 权限模型。
- 响应字段与 v0.8 API 设计对齐：列表/详情/版本三种模式，用户字段拆为 `*_id` + `*_name`。
- 编写覆盖主流程和权限控制的单元测试。

**Non-Goals:**
- 不实现 Arbiter LLM 自动审查（MVP 跳过，直接转 reviewed）。
- 不实现文件上传（`/files`），attachments 字段只存储 URL 元数据。
- 不实现内部 Kanban / Task 子系统。
- 不实现跨系统互操作（`bc://` 协议）。
- 不实现 feedback 的 Arbiter 审查和自动汇总。

## Decisions

- **路由组织**：
  - `src/briefchain/api/routes/briefs.py`：`/briefs` 主路由 + `/briefs/:id/editing` 子路由。
  - `src/briefchain/api/routes/brief_transfers.py`：`/briefs/:id/transfer` + `/briefs/:id/transfers`。
  - `src/briefchain/api/routes/brief_actions.py`（或合并到 briefs.py）：`/briefs/:id/upstream-actions` 和 `/briefs/:id/downstream-actions`。
  - `src/briefchain/api/routes/brief_versions.py`：`/briefs/:id/versions`。
  - `src/briefchain/api/routes/feedbacks.py`：`/briefs/:id/feedbacks` 和 `/feedbacks/:id`。
  - `src/briefchain/api/routes/chains.py`：`/chains`。
  - `src/briefchain/api/main.py`：注册上述路由。
- **Service 层**：
  - `src/briefchain/api/services/briefs.py`：封装 brief 的 CRUD、版本管理、状态机和权限校验，供 routes 调用。
  - 路由层只负责 HTTP 请求解析、调用 service、返回响应；业务逻辑和状态流转集中在 service。
- **Schema 组织**：
  - `src/briefchain/api/schemas/briefs.py`：brief 请求/响应模型（列表、详情、版本、创建、patch/review/update 请求）。
  - `src/briefchain/api/schemas/transfers.py`：流转记录响应。
  - `src/briefchain/api/schemas/feedbacks.py`：反馈请求/响应。
  - `src/briefchain/api/schemas/chains.py`：chain 响应（含树形结构）。
- **权限模型**：
  - 创建者（`created_by`）拥有 upstream 操作权限（editing、transfer send、upstream-actions）。
  - 被分配者（`assigned_to`）可接受/拒绝 transfer 和执行 downstream-actions。
  - 其他已认证用户只读（列表/详情/版本/历史/反馈/chain）。
- **版本管理**：
  - 创建 brief 时同步创建 `BriefVersion` v1，状态为 "draft"；`briefs.current_version` 初始为 null。
  - `PATCH /briefs/:id/editing?action=patch`：只操作 version.status。`draft`/`reviewed` 原地修改；`final` 不能修改，自动创建 v(n+1) draft（若已存在则报错）。patch 不同步 `briefs.title` / `priority` / `expected_completion_at`。
  - `POST /briefs/:id/editing?action=submit-review`：当前 draft 版本 → "reviewed"；不碰 brief state。
  - `POST /briefs/:id/transfer?action=send`：当前 reviewed 或 sent 版本 → "sent"，并同步 `briefs.current_version` / `title` / `priority` / `expected_completion_at`（邀约阶段桥梁，拒绝后可重新分配）。
  - `POST /briefs/:id/upstream-actions?action=update`：合约期桥梁，对 version 的操作与 send 相同，但记录在 feedbacks 并强制 `downstream_state=opened`。
  - 详情接口通过 `?version=` 参数返回指定版本内容，默认返回 `current_version` 内容；同时返回 `unfinalized_version` 字段标识可编辑 draft（null 表示无）。
- **状态流转**：
  - editing 阶段：patch（只改 version 内容/状态）、submit-review（版本 draft → reviewed，不改 brief state）。
  - transfer 阶段：send（editing/sent → sent，version→final，同步 current_version 等）、accept（sent → in_process, opened）、reject（sent → editing）。
  - upstream-actions（除 update 外只改 brief state）：cancel（→ cancelled，保留 downstream_state）、suspend（→ suspended，保留 downstream_state）、resume（→ in_process）、approve（→ done，保留 downstream_state）、reject_submit（downstream_state → opened）、update（新版本 sent，downstream_state → opened）。
  - downstream-actions（只改 brief state）：process（progress feedback，无状态变化）、submit（→ submitted）、open（→ opened）、delegate（→ delegated）、block（→ blocked）。
- **响应模式**：
  - 列表模式：`brief_id`, `title`, `upstream_state`, `downstream_state`, `priority`, `created_by_id`, `created_by_name`, `assigned_to_id`, `assigned_to_name`, `status_changed_by_id`, `status_changed_by_name`, `status_changed_at`, `updated_at`。
  - 详情模式：列表模式 + `root_id`, `parent_id`, `content`, `attachments`, `current_version`, `version`, `is_current`, `unfinalized_version`, `estimated_man_days`, `expected_completion_at`, `created_at`。
  - tree 模式：`brief_id`, `title`, `upstream_state`, `downstream_state`, `children`。
- **错误处理**：复用统一的 `{ "error": { "code": "...", "message": "...", "details": {} } }` 格式。
- **分页**：列表接口使用 cursor-based 分页（`page_cursor` + `page_size`）。MVP 阶段使用基于 `updated_at` + `brief_id` 的游标，降低实现复杂度。

## Risks / Trade-offs

- **状态组合复杂度** → 缓解：service 层维护有效状态矩阵，单元测试覆盖所有合法/非法组合。
- **Cursor 分页实现复杂度** → 缓解：MVP 使用 `updated_at` + `brief_id` 简单游标，后续可替换为更复杂的排序方案。
- **Brief 树形结构查询性能** → 缓解：chain 详情先查询所有 `WHERE root_id = chain_id` 的 briefs，在内存中构建树，MVP 数据量小可接受。
- **状态机权限分散在路由中** → 缓解：每个 action 路由显式检查当前状态和操作者身份，测试覆盖边界情况。
- **版本更新与 transfer 的 brief_version 不一致** → 缓解：send 操作记录发送时的 `current_version`，后续 update 不影响历史 transfer。
- **临时用户发送逻辑与现有 invite 服务耦合** → 缓解：复用 `invite-temp-user-auth` 的实现，send 服务统一处理 registered 和 temporary 两种 recipient。

## Migration Plan

- 本 change 依赖 `brief-model` 的数据模型更新（双状态 + 冗余字段）。
- 新增/调整路由、schema、service 文件，注册到现有 FastAPI app。
- 旧端点（`/briefs/:id/submit`、 `/briefs/:id/send` 等）被新分组端点取代，需在实现阶段同步更新测试。
- 升级后按新 API 聚类调用 brief 相关接口。

## Open Questions

- Chain 列表是否只返回当前用户参与的 chain？（MVP 返回全部 chain，后续按权限过滤。）
- Feedback 的 `confirmed_at` 在 MVP 中是否使用？（MVP 不实现 auto-generated feedback，confirmed_at 固定为 null。）
- 是否需要为 `/briefs/:id/upstream-actions?action=update` 提供独立的版本内容请求 schema，还是复用 `BriefUpdateRequest`？每个端点的独立比较清楚。
