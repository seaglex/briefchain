## 1. 共享基础

- [x] 1.1 在 `web/lib/auth.ts` 中新增 `getSessionToken()` 用于 Server Component 读取 httpOnly Cookie。
- [x] 1.2 在 `web/lib/api.ts`（或 `web/lib/auth.ts`）新增服务端数据获取 helper，自动携带 `Authorization: Bearer <token>` 调用后端。
- [x] 1.3 在 `web/app/globals.css` 中补充列表、详情与创建页所需样式（`.brief-tabs`、`.feedback-type-icon` 等）。

## 2. 创建 Brief

- [x] 2.1 创建 `web/app/briefs/new/page.tsx`，实现创建 Brief 表单（标题、内容、优先级、预估人天）。
- [x] 2.2 实现前端校验：标题和内容必填。
- [x] 2.3 创建 `POST /api/briefs` API Route，代理到后端 `POST /api/v1/briefs`。
- [x] 2.4 创建成功后跳转至新 Brief 详情页 `/briefs/[brief_id]`。

## 3. 列表页

- [x] 3.1 创建 `web/app/briefs/page.tsx`，默认展示 `role=assigned`，支持 `created` 与 `assigned` 切换（MVP 暂不支持 `all`）。
- [x] 3.2 实现状态筛选：调用 `GET /api/v1/briefs?status=...`。
- [x] 3.3 实现优先级筛选：在已加载数据上前端过滤 P1/P2/P3。
- [x] 3.4 实现 Brief 卡片渲染，点击跳转 `/briefs/[brief_id]`。

## 4. 详情页基础结构

- [x] 4.1 创建 `web/app/briefs/[brief_id]/page.tsx`，Server Component 获取 Brief 详情与当前用户。
- [x] 4.2 实现详情头部：标题、状态 badge、优先级 badge、创建者/执行者信息。
- [x] 4.3 实现内容/流转/Feedback 标签页切换。
- [x] 4.4 实现流转历史时间线展示。
- [x] 4.5 实现 Feedback 列表展示。

## 5. 需求方操作

- [x] 5.1 实现编辑功能：draft 状态显示编辑表单，调用 `PATCH /api/v1/briefs/[id]`。
- [x] 5.2 实现发送功能：reviewed 状态显示“发送给 downstream”按钮，弹出用户选择器并填写 note，调用 `POST /api/v1/briefs/[id]/send`。
- [x] 5.3 实现提交审查功能（可选，若需要 draft → reviewed）：调用 `POST /api/v1/briefs/[id]/submit`。

## 6. 执行方操作

- [x] 6.1 实现接受功能：sent 状态显示“接受”按钮，调用 `POST /api/v1/briefs/[id]/accept`。
- [x] 6.2 实现拒绝功能：sent 状态显示“拒绝”按钮，弹出 reason 输入框，调用 `POST /api/v1/briefs/[id]/reject`。
- [x] 6.3 实现完成通知功能：accepted 状态显示“标记完成”按钮，弹出完成文档输入框，调用 `POST /api/v1/briefs/[id]/complete` 并创建 `complete` feedback。
- [x] 6.4 实现阻塞通知功能：accepted 状态显示“标记阻塞”按钮，弹出阻塞原因输入框，调用 `POST /api/v1/briefs/[id]/feedbacks` 创建 `blocked` feedback。

## 7. 用户选择器与写操作代理

- [x] 7.1 创建 `web/app/api/briefs/route.ts` 代理 `POST /api/v1/briefs`。
- [x] 7.2 创建 `web/app/api/briefs/[id]/send/route.ts` 等写操作 API Route，从 Cookie 取 token 代理到后端。
- [x] 7.3 创建 `web/app/api/users/route.ts` 代理 `GET /api/v1/users`。
- [x] 7.4 创建 `UserSelector` 组件，调用 `/api/users` 加载用户列表并支持单选。

## 8. 导航与默认着陆页

- [x] 8.1 更新 `web/app/page.tsx`，登录后重定向到 `/briefs?role=assigned`。
- [x] 8.2 更新主应用 sidebar 与 topbar 的 Logo/导航链接，点击后跳转 `/briefs?role=assigned`。
- [x] 8.3 更新 `web/app/login/page.tsx` 与 `web/app/register/page.tsx`，登录/注册成功后跳转 `/`（会再重定向到 assigned 列表）。

## 9. 验证

- [x] 9.1 启动前后端，验证创建 Brief 成功后跳转详情页。
- [x] 9.2 验证列表页按角色（created/assigned）与状态筛选。
- [x] 9.3 验证需求方可以编辑 draft Brief 并发送给下游用户。
- [x] 9.4 验证执行方可以接受/拒绝 sent Brief。
- [x] 9.5 验证执行方可以标记完成和提交 blocked 反馈。
- [x] 9.6 验证登录后自动进入“分配给我的”列表，点击 Logo 回到该列表。
