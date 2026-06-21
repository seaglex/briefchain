## Context

`fe-user` 已实现基于 Next.js + httpOnly Cookie 的认证入口。当前 `web/app/page.tsx` 只是一个占位主应用 shell，没有任何 Brief 数据展示或操作。后端已提供 `/api/v1/briefs`、`/api/v1/briefs/:id/*`、`/api/v1/users`、`/api/v1/feedbacks` 等完整接口（见 `docs/mvp_design/03-api-design.md`）。本次变更需要在前端实现 Brief 创建、列表与详情交互。

## Goals / Non-Goals

**Goals:**
- 实现创建 Brief 页面 `/briefs/new`，支持填写标题、内容、优先级、预估人天。
- 实现 Brief 列表页，支持“我创建的 / 分配给我的”角色切换（MVP 暂不支持“全部”），支持状态筛选与前端优先级筛选。
- 实现 Brief 详情页，按用户角色展示不同操作：需求方可编辑/发送，执行方可接受/拒绝/完成/提交 blocked 反馈。
- 实现用户选择器，用于发送 Brief 时选择 downstream。
- 登录/注册成功及点击 Logo 后默认进入“分配给我的”列表。

**Non-Goals:**
- 不实现“全部”Brief 列表视图（后端支持但 MVP 暂不暴露）。
- 不实现 Chain 树形视图、看板、设置等页面。
- 不实现文件上传与附件管理。
- 不实现 Arbiter 自动审查（MVP 为人工提交直接转 reviewed）。

## Decisions

### 1. 页面路由约定
- `/briefs/new`：创建新 Brief 页面。
- `/briefs?role=assigned`：Brief 列表页，默认角色为 assigned。
- `/briefs?role=created`：列表页切换到我创建的。
- `/briefs/[brief_id]`：Brief 详情页。
- `/`：重定向到 `/briefs?role=assigned`。

**理由**：与后端 `role` 查询参数保持一致，URL 即状态，刷新后可恢复。

### 2. 创建 Brief 页面使用 Client Component + API Route
- **理由**：创建表单需要客户端状态管理（受控输入、校验），提交后需要跳转到新 Brief 详情页。
- **做法**：`web/app/briefs/new/page.tsx` 为 Client Component，提交时调用 `POST /api/briefs`，API Route 代理到后端 `POST /api/v1/briefs`，成功返回新 brief id 后前端跳转。

### 3. 列表页使用 Server Component + 服务端取数
- **理由**：列表数据相对稳定，Server Component 可以直接读取 `briefchain_session` Cookie，向后端发起带 `Authorization: Bearer <token>` 的请求，避免客户端暴露 token 管理逻辑，也减少首屏 loading。
- **做法**：在 `web/lib/auth.ts` 新增 `getSessionToken()`（读取 httpOnly Cookie），列表页通过该 token 调用 `GET /api/v1/briefs?role=...&status=...`。

### 4. 详情页为 Server Component，交互操作为 Client Component
- **理由**：详情内容（title、content、attachments、versions、transfers、feedbacks）适合服务端渲染；而编辑、发送、接受、拒绝、完成、提交 feedback 等需要表单状态与事件处理，必须使用 Client Component。
- **做法**：`page.tsx` 为 Server Component，负责获取 brief 详情与当前用户；将操作按钮抽取到 `BriefActions` Client Component，通过 props 传入 brief 状态、当前用户角色等信息。

### 5. 写操作通过内部 API Route 代理
- **理由**：Client Component 无法读取 httpOnly Cookie，因此 POST / PATCH / send / accept / reject / complete / feedback 等写操作需要 Next.js API Route 代理到后端。
- **做法**：创建以下 API Route：
  - `POST /api/briefs` → 后端 `POST /api/v1/briefs`
  - `PATCH /api/briefs/[id]` → 后端 `PATCH /api/v1/briefs/:id`
  - `POST /api/briefs/[id]/send` → 后端 `POST /api/v1/briefs/:id/send`
  - `POST /api/briefs/[id]/accept` → 后端 `POST /api/v1/briefs/:id/accept`
  - `POST /api/briefs/[id]/reject` → 后端 `POST /api/v1/briefs/:id/reject`
  - `POST /api/briefs/[id]/complete` → 后端 `POST /api/v1/briefs/:id/complete`
  - `POST /api/briefs/[id]/feedbacks` → 后端 `POST /api/v1/briefs/:id/feedbacks`
  API Route 从 Cookie 中取出 JWT，以 `Authorization: Bearer <token>` 调用后端，并透传响应。

### 6. 用户选择器通过 `/api/v1/users` 加载
- **理由**：发送 Brief 时需要选择 downstream 用户，后端已提供用户列表接口。
- **做法**：在发送弹窗中调用 `GET /api/v1/users`（经内部代理或直接 Server Component 预取），展示用户名称列表，选择后调用 send API。

### 7. 筛选策略
- 状态筛选：调用后端 `GET /api/v1/briefs?status=...`。
- 优先级筛选：后端列表接口不支持 `priority` 参数，因此在已加载数据上进行前端过滤。
- **理由**：避免为优先级筛选单独增加后端改动，保持本次变更前端范围内完成。

### 8. 默认着陆页
- **理由**：用户角色以执行方为主，登录后优先看到“分配给我的”更符合工作流。
- **做法**：Middleware 对 `/` 的未登录重定向保持不变；登录后访问 `/` 时，Server Component 直接 307 到 `/briefs?role=assigned`。注册/登录页的 `router.replace("/")` 会进一步被重定向到 `/briefs?role=assigned`。

### 9. 样式复用
- **理由**：保持与原型一致的视觉风格。
- **做法**：继续使用 `globals.css` 中的 `.card`、`.badge`、`.btn`、`.brief-item`、`.detail-tabs` 等类名；新增 `.brief-tabs`、`feedback-type-icon` 等少量样式。

## Risks / Trade-offs

- **[Risk]** 列表接口不支持优先级过滤，前端过滤在数据量大时不准确。  
  → **Mitigation**：MVP 数据量小，可接受；后续在后端增加 `priority` 查询参数后改为服务端过滤。
- **[Risk]** 详情页 Server Component 与操作 Client Component 之间状态同步需要刷新页面。  
  → **Mitigation**：每次操作成功后调用 `router.refresh()` 重新获取详情数据，MVP 阶段简单可靠。
- **[Risk]** 用户列表接口返回脱敏信息，但发送时只需要 `id`，不影响功能。  
  → **Mitigation**：选择器展示 `name` 即可。
- **[Trade-off]** 写操作均走 API Route 代理，增加了文件数量。  
  → **Mitigation**：代理逻辑简单统一，便于后续改为 Server Actions 或直连。

## Migration Plan

1. 在 `web/lib/auth.ts` 增加服务端 Cookie 读取 helper。
2. 创建 `web/app/briefs/new/page.tsx` 创建 Brief 页面及 `POST /api/briefs` 代理。
3. 创建 `web/app/briefs/page.tsx` 列表页及筛选组件。
4. 创建 `web/app/briefs/[brief_id]/page.tsx` 详情页与操作组件。
5. 创建 `web/app/api/briefs/...` 写操作代理路由。
6. 更新 `web/app/page.tsx`，登录后重定向到 `/briefs?role=assigned`。
7. 更新 `web/middleware.ts`（如有必要）与 sidebar 导航链接。
8. 启动前后端，创建测试 Brief，验证创建、列表、详情、发送、接受、拒绝、完成、反馈流程。

## Open Questions

- 列表页是否需要显示分页？后端使用 cursor 分页，MVP 可先展示第一页，后续再加分页 UI。
- 详情页的版本内容切换是否需要支持？原型有计划，MVP 可先展示当前版本，隐藏版本选择器或仅展示只读版本号。
- 发送 Brief 时是否需要附带 note？后端 `SendBriefRequest` 支持 `note`，MVP 可选填写。
