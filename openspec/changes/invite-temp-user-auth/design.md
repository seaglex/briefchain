## Context

BriefChain MVP 已具备用户注册/登录、Brief 创建与发送、接受/拒绝等基础能力。当前 `POST /briefs/:brief_id/transfer?action=send` 只接受 `assigned_to`（已注册用户 UUID），外部协作者必须先注册账号才能接收 Brief，增加了协作门槛。

设计文档 `docs/mvp_design/05-invite-link-design.md` 已明确方案：发送 Brief 时可为未注册用户创建临时用户并生成 HMAC Token 邀请链接；接收方无需 JWT 即可通过链接查看、接受、拒绝、标记 blocked 或标记 done；临时用户可在邀请页注册升级或登录已有账号接管 Brief。

本变更将 05 文档中的设计落地到后端 API 与数据模型。

## Goals / Non-Goals

**Goals:**
- `POST /briefs/:brief_id/transfer?action=send` 支持 `is_temporary_user=true`：email/phone 可选；按 users 表查找结果分别走系统内发送、复用临时用户或创建新临时用户。
- 公开端点 `/invites/{token}/transfer?action=accept|reject` 与 `/invites/{token}/downstream-actions?action=process|submit|open|delegate|block` 支持基于 HMAC Token 的临时用户鉴权。
- `POST /auth/register` 支持可选 `temporary_user_id` + `invite_token`：找到该 invite 关联的临时用户并原地升级为 `registered`；同时将该临时用户名下所有非 `done` / `cancelled` 的 brief 的 `assigned_to` 迁移到新注册用户。
- `POST /auth/login` 支持可选 `temporary_user_id` + `invite_token`：将该临时用户名下所有非 `done` / `cancelled` 的 brief 的 `assigned_to` 迁移到已登录用户。
- 临时用户升级/登录后，关联邀请链接标记失效，避免链接被再次使用。
- 已发生的历史记录（transfer、feedback）保持原 `to_user`/`from_user` 不变，只修改 Brief 当前归属。

**Non-Goals:**
- 不实现邮件/短信自动通知，邀请 URL 由用户自行分享。
- 不实现邀请链接二次验证码（MVP 后续扩展）。
- 不实现跨 BriefChain 实例的 `external` 用户互操作（MVP 不做）。
- 不删除或合并历史临时用户行；临时用户作为历史引用保留。

## Decisions

### 1. 邀请 = 创建或复用临时用户 + 生成 HMAC Token
- **选择**：`is_temporary_user=true` 时，按 email/phone 在 users 表中查找：已注册用户或已有 final_user_id 的临时用户走系统内发送；无 final_user_id 的临时用户复用 user_id；未找到则创建新临时用户（允许无 email/phone）。随后创建 `BriefInvite`。
- **理由**：避免同一联系方式产生多个临时用户；已升级过的临时用户通过 `final_user_id` 指向其正式账号，再次收到邀请时直接派给正式账号。
- **替代方案**：每次发送都创建新临时用户。这会导致同一邮箱对应多个临时用户行，增加混乱。

### 2. Token 格式使用 `brief_id:nonce:deadline:signature`
- **选择**：Token 由 `brief_id_hex`、`nonce`、`accept_deadline_epoch`、HMAC-SHA256 签名组成，用 `:` 分隔。
- **理由**：
  - 签名校验无需查 DB，可快速拒绝伪造或篡改。
  - `nonce` 16 字符足够随机且便于做唯一索引；完整签名 64 字符 hex 仅用于校验，不做索引。
  - 过期时间放在 token 中，过期检查无需查 DB。
- **替代方案**：纯随机 UUID 做 token，DB 查索引。这需要每次请求都查 DB 才能校验过期与签名，无法优先拒绝伪造请求。

### 3. 签名密钥复用 `jwt_secret_key`
- **选择**：HMAC 签名使用与 JWT 相同的 secret。
- **理由**：MVP 阶段减少额外配置；JWT secret 已是高熵密钥。
- **风险**：如果未来 JWT secret 轮换，需要同时重新签发邀请链接或兼容旧签名。见下方风险与迁移计划。

### 4. 临时用户升级时 `user_id` 不变
- **选择**：注册升级时原地修改 `user_type=registered`、`password_hash=...`，不新建用户行。
- **理由**：`brief.assigned_to`、`transfer.to_user`、`feedback.from_user` 等所有引用自动保持有效，无需数据迁移。
- **替代方案**：创建新用户后把历史记录迁移过去。这会导致 transfer/feedback 等历史事实被改写，且迁移逻辑复杂。

### 5. 登录/注册迁移所有活跃 brief 的 `assigned_to`
- **选择**：临时用户 T 注册或登录已有账号 R 后，将 T 名下所有状态不是 `done` / `cancelled` 的 brief 的 `assigned_to` 从 T 改为 R；transfer/feedback 中指向 T 的记录不变。
- **理由**：临时用户可能同时持有多个活跃 brief；一次认证应全部接管。transfer/feedback 记录的是「当时谁做了什么」这一历史事实，只改当前归属即可保证业务继续。
- **替代方案**：只迁移当前 invite 对应的 brief。这会导致同一临时用户的其他 brief 仍指向失效的临时用户，需要再次登录/注册才能处理。

### 6. 邀请失效与最终用户追踪
- **选择**：注册或登录后，将该临时用户关联的所有未失效邀请标记 `invalidated_at=now()`，并将 `final_user_id` 设为最终注册用户的 UUID。
- **理由**：保留邀请历史便于审计；`final_user_id` 可追踪临时用户最终归属哪个正式账号；一次认证使该临时用户的所有邀请链接同时失效。

### 7. 用户行记录来源临时用户
- **选择**：当临时用户通过注册升级为正式用户，或登录关联到已有账号时，在最终用户行的 `from_temporary_user_id` 字段记录原临时用户 UUID。
- **理由**：保留用户演化链路，便于审计与后续数据追踪。

### 8. 临时用户不能通过 `/auth/login` 登录
- **选择**：`temporary` 类型用户没有 `password_hash`，登录校验在查到用户后增加 `user_type != temporary` 判断。
- **理由**：临时用户只允许通过邀请 Token 操作；若允许密码登录，则与「无密码」定义冲突。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| Token 伪造导致未授权访问 Brief | HMAC-SHA256 签名 + nonce DB 唯一索引双重校验；Token 包含过期时间。 |
| 临时用户长期未清理导致 users 表膨胀 | MVP 不自动清理；临时用户行占用极小，可在后续版本评估过期邀请清理策略。 |
| JWT secret 轮换后旧邀请链接失效 | 轮换 secret 时同步重新生成或迁移 token；MVP 阶段 secret 不频繁轮换。 |
| 注册/登录时 `invite_token` 与已注册账号邮箱/手机冲突 | 升级前校验 invite 有效且 temporary_user_id 匹配；注册时若邮箱/手机已注册则返回明确错误。 |
| 登录接管时多个 Brief 同时指向同一临时用户 | 遍历该临时用户的所有 `assigned_to=临时用户ID` 且状态为 `sent`/`accepted` 的 brief，逐个迁移到注册用户。 |

## Migration Plan

1. 创建 Alembic migration：
   - 在 `users.user_type` 检查/新增 `temporary`（取决于当前 enum 实现是 CHECK 还是 native ENUM）。
   - 创建 `brief_invites` 表，含 `nonce` 与 `token` 唯一索引，以及 `final_user_id` 外键。
   - 在 `users` 表增加 `from_temporary_user_id` 外键（可为空）。
   - 如果存在旧的 `EmailToken` 相关表/列，执行删除（按 05 文档代码变更清单）。
2. 部署代码后，现有已注册用户的登录/注册行为不变；`send_brief` 外部用户分支立即可用。
3. 回滚：回滚 migration 会删除 `brief_invites` 表；若已有外部用户邀请数据，需先确认无未完成 Brief，否则回滚会导致临时用户相关 brief 失去邀请关联（但 brief 与 transfer 数据仍保留）。

## Open Questions

1. `users.user_type` 当前在代码中是 Python Enum 还是 PostgreSQL native ENUM？migration 需要据此选择 ALTER TYPE ADD VALUE 或调整 CHECK 约束。
2. 当前项目是否已存在 `EmailToken` 表/模型？如不存在，migration 中删除步骤可省略。
3. 邀请 URL 的前端基础路径（如 `https://app.briefchain.example/invites/{token}`）是否由后端配置决定，还是后端只返回相对路径 `/invites/{token}`？MVP 按 05 文档返回相对路径。
