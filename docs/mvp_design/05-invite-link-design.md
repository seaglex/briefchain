# BriefChain 邀请链接设计

> 版本：MVP v1.1
> 最后更新：2026-06-23
> 关联文档：03-api-design.md（第 2.6 节 send_brief 已同步更新）

---

## 1. 设计目标

将 Brief 发送给**未注册用户**，对方打开链接即可查看、接受或拒绝。业务逻辑与系统内完全一致，唯一区别是鉴权方式。

---

## 2. 核心原则

**邀请 = 创建临时用户 + 生成鉴权 URL**

- 发送时立即创建临时用户（`user_type=temporary`），所有业务记录（transfer、assigned_to）直接使用该用户 UUID
- 业务逻辑零改动：accept/reject 等操作复用现有函数
- 鉴权层变化：邀请端点用 HMAC Token 替代 JWT
- 不发邮件/短信：只构造 URL，用户自行通过任意方式分享

---

## 3. BriefInvite 数据模型

邀请表的作用：解释临时用户的来源 + 记录 Token/过期时间。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| brief_id | UUID | 关联 brief（外键） |
| nonce | String(24) | 随机 nonce，DB 查找索引 |
| token | String(255) | HMAC 签名完整串（唯一索引） |
| name | String(255) | 接收人名字（显示用途） |
| temporary_user_id | UUID | 创建邀请时同步创建的临时用户（外键 → users.id） |
| from_user | UUID | 发送人（已注册用户） |
| accept_deadline | datetime(tz) | 接受/拒绝截止时间 |
| complete_deadline | datetime(tz) | 完成截止时间 |
| invalidated_at | datetime(tz) \| null | 失效时间（注册或登录后标记） |
| **final_user_id** | UUID \| null | 临时用户注册/登录后的最终用户 UUID（同 temporary_user_id 或注册用户 UUID） |
| created_at | datetime(tz) | 创建时间 |
| updated_at | datetime(tz) | 更新时间 |

> **注意**：无 `consumed` / `consumed_at` 字段。accept/reject 本身受 brief 状态约束（不能 accept 两次），无需额外消费标记。过期后自动不可操作。`invalidated_at` 用于标记「临时用户已注册/登录，邀请链接不再可用」。`final_user_id` 用于追踪「是哪个账号最终执行了操作」，注册时 = temporary_user_id，登录已有账号时 = 注册用户 UUID。

---

## 4. Token 机制

### 4.1 生成

```
token = brief_id_hex : nonce : accept_deadline_epoch : HMAC-SHA256(brief_id_hex : nonce : accept_deadline_epoch, jwt_secret_key)
```

- `nonce` = `secrets.token_urlsafe(16)`（16 字符 URL-safe 随机串）
- `accept_deadline_epoch` = Unix timestamp（秒）
- 签名密钥复用 `jwt_secret_key`

### 4.2 校验流程

1. 解析 token → 提取 `brief_id`, `nonce`, `accept_deadline_epoch`, `signature`
2. HMAC 签名比对 → 拒绝伪造（**无需查 DB**）
3. 检查 `accept_deadline_epoch` > 当前时间 → 拒绝过期
4. DB 查 nonce → 找到 invite 记录
5. 检查 `invalidated_at` 是否为 null → 拒绝已失效的邀请

### 4.3 为什么 nonce 做 DB 索引

完整 HMAC 签名约 64 字符 hex，做索引过长。nonce 16 字符足够短且不可伪造（签名校验已保证安全性），先签名验证再 DB 查 nonce，两层防御。

---

## 5. 临时用户

### 5.1 创建时机

发送给未注册用户时，立即创建：

```python
User(
    id=uuid4(),
    name=invite_name,           # 取 recipient_name 参数
    email=recipient_email,      # 可选
    phone=recipient_phone,      # 可选
    user_type="temporary",      # 无密码、无登录能力
    password_hash=None,
)
```

### 5.2 特性

- `user_type=temporary`：无密码，不能通过 `/auth/login` 登录
- 仅通过邀请链接操作（Token 鉴权）
- `brief.assigned_to` 和 `transfer.to_user` 直接指向该临时用户 UUID → 与系统内用户完全一致

### 5.3 临时用户升级

临时用户有两种方式升级为正式用户，均需携带 `temporary_user_id`（前端从邀请页面传入）。

#### 场景一：注册新账号（user_id 不变）

临时用户在邀请页面点击「注册」，前端将 `token` 和 `temporary_user_id` 传给注册端点：

```json
POST /auth/register
{
  "email": "lisi@example.com",
  "password": "secure_password",
  "name": "李四",
  "temporary_user_id": "临时用户UUID",
  "invite_token": "签名token"    // 用于校验 + 直接定位 brief_id，无需额外查询
}
```

后端处理：
1. 校验 `invite_token`（HMAC 签名 + 未过期 + 未失效），从中提取 `brief_id`
2. 找到 `user_type=temporary` 的用户行（校验 temporary_user_id = invite.temporary_user_id）
3. **原地升级**：`user_type` → `registered`，设置 `password_hash`，更新 `email`/`phone`/`name`
4. `user_id` 不变 → `brief.assigned_to`、`transfer.to_user` 等所有引用自动有效，无需改动
5. **批量失效所有 invite**：`UPDATE brief_invites SET invalidated_at = now WHERE temporary_user_id = T AND invalidated_at IS NULL`
6. 返回 JWT（同一个 user_id）

#### 场景二：登录已有账号

临时用户已有注册账号，在邀请页面点击「登录」，前端将 `token` 和 `temporary_user_id` 传给登录端点：

```json
POST /auth/login
{
  "email_or_phone": "lisi@example.com",
  "password": "secure_password",
  "temporary_user_id": "临时用户UUID",
  "invite_token": "签名token"    // 用于校验 + 直接定位 brief_id
}
```

后端处理：
1. 校验 `invite_token`（HMAC 签名 + 未过期 + 未失效），从中提取 `brief_id`
2. 正常登录 → 找到注册用户 R
3. 校验 temporary_user_id = invite.temporary_user_id
4. **批量收回活跃 brief**：`UPDATE briefs SET assigned_to = R WHERE assigned_to = T AND status NOT IN ('done', 'cancelled')`
5. **批量失效所有 invite**：`UPDATE brief_invites SET invalidated_at = now, final_user_id = R WHERE temporary_user_id = T AND invalidated_at IS NULL`
6. `users.from_temporary_user_id = T`（记录 R 接管了哪个临时用户）
7. **已经发生的记录不改**：`transfer.to_user = T`、`feedback.from_user = T` 保持不变（T 行仍在 DB 中，是有效引用）
8. 返回 JWT（注册用户 R 的 token）

> **为什么传 invite_token 而不仅传 temporary_user_id**：
> - token 携带 brief_id（从签名中提取），后端直接定位 brief，无需通过 temporary_user_id 扫描 brief 表
> - 同时完成校验（签名有效、未过期、未失效）与数据提取，一次操作
> - 防止攻击者伪造 temporary_user_id 绑架他人邀请记录

> **为什么已发生的记录不改**：
> - transfer/feedback 是历史事实，记录的是「当时谁做了什么」
> - T 行不会删除，作为历史引用始终有效
> - 只改 brief 的「当前状态」属性（assigned_to），不改「历史记录」

#### 邀请失效后的用户体验

邀请链接失效后，`GET /invites/{token}` 返回：

```json
{
  "error": { "code": "INVITE_INVALIDATED", "message": "此邀请已失效，请登录您的账号继续操作" }
}
```

前端引导用户跳转到登录页。

---

## 6. 发送流程变更

### 6.1 send_brief 变更（详见 03-api-design.md 第 2.6 节）

`POST /briefs/:brief_id/send` 新增参数 `is_temporary_user`（bool），区分两种发送方式：

- `is_temporary_user=false`（方式一）：`assigned_to` = 已注册用户 UUID（原逻辑不变）
- `is_temporary_user=true`（方式二）：通过邀请链接发送，`recipient_email` / `recipient_phone` 可选（至多填一个），`recipient_name` 可选

方式二的后端查找逻辑：

```
is_temporary_user=true，收到 recipient_email/phone（可能都为空）
1. 若填了 email 或 phone → 在 users 表查找
   ├─ 找到 registered/oauth 用户 → 自动转方式一（assigned_to = 该用户 UUID）
   ├─ 找到 temporary 用户 T
   │   ├─ T.final_user_id 为空 → 复用 T.user_id，新建 invite
   │   └─ T.final_user_id = R  → 用 R，走方式一（T 已升级，不再发 invite）
   └─ 没找到 → 新建临时用户
2. 若 email/phone 都没填 → 直接新建临时用户
3. 设置 brief.assigned_to = 临时用户 UUID
4. 创建 BriefInvite 记录 + HMAC 签名 token
5. 创建 TransferHistory(from_user=creator, to_user=临时用户UUID)
6. 返回 invite URL（不发邮件，用户自行分享）
```

> **final_user_id 分支的意义**：T 有 `final_user_id` 说明该临时用户已经登录/注册过，所有 invite 已失效。如果还往 T 发 invite，对方打开链接会看到「链接已失效」。正确做法是跳过 T，直接用 `final_user_id` 对应的注册用户走方式一。

### 6.2 返回格式

发送给已注册用户（不变）：
```json
{
  "brief": { "status": "sent", "assigned_to": "user_uuid", ... },
  "transfer": { "sent_at": "...", "accepted_at": null, "rejected_at": null }
}
```

发送给外部用户：
```json
{
  "brief": { "status": "sent", "assigned_to": "临时用户UUID", ... },
  "transfer": { "to_user": "临时用户UUID", "sent_at": "...", ... },
  "invite": {
    "invite_url": "/invites/{token}",
    "accept_deadline": "2026-06-29T22:30:00Z",
    "complete_deadline": "2026-07-20T22:30:00Z"
  }
}
```

---

## 7. 邀请链接端点（公开，无需 JWT）

### 7.1 查看邀请

`GET /invites/{token}`

- 不需要 `Authorization` header
- 校验：HMAC 签名 → nonce 查 DB → 检查 accept_deadline

```json
// Response 200
{
  "invite": {
    "name": "李四",
    "from_user": { "id": "guid", "name": "张三" },
    "accept_deadline": "2026-06-29T22:30:00Z",
    "complete_deadline": "2026-07-20T22:30:00Z"
  },
  "brief": {
    // 详情模式，与 GET /briefs/:brief_id 一致
  }
}
```

```json
// Response 410 — 过期
{
  "error": { "code": "INVITE_EXPIRED", "message": "邀请链接已过期" }
}

// Response 410 — 失效（临时用户已注册或登录）
{
  "error": { "code": "INVITE_INVALIDATED", "message": "此邀请已失效，请登录您的账号继续操作" }
}
```

### 7.2 接受

`POST /invites/{token}/accept`

- 不需要 JWT
- 校验 token + accept_deadline 未过期 + brief 当前状态为 sent
- 内部调用 `accept_brief(session, brief_id, temporary_user_id)` — 复用现有函数

```json
// Request（可选，修正名字）
{ "name": "李四" }

// Response 200
{
  "brief": { "status": "accepted", ... },
  "transfer": { "accepted_at": "..." },
  "message": "已接受。注册账号可继续追踪此 Brief"
}
```

### 7.3 拒绝

`POST /invites/{token}/reject`

- 不需要 JWT
- 校验同上（需在 accept_deadline 内）
- 内部调用 `reject_brief(session, brief_id, temporary_user_id, reason)` — 复用现有函数

```json
// Request
{ "reason": "验收标准不清晰" }

// Response 200
{
  "brief": { "status": "draft", ... },
  "transfer": { "rejected_at": "...", "rejection_reason": "..." }
}
```

### 7.4 标记阻塞

`POST /invites/{token}/block`

- 不需要 JWT
- 前提：brief 状态为 `accepted`，当前时间在 `complete_deadline` 内
- 内部调用 `block_brief(session, brief_id, temporary_user_id, reason)` — 复用现有函数

```json
// Request
{ "reason": "依赖的设计稿还未完成，无法推进" }

// Response 200
{
  "brief": { "status": "blocked", ... },
  "feedback": {
    "id": "guid",
    "type": "blocked",
    "content": "依赖的设计稿还未完成，无法推进",
    "from_user": { "id": "临时用户UUID", "name": "李四" },
    "created_at": "..."
  }
}
```

> 阻塞解除（blocked → accepted）需要由发送方（已注册用户）在系统内操作，不提供邀请链接端点

### 7.5 标记完成（含结果）

`POST /invites/{token}/complete`

- 不需要 JWT
- 前提：brief 状态为 `accepted`，当前时间在 `complete_deadline` 内
- 内部调用 `complete_brief(session, brief_id, temporary_user_id, result)` — 复用现有函数

```json
// Request
{
  "result": "已完成首页性能优化，首屏加载时间从 3.2s 降至 1.3s",
  "attachments": [
    { "name": "性能对比报告.png", "url": "/api/v1/files/...", "type": "image" }
  ]
}

// Response 200
{
  "brief": { "status": "done", ... },
  "feedback": {
    "id": "guid",
    "type": "completion",
    "content": "已完成首页性能优化...",
    "attachments": [...],
    "from_user": { "id": "临时用户UUID", "name": "李四" },
    "created_at": "..."
  }
}
```

> complete_deadline 过期后不能标记完成，需联系发送方延期

---

## 8. 鉴权层实现

邀请端点不需要 JWT，使用 Token 参数验证：

```python
# dependencies.py 新增
def get_invite_from_token(session: SessionDep, token: str) -> BriefInvite:
    """验证邀请 token，返回 BriefInvite 记录。"""
    # 1. HMAC 签名校验（不查 DB）
    # 2. 检查 accept_deadline 未过期
    # 3. DB 查 nonce → BriefInvite 记录
    # 4. 检查 invalidated_at 为 null（未失效）

InviteDep = Annotated[BriefInvite, Depends(get_invite_from_token)]
```

```python
# routes/invites.py
router = APIRouter(prefix="/invites", tags=["invites"])

@router.get("/{token}")
def view_invite(invite: InviteDep, session: SessionDep):
    ...

@router.post("/{token}/accept")
def accept_invite(invite: InviteDep, session: SessionDep, body: AcceptInviteRequest | None = None):
    # 校验使用 accept_deadline
    user_id = invite.temporary_user_id
    return accept_brief(session, invite.brief_id, user_id)  # 复用！

@router.post("/{token}/reject")
def reject_invite(invite: InviteDep, session: SessionDep, body: RejectInviteRequest):
    # 校验使用 accept_deadline
    user_id = invite.temporary_user_id
    return reject_brief(session, invite.brief_id, user_id, body.reason)  # 复用！

@router.post("/{token}/block")
def block_invite(invite: InviteDep, session: SessionDep, body: BlockInviteRequest):
    # 校验使用 complete_deadline（brief 已 accepted）
    user_id = invite.temporary_user_id
    return block_brief(session, invite.brief_id, user_id, body.reason)  # 复用！

@router.post("/{token}/complete")
def complete_invite(invite: InviteDep, session: SessionDep, body: CompleteInviteRequest):
    # 校验使用 complete_deadline（brief 已 accepted）
    user_id = invite.temporary_user_id
    return complete_brief(session, invite.brief_id, user_id, body.result, body.attachments)  # 复用！
```

> **两套 deadline 的校验分工**：
> - `accept_deadline`：适用于 accept / reject（接受/拒绝阶段）
> - `complete_deadline`：适用于 block / complete（执行阶段，brief 处于 accepted）
> - InviteDep 校验签名和失效状态；各端点内部再检查对应的 deadline 和 brief 当前状态

---

## 9. 后端代码变更清单

| 文件 | 变更 |
|------|------|
| models/invite.py | 新增 BriefInvite 模型（含 `invalidated_at`、`final_user_id`） |
| models/brief.py | 新增 invites 关系 |
| models/user.py | user_type 新增 temporary；删除 EmailToken；新增 `from_temporary_user_id` 字段 |
| models/enums.py | UserType 新增 TEMPORARY |
| schemas/invites.py | 新增 InviteViewResponse / AcceptInviteRequest / RejectInviteRequest / BlockInviteRequest / CompleteInviteRequest |
| schemas/auth.py | RegisterRequest / LoginRequest 新增 `temporary_user_id`、`invite_token` 可选参数 |
| services/invites.py | 新增 token 生成/校验 + invite 失效逻辑（回填 final_user_id） |
| services/auth.py | 注册：原地升级，校验 invite_token 提取 brief_id；登录：用 brief_id 直接更新 assigned_to，填写 from_temporary_user_id |
| routes/invites.py | 新增邀请链接路由（5 个端点：view / accept / reject / block / complete） |
| routes/auth.py | 注册/登录端点增加 invite_token 处理 |
| dependencies.py | 新增 InviteDep |
| services/briefs.py | send_brief 支持外部用户（方式二） |
| alembic/ | 新增 migration：brief_invites 表 + users.from_temporary_user_id + EmailToken 表删除 |

---

## 10. 未来扩展

- **邀请链接验证码**：敏感 Brief 可选择要求接收人输入 6 位短码（通过邮箱/短信单独发送）才能操作
- **邀请通知**：可选自动发送邮件/短信通知（目前用户自行分享 URL）
- **临时用户清理**：长期未升级且所有邀请已过期的临时用户，可定期清理（需确认无活跃引用）
