# BriefChain REST API 设计文档

> 版本：MVP v0.3
> 最后更新：2026-06-23
> 基础路径：`/api/v1`

---

## 设计原则

- **JWT 认证**：登录后所有请求带 `Authorization: Bearer <token>`
- **权限模型（MVP）**：`created_by` 有全部读写权限，其他人有只读权限
- **状态码**：标准 HTTP 状态码，错误返回统一格式
- **分页**：游标分页（cursor-based），避免 offset 性能问题

---

## 统一错误格式

```json
{
  "error": {
    "code": "BRIEF_NOT_FOUND",
    "message": "Brief 不存在或无权限访问",
    "details": {}
  }
}
```

---

## 1. 认证（`/auth`）

### 1.1 注册

`POST /auth/register`

```json
// Request
{
  "email": "user@example.com",      // 可选，email 和 phone 至少提供一个
  "phone": "+86 138 0000 0000",   // 可选
  "password": "secure_password",
  "name": "张三",
  "temporary_user_id": null,      // 可选，邀请页面传入的临时用户 UUID
  "invite_token": null            // 可选，邀请链接 token（与 temporary_user_id 配对，用于校验 + 提取 brief_id）
}

// Response 201 — 普通注册
{
  "user": { 
    "id": "guid", 
    "email": "...", 
    "phone": "...",
    "name": "...", 
    "user_type": "registered" 
  },
  "token": "jwt_token"
}

// Response 201 — 临时用户升级注册（invite_token + temporary_user_id 有效）
{
  "user": { 
    "id": "同一UUID", 
    "email": "...", 
    "phone": "...",
    "name": "...", 
    "user_type": "registered" 
  },
  "token": "jwt_token",
  "upgraded_from_temporary": true
}
```

> 校验规则：
> - `email` 和 `phone` 至少提供一个
> - 如果提供 `email`，格式需合法且未注册
> - 如果提供 `phone`，格式需合法且未注册
> - 若 `invite_token` + `temporary_user_id` 均有效：校验 token 签名和有效期，提取 brief_id，原地升级（`user_type` → `registered`，`user_id` 不变），邀请链接标记失效（详见 05-invite-link-design.md 5.3）

### 1.2 登录

`POST /auth/login`

```json
// Request
{
  "email_or_phone": "user@example.com",  // 或 "+86 138 0000 0000"
  "password": "secure_password",
  "temporary_user_id": null,      // 可选，邀请页面传入的临时用户 UUID
  "invite_token": null            // 可选，邀请链接 token（与 temporary_user_id 配对，用于校验 + 提取 brief_id）
}

// Response 200 — 普通登录
{
  "user": { 
    "id": "guid", 
    "email": "...", 
    "phone": "...",
    "name": "...", 
    "user_type": "registered" 
  },
  "token": "jwt_token"
}

// Response 200 — 登录并接管临时用户
{
  "user": { 
    "id": "注册用户UUID", 
    "email": "...", 
    "phone": "...",
    "name": "...", 
    "user_type": "registered" 
  },
  "token": "jwt_token",
  "linked_temporary_user": "临时用户UUID"
}
```

> 后端自动识别 `email_or_phone` 是邮箱还是手机（含 `+` 号或纯数字为手机）
> 若 `invite_token` + `temporary_user_id` 均有效：校验 token，提取 brief_id，直接更新该 brief 的 assigned_to 为注册用户 UUID，邀请链接标记失效，已发生的 transfer/feedback 不改（详见 05-invite-link-design.md 5.3）

### 1.3 微信扫码登录（MVP 后续）

`POST /auth/wechat`

```json
// Request
{ "code": "wechat_oauth_code" }

// Response 200
{
  "user": { 
    "id": "guid", 
    "email": null,      // 三方登录用户可能无邮箱
    "phone": null,      // 三方登录用户可能无手机
    "name": "...", 
    "user_type": "oauth" 
  },
  "token": "jwt_token",
  "is_new": false
}
```

### 1.4 获取当前用户

`GET /auth/me`

```
Response 200
{
  "user": { 
    "id": "guid", 
    "email": "...", 
    "phone": "...",
    "name": "...", 
    "user_type": "registered" 
  }
}
```

### 1.5 登出

`POST /auth/logout`

```
Response 204
```

---

## 2. Brief（`/briefs`）

> **响应模式说明**：
> Brief 接口有三种响应模式：
> | 模式 | 包含字段 | 使用场景 |
> |---|---|---|
> | **列表模式** | `brief_id`, `title`, `status`, `priority`, `created_by`, `assigned_to`, `updated_at` | 2.2 列表查询 |
> | **详情模式** | 列表模式 + `content`, `attachments`, `current_version` | 2.3 获取单个 Brief |
> | **版本模式** | 详情模式 + `version`, `is_current` | 2.3 `?version=` 参数 |
>
> 除用户相关接口外，其他接口的用户对象只返回 `id` 和 `name`，需要完整信息请调 `GET /users/:user_id`（7.2）。

### 2.1 创建 Brief

`POST /briefs`

```json
// Request
{
  "title": "优化首页加载速度",
  "content": "当前首页首屏加载时间 3.2s，目标降到 1.5s 以内...",
  "attachments": [
    { "name": "性能报告.png", "url": "/api/v1/files/...", "type": "image" }  // 先调 8.1 上传拿 url
  ],
  "priority": "p1",
  "estimated_man_days": 3,
  "parent_id": null
}

// Response 201
{
  "brief": {
    "brief_id": "guid",
    "root_id": "guid",
    "parent_id": null,
    "current_version": 1,
    "status": "draft",
    "title": "优化首页加载速度",
    "priority": "p1",
    "estimated_man_days": 3,
    "created_by": { "id": "guid", "name": "张三" },
    "assigned_to": null,
    "created_at": "2026-06-20T22:00:00Z",
    "updated_at": "2026-06-20T22:00:00Z"
  }
}
```

### 2.2 列表查询 Brief

`GET /briefs?status=draft&role=created&page_cursor=abc&page_size=20`

查询参数：
- `status` — 过滤状态
- `role` — `created`（我创建的）/ `assigned`（分配给我的）/ `all`（全部可读）
- `root_id` — 过滤某棵树
- `page_cursor` — 分页游标
- `page_size` — 每页数量，默认 20

```
Response 200
{
  "briefs": [
    {
      "brief_id": "guid",
      "title": "优化首页加载速度",
      "status": "draft",
      "priority": "p1",
      "created_by": { "id": "guid", "name": "张三" },
      "assigned_to": null,
      "updated_at": "2026-06-20T22:00:00Z"
    }
  ],
  "next_cursor": "next_page_token_or_null"
}
```

> 列表模式：不包含 `content` 和 `attachments`，减少响应大小

### 2.3 获取单个 Brief（含版本内容）

`GET /briefs/:brief_id?version=<version_number>`

查询参数：
- `version` — 可选，指定版本号；不传则返回当前版本（`current_version`）

```
Response 200
{
  "brief": {
    "brief_id": "guid",
    "root_id": "guid",
    "parent_id": null,
    "version": 1,              // 本次返回的版本号
    "is_current": true,         // 是否为当前版本
    "status": "draft",
    "title": "...",
    "content": "...",            // 该版本的内容
    "attachments": [             // 该版本的附件
      { "name": "性能报告.png", "url": "/api/v1/files/...", "type": "image" }
    ],
    "priority": "p1",
    "estimated_man_days": 3,
    "created_by": { "id": "guid", "name": "张三" },
    "assigned_to": null,
    "created_at": "2026-06-20T22:00:00Z",
    "updated_at": "2026-06-20T22:00:00Z"
  }
}
```

> 权限：created_by 或只读权限用户可访问  
> 通过 `?version=` 参数可获取历史版本，无需单独调用版本详情

### 2.4 更新 Brief（仅 draft 状态）

`PATCH /briefs/:brief_id`

```json
// Request（只传需要更新的字段）
{
  "title": "新标题",
  "content": "更新后的内容",
  "priority": "p0"
}

// Response 200
{
  "brief": {
    "brief_id": "guid",
    "root_id": "guid",
    "parent_id": null,
    "current_version": 2,
    "status": "draft",
    "title": "新标题",
    "priority": "p0",
    "estimated_man_days": 3,
    "created_by": { "id": "guid", "name": "张三" },
    "assigned_to": null,
    "created_at": "2026-06-20T22:00:00Z",
    "updated_at": "2026-06-20T22:10:00Z"
  },
  "version": 2
}
```

> 权限：只有 created_by 可更新，且 status = draft

### 2.5 提交审查（draft → reviewed）

`POST /briefs/:brief_id/submit`

```
Request body: 空或 { "note": "请审查" }

Response 200
{
  "brief": { "status": "reviewed", ... },
  "message": "Brief 已提交，等待审查"
}
```

> MVP 阶段：跳过 Arbiter，直接转 reviewed  
> 后续：调用 Arbiter LLM，通过才转 reviewed

### 2.6 发送 Brief（reviewed → sent）

`POST /briefs/:brief_id/send`

通过 `is_temporary_user` 参数区分两种发送方式：

**方式一：发送给已注册用户（`is_temporary_user=false` 或缺省）**

```json
// Request
{
  "is_temporary_user": false,
  "assigned_to": "downstream_user_guid",
  "note": "请帮忙评估工时"
}

// Response 200
{
  "brief": { "status": "sent", "assigned_to": "downstream_user_guid", ... },
  "transfer": { "sent_at": "2026-06-20T22:30:00Z", "accepted_at": null, "rejected_at": null }
}
```

**方式二：发送给外部用户（`is_temporary_user=true`，详见 05-invite-link-design.md）**

```json
// Request
{
  "is_temporary_user": true,
  "recipient_email": "lisi@example.com",     // 可选，email 和 phone 至多填一个
  "recipient_phone": null,                   // 可选
  "recipient_name": "李四",                  // 可选，用于显示
  "note": "请帮忙评估工时",
  "accept_deadline_days": 7,                 // 接受截止天数，默认 7
  "complete_deadline_days": 30               // 完成截止天数，默认 30
}

// Response 200 — 新建临时用户
{
  "brief": { "status": "sent", "assigned_to": "临时用户UUID", ... },
  "transfer": { "to_user": "临时用户UUID", "sent_at": "...", ... },
  "invite": {
    "invite_url": "/invites/{token}",
    "accept_deadline": "2026-06-27T22:30:00Z",
    "complete_deadline": "2026-07-20T22:30:00Z"
  }
}

// Response 200 — email/phone 命中已注册用户，自动转方式一
{
  "brief": { "status": "sent", "assigned_to": "注册用户UUID", ... },
  "transfer": { "to_user": "注册用户UUID", "sent_at": "...", ... }
  // 无 invite 字段
}
```

> 校验规则：
> - `is_temporary_user=false`：必须有 `assigned_to`
> - `is_temporary_user=true`：`recipient_email` 和 `recipient_phone` 至多填一个（可都不填）；无 `assigned_to`
> - 方式二查找逻辑（详见 05-invite-link-design.md 第 6.1 节）：
>   - email/phone 命中 registered/oauth 用户 → 自动转方式一
>   - email/phone 命中 temporary 用户且 `final_user_id` 为空 → 复用该 user_id，新建 invite
>   - email/phone 命中 temporary 用户且 `final_user_id` 不为空 → 用 `final_user_id` 走方式一
>   - 未命中或未填 email/phone → 新建临时用户 + invite
> - 权限：只有 created_by 可发送

### 2.7 接受 Brief（sent → accepted）

`POST /briefs/:brief_id/accept`

```
Request body: 空或 { "note": "已理解，开始排期" }

Response 200
{
  "brief": { "status": "accepted", ... },
  "transfer": { "accepted_at": "2026-06-20T22:35:00Z" }
}
```

> 权限：只有 assigned_to 可接受

### 2.8 拒绝 Brief（sent → draft）

`POST /briefs/:brief_id/reject`

```json
// Request
{ "reason": "验收标准不清晰，请补充具体性能指标" }

// Response 200
{
  "brief": { "status": "draft", ... },
  "transfer": { "rejected_at": "2026-06-20T22:40:00Z", "rejection_reason": "..." }
}
```

> 权限：只有 assigned_to 可拒绝

### 2.9 取消 Brief

`POST /briefs/:brief_id/cancel`

```
Response 200
{ "brief": { "status": "cancelled", ... } }
```

> 权限：只有 created_by 可取消，且 status 不是 done

### 2.10 完成 Brief（accepted → done）

`POST /briefs/:brief_id/complete`

```
Response 200
{ "brief": { "status": "done", ... } }
```

> 简化版：assigned_to 可以直接标记完成  
> 完整版（后续）：需要提交 completion feedback + Arbiter 审查通过

---

## 3. Brief 版本（`/briefs/:brief_id/versions`）

### 3.1 列出所有版本

`GET /briefs/:brief_id/versions`

```
Response 200
{
  "versions": [
    {
      "version": 1,
      "title": "优化首页加载速度",
      "modified_by": { "id": "guid", "name": "张三" },
      "modified_at": "2026-06-20T22:00:00Z",
      "change_summary": "初始创建",
      "is_upstream_changed": false,
      "revision_reason": "initial"
    }
  ]
}
```

> 获取某版本的完整内容请调用 `GET /briefs/:brief_id?version=<version_number>`（2.3）

---

## 4. 流转历史（`/briefs/:brief_id/transfers`）

### 4.1 列出流转历史

`GET /briefs/:brief_id/transfers`

```
Response 200
{
  "transfers": [
    {
      "id": "guid",
      "brief_version": 1,
      "from_user": { "id": "guid", "name": "张三" },
      "to_user": { "id": "guid", "name": "李四" },
      "sent_at": "2026-06-20T22:30:00Z",
      "accepted_at": "2026-06-20T22:35:00Z",
      "rejected_at": null,
      "rejection_reason": null
    }
  ]
}
```

---

## 5. Feedback（`/briefs/:brief_id/feedbacks`）

### 5.1 创建 Feedback

`POST /briefs/:brief_id/feedbacks`

```json
// Request
{
  "type": "progress",
  "content": "已完成接口层优化，预计明天完成前端集成",
  "attachments": []
}

// Response 201
{
  "feedback": {
    "id": "guid",
    "brief_id": "guid",
    "brief_version": 1,
    "type": "progress",
    "content": "...",
    "from_user": { "id": "guid", "name": "李四" },
    "created_at": "2026-06-20T23:00:00Z",
    "confirmed_at": null
  }
}
```

> 权限：brief 的 assigned_to 或 created_by 可创建

### 5.2 列出 Feedback

`GET /briefs/:brief_id/feedbacks?type=progress`

```
Response 200
{
  "feedbacks": [
    {
      "id": "guid",
      "type": "progress",
      "from_user": { "id": "guid", "name": "李四" },
      "created_at": "2026-06-20T23:00:00Z"
    }
  ]
}
```

> 列表模式：不包含 `content` 和 `attachments`，减少响应大小  
> 需要完整信息请调用 `GET /feedbacks/:feedback_id`（5.3）

### 5.3 获取单个 Feedback（详情模式）

`GET /feedbacks/:feedback_id`

```
Response 200
{
  "feedback": {
    "id": "guid",
    "brief_id": "guid",
    "brief_version": 1,
    "type": "progress",
    "content": "...",              // 完整内容
    "attachments": [               // 完整附件
      { "name": "截图.png", "url": "/api/v1/files/...", "type": "image" }
    ],
    "from_user": { "id": "guid", "name": "李四" },
    "created_at": "2026-06-20T23:00:00Z",
    "confirmed_at": null
  }
}
```

---

## 6. Brief Chain（`/chains`）

### 6.1 创建 Chain（即创建根 Brief 时自动创建）

> MVP 简化：创建 root brief 时自动创建 chain，不需要单独创建

### 6.2 列出我的 Chains

`GET /chains`

```
Response 200
{
  "chains": [
    {
      "chain_id": "guid",
      "title": "Q3 性能优化项目",
      "root_brief_id": "guid",
      "brief_count": 5,
      "created_at": "2026-06-20T22:00:00Z"
    }
  ]
}
```

### 6.3 获取 Chain 详情（含树形结构）

`GET /chains/:chain_id`

```
Response 200
{
  "chain": {
    "chain_id": "guid",
    "title": "Q3 性能优化项目",
    "root_brief": { 
      "brief_id": "guid", 
      "title": "...",
      "status": "accepted",
      "priority": "p1",
      "created_by": { "id": "guid", "name": "张三" },
      "assigned_to": { "id": "guid", "name": "李四" },
      "updated_at": "2026-06-20T22:00:00Z"
    },
    "tree": {
      "brief_id": "root_guid",
      "title": "...",
      "status": "accepted",
      "children": [
        {
          "brief_id": "child_guid",
          "title": "...",
          "status": "done",
          "children": []
        }
      ]
    }
  }
}
```

> `root_brief` 使用详情模式（包含 `status`, `priority`, `created_by`, `assigned_to`）  
> `tree` 使用列表模式（只包含 `brief_id`, `title`, `status`, `children`）

---

## 7. 用户（`/users`）

### 7.1 获取用户列表

`GET /users?role=created&status=draft`

```
Response 200
{
  "users": [
    { 
      "id": "guid", 
      "name": "张三", 
      "email": "***@example.com",  // 非本人/非 admin 显示脱敏
      "phone": "138****0000",     // 非本人/非 admin 显示脱敏
      "avatar_url": null 
    }
  ]
}
```

> 敏感信息（email/phone）脱敏规则：
> - 本人：显示完整 `email` 和 `phone`
> - 其他用户：显示脱敏版本（email 显示 `***@example.com`，phone 显示 `138****0000`）
> - Admin：显示完整信息

### 7.2 获取单个用户

`GET /users/:user_id`

```
Response 200
{ 
  "user": { 
    "id": "guid", 
    "name": "...", 
    "email": "...",    // 本人/Admin 显示完整，其他显示脱敏
    "phone": "...",    // 本人/Admin 显示完整，其他显示脱敏
    "avatar_url": null 
  } 
}
```

> 敏感信息（email/phone）脱敏规则同 7.1

---

## 8. 文件上传（`/files`）

### 上传流程

1. 客户端调 `POST /files/upload` 上传文件，拿到 `url`
2. 创建/更新 Brief 或 Feedback 时，将 `url` 填入 `attachments` 数组

### 8.1 上传文件

`POST /files/upload`

```json
// Request（multipart/form-data）
// field: file
// field: type  // "brief" | "feedback"

// Response 201
{
  "url": "/api/v1/files/abc123.png",
  "name": "性能报告.png",
  "type": "image",
  "size": 102400
}
```

> 服务端将文件存入本地 `uploads/` 目录（MVP）  
> 未来切换到 S3 时，返回 `https://s3.xxx/bucket/abc123.png`

### 8.2 获取文件

`GET /files/:file_id`

> 服务端返回文件流（通过 Storage Adapter）

---

## 附录：状态转移图

```
[draft] ──submit──→ [reviewed] ──send──→ [sent]
                                           ↓ accept    ↓ reject
                                      [accepted]    [draft]
                                           ↓ complete
                                        [done]

[draft/sent/accepted] ──cancel──→ [cancelled]
[accepted] ──blocked feedback──→ [blocked] ──resolve──→ [accepted]
```

---

## 附录：MVP 不做的功能

- ❌ Arbiter LLM 自动审查（人工替代）
- ❌ 内部 Kanban / 工作状态管理
- ❌ 跨系统互操作（bc:// 协议）
- ❌ 可配置工作流模板
- ❌ 微信/三方登录（先邮箱/手机注册）
- ❌ 细粒度权限（先 created_by 全权限）
- ❌ 手机号验证码登录（MVP 只支持密码登录）
- ❌ 邀请链接验证码（MVP 只做信任场景，详见 05-invite-link-design.md）
