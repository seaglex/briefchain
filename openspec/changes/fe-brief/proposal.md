## Why

BriefChain MVP 的认证入口已经实现，但用户登录后缺少 Brief 相关的核心交互界面：无法查看自己创建或接收的 Brief、无法创建/编辑/发送/接受/拒绝 Brief、也无法提交进度或阻塞反馈。没有这些页面，需求方与执行方之间的工作流转无法闭环，因此需要补齐 Brief 创建、列表与详情页。

## What Changes

- 新增创建 Brief 页面 `/briefs/new`，支持填写标题、内容、优先级、预估人天。
- 新增 Brief 列表页 `/briefs`，默认展示“分配给我的”，支持切换“我创建的”；MVP 暂不支持“全部”视图。
- 列表支持按状态筛选；按优先级筛选由前端在已加载数据上完成（后端列表接口暂不支持按优先级过滤）。
- 新增 Brief 详情页 `/briefs/[brief_id]`，展示内容、版本、流转历史与 Feedback。
- 需求方（created_by）在详情页可对 draft 状态 Brief 进行编辑、提交审查，对 reviewed 状态 Brief 选择下游用户并发送。
- 执行方（assigned_to）在详情页可对 sent 状态 Brief 接受或拒绝（需填写原因），对 accepted 状态 Brief 标记完成或提交 blocked 反馈（均需填写说明）。
- 点击左上角 Logo 以及登录/注册成功后自动跳转到“分配给我的”列表页。
- 复用 `docs/mvp_design/04-frontend-prototype.html` 的视觉风格与组件类名。

## Capabilities

### New Capabilities

- `fe-brief-create`: 创建新 Brief 页面与表单。
- `fe-brief-list`: Brief 列表页，包含角色切换（我创建的/分配给我的）、状态与优先级筛选。
- `fe-brief-detail`: Brief 详情页，包含内容展示、版本/流转/Feedback 标签页。
- `fe-brief-actions`: Brief 核心操作，包括编辑、发送、接受、拒绝、完成、提交 blocked/complete feedback。
- `fe-user-selector`: 在发送 Brief 时选择下游用户的用户选择器。

### Modified Capabilities

<!-- 无现有 spec 需要修改 -->

## Impact

- 新增 `web/app/briefs/new/`、`web/app/briefs/`、`web/app/briefs/[brief_id]/` 等页面与相关组件。
- 需要读取 `briefchain_session` Cookie 并代理/携带 JWT 调用后端 `/api/v1/briefs`、`/api/v1/users`、`/api/v1/feedbacks` 接口。
- 主应用首页 `/` 需重定向到 `/briefs?role=assigned`。
- 依赖 `fe-user` 已完成的认证 Cookie 与 Middleware。
