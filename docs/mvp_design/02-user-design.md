# User 子系统设计

> 最后更新：2026-06-23

## 1. 设计原则

- 支持邮箱注册、手机号注册（registered）
- 支持三方登录（oauth：微信/Google/GitHub）
- 其他 BriefChain 用户（external），不能登录本系统，在自分系统操作
- 临时用户（temporary），无账号，通过邀请链接访问
- 用户 ID 使用 GUID 全局唯一，`external_ref` 字段防恶作剧
- 各用户类型通过 `user_type` 直接判断，避免复杂条件组合

## 2. 用户类型

| user_type | 能登录 | 关联数据 |
|---|---|---|
| `registered` | ✅ 密码登录 | `password_hash`（users 表内） |
| `oauth` | ✅ 三方登录 | `user_identites` 表 |
| `external` | ❌ 不能登录本系统 | `source_system` + `external_ref`（users 表内） |
| `temporary` | ❌ 邀请链接访问 | `brief_invites` 表 |

## 3. 用户模型

### 3.1 users（用户表）

```sql
users {
  id: GUID
  email: string | null
  phone: string | null
  name: string
  avatar_url: string | null

  user_type: "registered" | "oauth" | "external" | "temporary"

  -- registered 类型
  password_hash: string | null

  -- external 类型
  source_system: string | null   -- 来源 BriefChain 实例域名
  external_ref: string | null    -- 对方系统的用户 ID（正常情况 = id，防恶作剧）

  -- 升级追踪（仅登录已有账号场景填写）
  from_temporary_user_id: GUID | null  -- 若该注册用户通过「登录已有账号」接管了临时用户，
                                       -- 记录被接管的临时用户 UUID。
                                       -- 注册新账号场景不填（user_id 不变，原地升级）

  created_at: timestamp
  updated_at: timestamp
}
```

设计决策：
- `user_type` 直接判断用户类型，不用组合多个字段做条件
- `password_hash` 仅 `registered` 类型使用，其余类型为 null
- `source_system` + `external_ref` 仅 `external` 类型使用
- `from_temporary_user_id` 仅登录已有账号接管临时用户时填写，方便追溯哪些历史 brief/transfer 原本属于该临时用户
- 一个用户可以有多个三方登录绑定，通过 user_identites 表关联

### 3.2 user_identities（三方登录绑定表）

```sql
user_identities {
  id: GUID
  user_id: GUID

  provider: "wechat" | "google" | "github"
  provider_user_id: string       -- 第三方返回的用户 ID（微信用 unionid）

  created_at: timestamp
}
```

设计决策：
- 微信登录使用 `unionid` 作为 `provider_user_id`，支持跨应用统一账号
- 用户注册后可将三方登录绑定到已有账号

### 3.3 brief_invites（邀请链接表）

> 详见 `docs/mvp_design/05-invite-link-design.md`

```sql
brief_invites {
  id: GUID
  brief_id: GUID                 -- 关联的 brief
  nonce: string(24)              -- DB 查找索引
  token: string(255)             -- HMAC 签名完整串
  name: string                   -- 接收人名字（显示用途）
  temporary_user_id: GUID        -- 创建邀请时同步创建的临时用户
  from_user: GUID                -- 发送人
  accept_deadline: timestamp     -- 接受/拒绝截止时间
  complete_deadline: timestamp   -- 完成截止时间
  invalidated_at: timestamp | null  -- 失效时间（注册或登录后标记）
  final_user_id: GUID | null        -- 最终执行操作的用户 UUID（注册时 = temporary_user_id，登录已有账号时 = 注册用户 UUID）
  created_at: timestamp
  updated_at: timestamp
}
```

临时用户（`temporary` 类型）流程：
1. upstream 发送 brief 给外部邮箱/手机 → 系统创建 `user_type="temporary"` 的 user 记录
2. 创建 BriefInvite 记录 + HMAC 签名 token → 构造 URL（不发邮件）
3. 用户打开链接 → 验证 token → 允许查看、接受或拒绝
4. 临时用户可注册升级（user_id 不变）或登录已有账号接管

## 4. 团队模型

### 4.1 teams（团队表）

```sql
teams {
  id: GUID
  name: string
  created_by: GUID
  created_at: timestamp
  updated_at: timestamp
}
```

### 4.2 team_memberships（团队成员表）

```sql
team_memberships {
  id: GUID
  team_id: GUID
  user_id: GUID
  role: "admin" | "member"
  joined_at: timestamp
}
```

## 5. 跨系统互操作

两个 BriefChain 实例互操作时：

- 用户 ID 使用 GUID，全局不冲突，可直接引用
- 本系统用户被邀请到外部系统时，外部系统创建 `user_type="external"` 的记录
- `source_system` 记录用户来源，`external_ref` 存对方系统的用户 ID
- `temporary` 类型用户通过 `brief_invites` 表验证访问权限

**临时用户升级（已设计，详见 05-invite-link-design.md 5.3）：**
- 注册新账号：`user_id` 不变，原地升级 `user_type` → `registered`，邀请链接标记失效
- 登录已有账号：将 brief.assigned_to 更新为注册用户 UUID，邀请链接标记失效，已发生的 transfer/feedback 不改
