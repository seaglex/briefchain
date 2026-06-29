## 1. 共享基础

- [x] 1.1 在 `web/lib/auth.ts` 中新增 `getSessionToken()` 用于 Server Component 读取 httpOnly Cookie。
- [x] 1.2 在 `web/lib/api.ts`（或 `web/lib/auth.ts`）新增服务端数据获取 helper，自动携带 `Authorization: Bearer <token>` 调用后端。
- [x] 1.3 在 `web/app/globals.css` 中补充列表、详情与创建页所需样式（`.brief-tabs`、`.feedback-type-icon` 等）。

## 2. 创建 Brief

- [x] 2.1 创建 `web/app/briefs/new/page.tsx`，实现创建 Brief 表单（标题、内容、优先级、预估人天、预期完成时间）。
- [x] 2.2 实现前端校验：标题和内容必填。
- [x] 2.3 创建 `POST /api/briefs` API Route，代理到后端 `POST /api/v1/briefs`。
- [x] 2.4 创建成功后跳转至新 Brief 详情页 `/briefs/[brief_id]`。

## 3. 列表页

- [x] 3.1 创建 `web/app/briefs/page.tsx`，默认展示 `role=assigned`，支持 `created` 与 `assigned` 切换（MVP 暂不支持 `all`）。
- [x] 3.2 实现 upstream_state 筛选：调用 `GET /api/v1/briefs?upstream_state=...`。
- [x] 3.3 实现 downstream_state 筛选：调用 `GET /api/v1/briefs?downstream_state=...`。
- [x] 3.4 实现优先级筛选：在已加载数据上前端过滤 P0/P1/P2/P3。
- [x] 3.5 实现 Brief 卡片渲染，展示 `upstream_state`、`downstream_state`、优先级、执行者，点击跳转 `/briefs/[brief_id]`。

## 4. 详情页基础结构

- [x] 4.1 创建 `web/app/briefs/[brief_id]/page.tsx`，Server Component 获取 Brief 详情与当前用户。
- [x] 4.2 实现详情头部：标题、upstream_state badge、downstream_state badge、优先级 badge、创建者/执行者信息、以及 `unfinalized_version` 可编辑 draft 徽标。
- [x] 4.3 实现内容/流转/Feedback 标签页切换。
- [x] 4.4 实现流转历史时间线展示（含 `from_user_name` / `to_user_name`）。
- [x] 4.5 实现 Feedback 列表展示（含 `is_to_down`、type、from/to 用户名字）。

## 5. Editing 阶段操作

- [x] 5.1 实现 patch 编辑功能：`upstream_state` 不是 `done`/`cancelled` 时显示编辑表单；对 `sent` 版本 patch 自动创建新 draft，调用 `POST /api/briefs/[id]/editing?action=patch`。
- [x] 5.2 实现 submit-review 功能：当前版本 status=draft 时显示“提交审查”，调用 `POST /api/briefs/[id]/editing?action=submit-review`。

## 6. Transfer 阶段操作

- [x] 6.1 实现 send 功能：版本 status=reviewed 时显示“发送给 downstream”，弹出用户选择器并填写 note，调用 `POST /api/briefs/[id]/transfer?action=send`。
- [x] 6.2 实现 accept 功能：`upstream_state=sent` 时显示“接受”，调用 `POST /api/briefs/[id]/transfer?action=accept`。
- [x] 6.3 实现 reject 功能：`upstream_state=sent` 时显示“拒绝”，弹出 reason 输入框，调用 `POST /api/briefs/[id]/transfer?action=reject`。

## 7. Upstream-actions 操作

- [x] 7.1 实现 cancel：`upstream_state` 非 done/cancelled 时显示，调用 `POST /api/briefs/[id]/upstream-actions?action=cancel`。
- [x] 7.2 实现 suspend/resume：`upstream_state=sent/in_process` 可 suspend，`upstream_state=suspended` 可 resume，调用对应 `upstream-actions` 端点。
- [x] 7.3 实现 approve：`upstream_state=in_process` + `downstream_state=submitted` 时显示，调用 `POST /api/briefs/[id]/upstream-actions?action=approve`。
- [x] 7.4 实现 reject_submit：`downstream_state=submitted` 时显示，调用 `POST /api/briefs/[id]/upstream-actions?action=reject_submit`。
- [x] 7.5 实现 update：`upstream_state=in_process` 时显示；`unfinalized_version` 为 null 时显示“推送更新”，不为 null 时显示“继续编辑更新”，调用 `POST /api/briefs/[id]/upstream-actions?action=update`。

## 8. Downstream-actions 操作

- [x] 8.1 实现 process（进度更新）：`upstream_state=in_process` 时显示，调用 `POST /api/briefs/[id]/downstream-actions?action=process`。
- [x] 8.2 实现 submit（提交完成）：`upstream_state=in_process` 时显示，调用 `POST /api/briefs/[id]/downstream-actions?action=submit`。
- [x] 8.3 实现 open（重开）：`upstream_state=in_process` 且 `downstream_state=submitted/delegated/blocked` 时显示，调用 `POST /api/briefs/[id]/downstream-actions?action=open`。
- [x] 8.4 实现 delegate：`upstream_state=in_process` 时显示，调用 `POST /api/briefs/[id]/downstream-actions?action=delegate`。
- [x] 8.5 实现 block：`upstream_state=in_process` 时显示，调用 `POST /api/briefs/[id]/downstream-actions?action=block`。

## 9. 用户选择器与写操作代理

- [x] 9.1 创建 `web/app/api/briefs/route.ts` 代理 `POST /api/v1/briefs`。
- [x] 9.2 创建 `web/app/api/briefs/[id]/editing/route.ts`、`/transfer/route.ts`、`/upstream-actions/route.ts`、`/downstream-actions/route.ts` 等写操作 API Route，从 Cookie 取 token 代理到后端对应分组端点。
- [x] 9.3 创建 `web/app/api/users/route.ts` 代理 `GET /api/v1/users`。
- [x] 9.4 创建 `UserSelector` 组件，调用 `/api/users` 加载用户列表并支持单选。

## 10. 导航与默认着陆页

- [x] 10.1 更新 `web/app/page.tsx`，登录后重定向到 `/briefs?role=assigned`。
- [x] 10.2 更新主应用 sidebar 与 topbar 的 Logo/导航链接，点击后跳转 `/briefs?role=assigned`。
- [x] 10.3 更新 `web/app/login/page.tsx` 与 `web/app/register/page.tsx`，登录/注册成功后跳转 `/`（会再重定向到 assigned 列表）。

## 11. 验证

- [x] 11.1 启动前后端，验证创建 Brief 成功后跳转详情页，初始 `upstream_state=editing`。
- [x] 11.2 验证列表页按角色（created/assigned）与 upstream/downstream 状态筛选。
- [x] 11.3 验证需求方可以 patch 编辑非终态 Brief 并 submit-review/send。
- [x] 11.4 验证执行方可以接受/拒绝 sent Brief。
- [x] 11.5 验证执行方可以 submit/open/delegate/block，需求方可以 approve/reject_submit/update。
- [x] 11.6 验证登录后自动进入“分配给我的”列表，点击 Logo 回到该列表。
