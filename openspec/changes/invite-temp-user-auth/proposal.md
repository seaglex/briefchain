## Why

BriefChain 需要把 Brief 发送给尚未注册的下游用户。当前 `send_brief` 只支持已注册用户，导致外部协作者必须预先注册才能接收任务。通过「邀请链接 + 临时用户」机制，发送方可以立即把 Brief 派给任意邮箱/手机，接收方点击链接即可查看、接受或拒绝，无需先完成注册流程。

## What Changes

- 新增 `brief_invites` 表与 `BriefInvite` 模型，用于存储邀请 nonce、token、过期时间与失效时间。
- 扩展 `UserType` 枚举，新增 `temporary` 类型；临时用户无密码、不能通过 `/auth/login` 登录。
- `POST /briefs/:brief_id/send` 支持 `is_temporary_user=true`：email/phone 可选；按 users 表查找结果分别走系统内发送、复用临时用户或创建新临时用户。
- 新增公开端点 `GET /invites/{token}`、`POST /invites/{token}/accept`、`POST /invites/{token}/reject`、`POST /invites/{token}/blocked`、`POST /invites/{token}/done`，使用 Token 鉴权替代 JWT。
- `POST /auth/register` 支持可选 `brief_id`：找到该 Brief 的 `assigned_to` 临时用户并原地升级为 `registered`；同时迁移该临时用户所有非 `done` / `cancelled` 的 brief。
- `POST /auth/login` 支持可选 `brief_id`：将该临时用户所有非 `done` / `cancelled` 的 brief 的 `assigned_to` 迁移到已登录用户，已发生的历史记录（transfer/feedback）保持不变。
- 新增 `services/invites.py` 负责 token 生成/校验与邀请失效逻辑；新增 `routes/invites.py` 与 `dependencies.py` 中的 `InviteDep`。
- 新增 Alembic migration：创建 `brief_invites` 表，删除旧的 `EmailToken` 相关表（如存在）。

## Capabilities

### New Capabilities

- `brief-invite-link`: Brief 邀请链接的生成、Token 校验、邀请页面查看、接受、拒绝、标记 blocked 与标记 done。覆盖 `POST /briefs/:brief_id/send` 的外部用户分支与 `/invites/{token}` 系列公开端点。
- `temporary-user`: 临时用户模型与生命周期。覆盖 `UserType.TEMPORARY`、临时用户创建规则、邀请有效期内通过 Token 操作 Brief 的鉴权方式。
- `temp-user-upgrade`: 临时用户升级为正式用户或关联到已有账号。覆盖 `POST /auth/register` 与 `POST /auth/login` 的 `brief_id` 参数及后续数据迁移/失效逻辑。

### Modified Capabilities

- （无现有 spec 需要修改；`send_brief` 的行为扩展已在 `brief-invite-link` 中描述。）

## Impact

- 后端：新增/修改 models、schemas、services、routes、dependencies 与 migration。
- API：新增 `/invites/{token}` 公开端点；`/auth/register` 与 `/auth/login` 新增可选字段；`/briefs/:brief_id/send` 新增外部用户分支。
- 数据库：新增 `brief_invites` 表；`users.user_type` 增加 `temporary`。
- 前端：邀请页面通过 Token 调用公开端点，并在注册/登录时传入 `brief_id`。
- 安全：HMAC Token 复用 JWT secret，nonce 做 DB 索引，签名校验优先于 DB 查询。
