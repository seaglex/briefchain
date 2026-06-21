# User 子系统设计

> 最后更新：2026-06-21

## 1. 设计原则

- 支持邮箱注册、手机号注册（registered）
- 支持三方登录（oauth：微信/Google/GitHub）
- 其他 BriefChain 用户（external），不能登录本系统，在自分系统操作
- 临时用户（temporary），无账号，通过邮件 token 访问
- 用户 ID 使用 GUID 全局唯一，`external_ref` 字段防恶作剧
- 各用户类型通过 `user_type` 直接判断，避免复杂条件组合

## 2. 用户类型

| user_type | 能登录 | 关联数据 |
|---|---|---|
| `registered` | ✅ 密码登录 | `password_hash`（users 表内） |
| `oauth` | ✅ 三方登录 | `user_identites` 表 |
| `external` | ❌ 不能登录本系统 | `source_system` + `external_ref`（users 表内） |
| `temporary` | ❌ token 访问 | `email_tokens` 表 |

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

  created_at: timestamp
  updated_at: timestamp
}
```

设计决策：
- `user_type` 直接判断用户类型，不用组合多个字段做条件
- `password_hash` 仅 `registered` 类型使用，其余类型为 null
- `source_system` + `external_ref` 仅 `external` 类型使用
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

### 3.3 email_tokens（外部用户访问令牌）

```sql
email_tokens {
  token: string                  -- URL 里的 token（随机 GUID）
  email: string                  -- 接收邮件的邮箱
  brief_id: GUID                 -- 关联的 brief
  expires_at: timestamp          -- 链接过期时间
  used_at: timestamp | null      -- 是否已使用（防止重放）
}
```

外部用户（`temporary` 类型）流程：
1. upstream 输入外部邮箱发送 brief
2. 系统创建 `user_type="temporary"` 的 user 记录
3. 生成 email_token，发送邮件
4. 用户点链接 → 验证 token → 允许操作该 brief
5. 完成后不需要注册，后续再收到 brief 复用同一 user 记录

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
- `temporary` 类型用户通过 `email_tokens` 表验证访问权限

**账号合并（后续）：**
`temporary` 或 `external` 用户后续注册正式账号时，通过 email 匹配，将历史记录合并到正式账号。
