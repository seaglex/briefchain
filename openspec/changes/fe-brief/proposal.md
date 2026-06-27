## Why

BriefChain MVP 的认证入口已经实现，但用户登录后缺少 Brief 相关的核心交互界面：无法查看自己创建或接收的 Brief、无法创建/编辑/发送/接受/拒绝 Brief、也无法提交进度、阻塞或完成反馈。没有这些页面，需求方与执行方之间的工作流转无法闭环，因此需要补齐 Brief 创建、列表与详情页，并与后端新的双状态 API 对齐。

## What Changes

- 新增创建 Brief 页面 `/briefs/new`，支持填写标题、内容、优先级、预估人天、预期完成时间。
- 新增 Brief 列表页 `/briefs`，默认展示“分配给我的”，支持切换“我创建的”；MVP 暂不支持“全部”视图。
- 列表支持按 `upstream_state` / `downstream_state` 筛选；按优先级筛选由前端在已加载数据上完成（后端列表接口暂不支持按优先级过滤）。
- 新增 Brief 详情页 `/briefs/[brief_id]`，展示内容、版本、流转历史与 Feedback。
- 需求方（created_by）在详情页可对 `upstream_state=editing` 的 Brief 进行 patch 编辑和提交审查（review）。
- 需求方在版本 reviewed 后选择下游用户并发送（`POST /briefs/:id/transfer?action=send`），支持 registered 和 temporary 两种接收方式。
- 需求方在合约期可执行 cancel / suspend / resume / approve / reject_submit / update 等 upstream-actions。
- 执行方（assigned_to）在 `upstream_state=sent` 时可接受或拒绝 transfer。
- 执行方在 `upstream_state=in_process` 时可执行 process / submit / open / delegate / block 等 downstream-actions。
- 点击左上角 Logo 以及登录/注册成功后自动跳转到“分配给我的”列表页。
- 复用 `docs/mvp_design/04-frontend-prototype.html` 的视觉风格与组件类名。

## Capabilities

### New Capabilities

- `fe-brief-create`: 创建新 Brief 页面与表单。
- `fe-brief-list`: Brief 列表页，包含角色切换（我创建的/分配给我的）、upstream/downstream 状态筛选与优先级筛选。
- `fe-brief-detail`: Brief 详情页，包含内容展示、版本/流转/Feedback 标签页，以及基于双状态矩阵的角色感知操作按钮。
- `fe-brief-actions`: Brief 核心操作，覆盖 editing（patch/review）、transfer（send/accept/reject）、upstream-actions（cancel/suspend/resume/approve/reject_submit/update）、downstream-actions（process/submit/open/delegate/block）。
- `fe-user-selector`: 在发送 Brief 时选择下游用户的用户选择器。

### Modified Capabilities

- 无现有前端 spec 需要修改（本 change 只新增页面与组件）。

## Impact

- 新增 `web/app/briefs/new/`、`web/app/briefs/`、`web/app/briefs/[brief_id]/` 等页面与相关组件。
- 需要读取 `briefchain_session` Cookie 并代理/携带 JWT 调用后端新的分组端点（`/editing`、`/transfer`、`/upstream-actions`、`/downstream-actions`）。
- 主应用首页 `/` 需重定向到 `/briefs?role=assigned`。
- 依赖 `fe-user` 已完成的认证 Cookie 与 Middleware。
- 与 `fe-temp-user-brief` 共用发送弹窗中的 temporary user 选项。
