# BriefChain REST API 设计文档

> 版本：MVP v0.5
> 最后更新：2026-06-28
> 基础路径：`/api/v1`

---

## 设计原则

- **JWT 认证**：登录后所有请求带 `Authorization: Bearer <token>`
- **user_id 解析**：所有 Brief / Transfer / Feedback 读写操作，后端从 JWT 解析 `user_id`，校验操作人与 brief 角色关系（upstream = created_by, downstream = assigned_to）。前端不传 user_id，后端强制从 JWT 提取
- **权限模型（MVP）**：`created_by`（upstream）有全部读写权限；`assigned_to`（downstream）有下游操作权限；其他人只读
- **状态码**：标准 HTTP 状态码，错误返回统一格式
- **分页**：游标分页（cursor-based），避免 offset 性能问题
- **API 聚类**：端点按状态阶段分为 4 组，每组用路径表达阶段 + `action` 参数表达动作，结构完全一致：
  - `POST /briefs/:id/editing?action={patch | submit-review}` — 只操作 version，不碰 brief 状态
  - `POST /briefs/:id/transfer?action={send | accept | reject}` — send 是邀约阶段桥梁（version↔state）
  - `POST /briefs/:id/upstream-actions?action={cancel | suspend | resume | approve | reject_submit | update}` — update 同时操作 version + brief，其余只操作 brief 状态
  - `POST /briefs/:id/downstream-actions?action={process | submit | open | delegate | block}` — 只操作 brief 状态
- **version 与 state 解耦**：patch / submit-review 只操作 version.status，不检查 upstream_state；accept / cancel / suspend 等只操作 brief 状态，不碰 version。send 是邀约阶段的桥梁（editing/sent → transfer_history），update 是合约期间的版本更新（in_process → feedbacks，两者对 version 操作相同但记录位置不同）
- **冗余存储人名**：briefs / feedbacks / transfers / chains 表冗余存储用户名字（name 快照），合约语义上名字是操作时的签名，列表查询不需要 JOIN users 表

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
> | **列表模式** | `brief_id`, `title`, `upstream_state`, `downstream_state`, `priority`, `created_by_id`, `created_by_name`, `assigned_to_id`, `assigned_to_name`, `status_changed_by_id`, `status_changed_by_name`, `status_changed_at`, `updated_at` | 2.2 列表查询 |
> | **详情模式** | 列表模式 + `content`, `attachments`, `current_version`, `unfinalized_version` | 2.3 获取单个 Brief |
> | **版本模式** | 详情模式 + `version`, `is_current` | 2.3 `?version=` 参数 |
>
> **人名冗余存储**：所有涉及用户的字段（created_by / assigned_to / from_user / to_user）都冗余存储 name（快照），响应中拆成 `id` + `name` 两个平级字段，不嵌套成对象。需要用户完整信息请调 `GET /users/:user_id`（11.2）。

### 2.1 创建 Brief

`POST /briefs`

```json
// Request
{
  "title": "优化首页加载速度",
  "content": "当前首页首屏加载时间 3.2s，目标降到 1.5s 以内...",
  "attachments": [
    { "name": "性能报告.png", "url": "/api/v1/files/...", "type": "image" }  // 先调 12.1 上传拿 url
  ],
  "priority": "p1",
  "estimated_man_days": 3,
  "expected_completion_at": "2026-07-05T00:00:00Z",  // 可选，预期完成时间
  "parent_id": null
}

// Response 201
{
  "brief": {
    "brief_id": "guid",
    "root_id": "guid",
    "parent_id": null,
    "current_version": null,        // 初始为 null，第一次 sent 后变为 1
    "upstream_state": "editing",    // 新建 brief = upstream 编写中
    "downstream_state": null,       // 还没 downstream
    "title": "优化首页加载速度",
    "priority": "p1",
    "estimated_man_days": 3,
    "expected_completion_at": "2026-07-05T00:00:00Z",
    "created_by_id": "guid",
    "created_by_name": "张三",
    "assigned_to_id": null,
    "assigned_to_name": null,
    "status_changed_by_id": "guid",
    "status_changed_by_name": "张三",
    "status_changed_at": "2026-06-20T22:00:00Z",
    "created_at": "2026-06-20T22:00:00Z",
    "updated_at": "2026-06-20T22:00:00Z"
  }
}
```

> user_id 从 JWT 解析，设为 `created_by`；从 users 表读取 name 写入 `created_by_name`（冗余快照）

### 2.2 列表查询 Brief

`GET /briefs?upstream_state=editing&role=created&page_cursor=abc&page_size=20`

查询参数：
- `upstream_state` — 过滤 upstream 状态，多选（前端可以分成 unassigned / assigned / ended / all 几种）
- `downstream_state` — 过滤 downstream 状态，多选（前端直接使用 opened / delegated / blocked / submitted / ended 几种） 
- `role` — `created`（我创建的）/ `assigned`（分配给我的）
- `root_id` — 过滤某棵树
- `page_cursor` — 分页游标
- `page_size` — 每页数量，默认 20

```json
Response 200
{
  "briefs": [
    {
      "brief_id": "guid",
      "title": "优化首页加载速度",
      "upstream_state": "editing",
      "downstream_state": null,
      "priority": "p1",
      "created_by_id": "guid",
      "created_by_name": "张三",
      "assigned_to_id": null,
      "assigned_to_name": null,
      "updated_at": "2026-06-20T22:00:00Z"
    }
  ],
  "next_cursor": "next_page_token_or_null"
}
```

> 列表模式：不包含 `content` 和 `attachments`，减少响应大小
> 人名字段从冗余存储直接读取，不需要 JOIN users 表

### 2.3 获取单个 Brief（含版本内容）

`GET /briefs/:brief_id?version=<version_number>`

查询参数：
- `version` — 可选，指定版本号；不传则返回当前版本（`current_version`）

```json
Response 200
{
  "brief": {
    "brief_id": "guid",
    "root_id": "guid",
    "parent_id": null,
    "version": 1,              // 本次返回的版本号
    "is_current": true,         // 是否为当前版本
    "unfinalized_version": null,      // 当前可编辑的 draft 版本号（null = 无 draft）；前端编辑时自动 load 此版本
    "upstream_state": "editing",
    "downstream_state": null,
    "title": "...",
    "content": "...",            // 该版本的内容
    "attachments": [             // 该版本的附件
      { "name": "性能报告.png", "url": "/api/v1/files/...", "type": "image" }
    ],
    "priority": "p1",
    "estimated_man_days": 3,
    "expected_completion_at": "2026-07-05T00:00:00Z",
    "created_by_id": "guid",
    "created_by_name": "张三",
    "assigned_to_id": null,
    "assigned_to_name": null,
    "created_at": "2026-06-20T22:00:00Z",
    "updated_at": "2026-06-20T22:00:00Z"
  }
}
```

> user_id 从 JWT 解析，有读权限即可访问（created_by 全权限，assigned_to 下游权限，其他人只读）
> 通过 `?version=` 参数可获取历史版本，无需单独调用版本详情
> **unfinalized_version 逻辑：**
> - current_version = null → 返回最新 draft 版本内容，unfinalized_version = 该版本号
> - current_version = N，存在 N+1 draft → 返回 vN 内容（final），unfinalized_version = N+1
> - current_version = N，无更高版本 → 返回 vN 内容，unfinalized_version = null
> - downstream 只看 current_version 内容（看不到 draft）；upstream 编辑时自动 load unfinalized_version

---

## 3. Editing 端点（`/briefs/:brief_id/editing`）

> 编辑端点只操作 version（内容和 status），不改变 upstream_state / downstream_state。
> patch 和 submit-review 只看 version.status，不检查 upstream_state（只要 upstream_state 不是 cancelled/done 终态即可）。
> 统一入口，通过 `action` 参数指定具体动作。

`POST /briefs/:brief_id/editing`

### 3.1 patch（更新内容）

```json
// Request
{
  "action": "patch",
  "title": "新标题",                    // 可选，只传需要更新的字段
  "content": "更新后的内容",             // 可选
  "priority": "p0",                     // 可选
  "expected_completion_at": "2026-07-10T00:00:00Z"  // 可选，调整预期完成时间
}

// Response 200
{
  "brief": {
    "brief_id": "guid",
    "upstream_state": "editing",    // 不变
    "downstream_state": null,       // 不变
    "current_version": null,        // 不变（patch 不碰 current_version）
    "unfinalized_version": 1,             // 当前可编辑的 draft 版本号
    "title": "新标题",              // draft 版本的标题（非 briefs.title）
    "priority": "p0",
    "estimated_man_days": 3,
    "created_by_id": "guid",
    "created_by_name": "张三",
    "assigned_to_id": null,
    "assigned_to_name": null,
    "status_changed_by_id": "guid",
    "status_changed_by_name": "张三",
    "status_changed_at": "2026-06-20T22:00:00Z",
    "created_at": "2026-06-20T22:00:00Z",
    "updated_at": "2026-06-20T22:10:00Z"
  },
  "version": 1,
  "version_status": "draft"         // patch 后 version.status
}
```

> user_id 从 JWT 解析，校验 = created_by，且 upstream_state 不是 cancelled/done
> **版本行为（只看 version.status，不看 upstream_state）：**
> - version.status = draft → 原地修改，version 不变
> - version.status = reviewed → 原地修改，status 重置为 draft
> - version.status = final → 不能修改，自动创建新版本 v(n+1) draft；如已存在 v(n+1) 则报错
> - briefs.current_version / title / priority 不变（只有 send 才更新这些字段）

### 3.2 submit-review（提交审查，版本 draft → reviewed）

```json
// Request
{
  "action": "submit-review",
  "note": "请审查"   // 可选
}

// Response 200
{
  "brief": {
    "upstream_state": "editing",    // 不变，editing 统一表达编写阶段
    "downstream_state": null,
    "status_changed_by_id": "guid",
    "status_changed_by_name": "张三",
    "status_changed_at": "2026-06-20T22:00:00Z",
    ...                   // 其余字段同 2.1
  },
  "version": {
    "version": 1,
    "status": "reviewed",           // 版本状态变 reviewed
    "arbiter_review_id": "guid"     // 审查记录 ID
  },
  "message": "Brief 已提交，等待审查"
}
```

> user_id 从 JWT 解析，校验 = created_by，且 upstream_state 不是 cancelled/done
> 版本状态：当前 draft 版本 → reviewed（arbiter_review_id 填入 brief_versions）
> upstream_state 不变（patch / submit-review 只操作 version，不碰 brief 状态）
> MVP 阶段：跳过 Arbiter，直接转 reviewed（arbiter_review_id 记录 force_skipped）
> 后续：调用 Arbiter LLM，通过才转 reviewed

---

## 4. Transfer 端点（邀约阶段）

> Transfer 端点处理 brief 从 upstream 到 downstream 的初始交接。记录在 brief_transfer_history。
> 统一入口，通过 `action` 参数指定具体动作。

`POST /briefs/:brief_id/transfer`

### 4.1 send（邀约：version→final，brief 进入邀约阶段）

send 处理两种邀约场景，都记录在 brief_transfer_history：

| brief 状态 | send 效果 | transfer_history |
|-----------|----------|-----------------|
| editing | 首次发送：current_version null→N，brief editing→sent | ✅ 新记录 |
| sent | 替换邀约：current_version 更新，brief 状态不变 | ✅ 新记录 |

> final 状态下也允许 send：upstream 发出邀约后、downstream 响应前，upstream 可以修改并重新发送，代价更小（还没建立合约）。

**参数随场景不同：**
- editing（首次发送）→ assigned_to 为空，需选择接收方（`assigned_to` 或 `is_temporary_user`）
- sent（替换邀约）→ assigned_to 已存在，无需重新选择（如需更换接收方仍可传参）

**方式一：发送给已注册用户（`is_temporary_user=false` 或缺省）**

```json
// Request
{
  "action": "send",
  "is_temporary_user": false,
  "assigned_to": "downstream_user_guid",
  "note": "请帮忙评估工时"
}

// Response 200 — 方式一
{
  "brief": { "upstream_state": "sent", "downstream_state": null, "assigned_to_id": "downstream_user_guid", "assigned_to_name": "李四", "status_changed_by_id": "guid", "status_changed_by_name": "张三", "status_changed_at": "...", ... },
  "transfer": { "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", "sent_at": "2026-06-20T22:30:00Z", "accepted_at": null, "rejected_at": null }
}
```

**方式二：发送给外部用户（`is_temporary_user=true`，详见 05-invite-link-design.md）**

```json
// Request
{
  "action": "send",
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
  "brief": { "upstream_state": "sent", "downstream_state": null, "assigned_to_id": "临时用户UUID", "assigned_to_name": "李四", ... },
  "transfer": { "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "临时用户UUID", "to_user_name": "李四", "sent_at": "...", ... },
  "invite": {
    "invite_url": "/invites/{token}",
    "accept_deadline": "2026-06-27T22:30:00Z",
    "complete_deadline": "2026-07-20T22:30:00Z"
  }
}

// Response 200 — email/phone 命中已注册用户，自动转方式一
{
  "brief": { "upstream_state": "sent", "downstream_state": null, "assigned_to_id": "注册用户UUID", "assigned_to_name": "李四", ... },
  "transfer": { "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "注册用户UUID", "to_user_name": "李四", "sent_at": "...", ... }
  // 无 invite 字段
}
```

> 校验规则：
> - user_id 从 JWT 解析，校验 = created_by，且 upstream_state = editing 或 sent
> - 版本必须为 reviewed（或 MVP: force_skipped）
> - `is_temporary_user=false`：必须有 `assigned_to`
> - `is_temporary_user=true`：`recipient_email` 和 `recipient_phone` 至多填一个（可都不填）；无 `assigned_to`
> - 方式二查找逻辑（详见 05-invite-link-design.md 第 6.1 节）
> **版本同步：** sent 时当前版本 status → final，同步更新 briefs.current_version / title / priority / expected_completion_at
> **brief 状态变更：**
> - 从 editing 发送：upstream_state editing → sent
> - 从 sent 发送：upstream_state 不变（替换邀约），transfer_history 新增记录
> transfer_history 记录 from_user_name / to_user_name（冗余快照）
> transfer_history.arbiter_review_id 从 brief_versions.arbiter_review_id 读取
> **合约期间推送新版本（in_process 状态），用 upstream-actions 的 update（5.5）**

### 4.2 accept（邀约：sent → in_process）

```json
// Request
{
  "action": "accept",
  "note": "已理解，开始排期"   // 可选
}

// Response 200
{
  "brief": { "upstream_state": "in_process", "downstream_state": "opened", "status_changed_by_id": "guid", "status_changed_by_name": "李四", "status_changed_at": "2026-06-20T22:35:00Z", ... },
  "transfer": { "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", "accepted_at": "2026-06-20T22:35:00Z" }
}
```

> user_id 从 JWT 解析，校验 = assigned_to
> upstream_state: sent → in_process；downstream_state: null → opened

### 4.3 reject（邀约：sent → editing）

```json
// Request
{
  "action": "reject",
  "reason": "验收标准不清晰，请补充具体性能指标"   // 必填
}

// Response 200
{
  "brief": { "upstream_state": "editing", "downstream_state": null, "assigned_to_id": null, "assigned_to_name": null, "status_changed_by_id": "guid", "status_changed_by_name": "李四", "status_changed_at": "2026-06-20T22:40:00Z", ... },
  "transfer": { "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", "rejected_at": "2026-06-20T22:40:00Z", "rejection_reason": "验收标准不清晰..." }
}
```

> user_id 从 JWT 解析，校验 = assigned_to
> upstream_state: sent → editing；downstream_state: null → null；assigned_to_id/name → null（清除分配）
> version.status = reviewed
> 不创建 feedback（邀约阶段的拒绝走 transfer_history，不是合约期通知）

---

## 5. Upstream-action 端点（`/briefs/:brief_id/upstream-actions`）

> upstream 在 brief 被接单后（upstream_state = in_process / suspended）的操作。
> 统一入口，通过 `action` 参数指定具体动作。
> update 推送新版本（合约期间），与 send（邀约阶段）对 version 的操作相同，但记录在 feedbacks 而非 transfer_history。

`POST /briefs/:brief_id/upstream-actions`

### 5.1 cancel（取消合约）

```json
// Request
{
  "action": "cancel",
  "content": "项目暂停"           // 必填，取消原因
}

// Response 200
{
  "brief": { "upstream_state": "cancelled", "downstream_state": "opened", "status_changed_by_id": "guid", "status_changed_by_name": "张三", "status_changed_at": "...", ... },
  "feedback": { "id": "guid", "is_to_down": true, "type": "cancel", "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", ... }
}
```

> user_id 从 JWT 解析，校验 = created_by，且 upstream_state 不是 done/cancelled
> upstream_state → cancelled，downstream_state 保留（用于历史审计）
> 创建一条 feedback (type=cancel, is_to_down=true)

### 5.2 suspend（暂停） / resume（恢复）

```json
// Request — suspend
{
  "action": "suspend",
  "content": "项目优先级调整，暂停执行"   // 必填，暂停原因
}

// Response 200 — suspend
{
  "brief": { "upstream_state": "suspended", "downstream_state": "opened", "status_changed_by_id": "guid", "status_changed_by_name": "张三", "status_changed_at": "...", ... },
  "feedback": { "id": "guid", "is_to_down": true, "type": "suspend", "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", ... }
}

// Request — resume
{
  "action": "resume",
  "content": "优先级恢复，继续执行"   // 必填，恢复原因
}

// Response 200 — resume
{
  "brief": { "upstream_state": "in_process", "downstream_state": "opened", "status_changed_by_id": "guid", "status_changed_by_name": "张三", "status_changed_at": "...", ... },
  "feedback": { "id": "guid", "is_to_down": true, "type": "resume", "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", ... }
}
```

> suspend: user_id 从 JWT 解析，校验 = created_by，upstream_state 必须为 in_process / sent
> upstream_state → suspended，downstream_state 保留不动
> resume: user_id 从 JWT 解析，校验 = created_by，upstream_state 必须为 suspended
> upstream_state → in_process，downstream_state 原样恢复
> 不需要 previous_status 字段

### 5.3 approve（验收通过）

> downstream_state 保留原状态（便于审计），不是 → null。

```json
// Request
{
  "action": "approve",
  "content": "验收通过，首屏加载 1.2s 达标"   // 必填，验收说明
}

// Response 200
{
  "brief": { "upstream_state": "done", "downstream_state": "submitted", "status_changed_by_id": "guid", "status_changed_by_name": "张三", "status_changed_at": "...", ... },
  "feedback": { "id": "guid", "is_to_down": true, "type": "approve", "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", ... }
}
```

> user_id 从 JWT 解析，校验 = created_by，且 upstream_state = in_process + downstream_state = submitted
> upstream_state → done（终态），downstream_state 保留原值（submitted）便于审计

### 5.4 reject_submit（打回提交）

```json
// Request
{
  "action": "reject_submit",
  "content": "验收标准未达标，首屏加载时间仍为 2.1s，目标 1.5s 以内"   // 必填，打回原因
}

// Response 200
{
  "brief": { "upstream_state": "in_process", "downstream_state": "opened", "status_changed_by_id": "guid", "status_changed_by_name": "张三", "status_changed_at": "...", ... },
  "feedback": { "id": "guid", "is_to_down": true, "type": "reject_submit", "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", ... }
}
```

> user_id 从 JWT 解析，校验 = created_by，且 downstream_state = submitted
> upstream_state 不变（in_process），downstream_state → opened（强制重做）
> brief 内容不变，downstream 需继续修改后重新提交
> downstream 不能 block 此动作（打回是强制合约动作）

### 5.5 update（推送新版本 — 合约期间更新）

upstream 在合约期间（in_process）推送新版本。与 send 对 version 的操作完全相同（version→final, current_version 更新），但记录在 feedbacks 而非 transfer_history。

```json
// Request
{
  "action": "update",
  "content": "新增需求：需要支持暗黑模式",   // 必填，变更说明
  "title": "优化首页加载速度 + 暗黑模式支持",
  "priority": "p1",
  // ... 其他 brief_versions 字段
  "revision_reason": "新增暗黑模式需求"
}

// Response 200
{
  "brief": { "upstream_state": "in_process", "downstream_state": "opened", "current_version": 2, "status_changed_by_id": "guid", "status_changed_by_name": "张三", "status_changed_at": "...", "title": "优化首页加载速度 + 暗黑模式支持", "priority": "p1", ... },
  "feedback": { "id": "guid", "is_to_down": true, "type": "update", "from_user_id": "guid", "from_user_name": "张三", "to_user_id": "guid", "to_user_name": "李四", ... }
}
```

> user_id 从 JWT 解析，校验 = created_by，且 upstream_state = in_process
> **与 send 的区别：** send 用于邀约阶段（editing/sent → transfer_history），update 用于合约期间（in_process → feedbacks）。两者对 version 的操作相同（version→final, current_version 更新），但记录位置不同——send 是初始交接，update 是合约期通知
> **版本流转（MVP: auto-pass）：**
> 1. 创建新版本 v(n+1): draft
> 2. 自动提交 Arbiter 审查 → v(n+1): reviewed（arbiter_review_id 填入，MVP: force_skipped）
> 3. 自动 final → v(n+1): final（v(n) 仍为 final，briefs.current_version 增大自动作废）
> 4. briefs.current_version = n+1，briefs.title/priority 同步
> 5. downstream_state → opened（强制重开，需求变了下游必须基于新版本重新执行）
> 6. 创建 feedback (type=update, is_to_down=true)
> **downstream 可以 block 来表达"不接受更新"**，但 block 只是通知，不阻止 update 的状态变更

---

## 6. Downstream-action 端点（`/briefs/:brief_id/downstream-actions`）

> downstream 在 brief 被接单后（upstream_state = in_process）的操作。
> 统一入口，通过 `action` 参数指定具体动作。
> downstream 自由控制 downstream_state（可从任意下游状态切换）。
> 所有 action 共用相同的 Request/Response 结构，差异仅为 `action` 值和 `content` 是否必填。

`POST /briefs/:brief_id/downstream-actions`

**通用 Request：**
```json
{
  "action": "<action>",
  "content": "...",        // 按类型必填或可空（见下方表格）
  "attachments": []        // 可选
}
```

**通用 Response：**
```json
{
  "brief": { "upstream_state": "in_process", "downstream_state": "<新状态>", ... },
  "feedback": { "id": "guid", "is_to_down": false, "type": "<action>", ... }
}
```

**校验规则（通用）：**
- user_id 从 JWT 解析，校验 = assigned_to，upstream_state = in_process
- 不改变 upstream_state，只改变 downstream_state

**action 差异表：**

| action | downstream_state 变更 | content | 说明 |
|--------|---------------------:|--------:|------|
| process | 不变（进度更新） | 可空 | 创建 feedback (type=progress) |
| submit | → submitted | 必填 | 创建 feedback (type=submit)，需 Arbiter 审查（MVP 跳过） |
| open | → opened | 必填 | 创建 feedback (type=open)，常见：从 submitted 撤回 |
| delegate | → delegated | **可空** | 创建 feedback (type=delegate)，通知 upstream 拆解进展 |
| block | → blocked | 必填 | 创建 feedback (type=block)，通知 upstream 需介入 |

> open 可从 submitted/delegated/blocked 发起；delegate/block 可从 opened/submitted 发起。downstream 自由切换。
> process 是唯一不改变 downstream_state 的 action（纯进度更新）。

---

## 7. Brief 版本（`/briefs/:brief_id/versions`）

### 7.1 列出所有版本

`GET /briefs/:brief_id/versions`

```json
Response 200
{
  "versions": [
    {
      "version": 1,
      "status": "final",
      "title": "优化首页加载速度",
      "modified_by_id": "guid",
      "modified_by_name": "张三",
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

## 8. 流转历史（`/briefs/:brief_id/transfers`）

### 8.1 列出流转历史

`GET /briefs/:brief_id/transfers`

```json
Response 200
{
  "transfers": [
    {
      "id": "guid",
      "brief_version": 1,
      "from_user_id": "guid",
      "from_user_name": "张三",
      "to_user_id": "guid",
      "to_user_name": "李四",
      "sent_at": "2026-06-20T22:30:00Z",
      "accepted_at": "2026-06-20T22:35:00Z",
      "rejected_at": null,
      "rejection_reason": null
    }
  ]
}
```

> 人名字段从冗余存储直接读取，不需要 JOIN users 表

---

## 9. Feedback（`/briefs/:brief_id/feedbacks`）

> feedbacks 是 brief 状态变更的记录，也是上下游之间的正式通知。
> 每个 feedback type（除 progress 外）都跟一个状态变更绑定。
> direction 用 `is_to_down` boolean 区分：true = upstream→downstream，false = downstream→upstream。

### 9.1 列出 Feedback

`GET /briefs/:brief_id/feedbacks?type=progress&is_to_down=false`

```json
Response 200
{
  "feedbacks": [
    {
      "id": "guid",
      "is_to_down": false,
      "type": "progress",
      "from_user_id": "guid",
      "from_user_name": "李四",
      "to_user_id": "guid",
      "to_user_name": "张三",
      "created_at": "2026-06-20T23:00:00Z"
    }
  ],
  "next_cursor": null
}
```

> 查询参数：
> - `type` — 过滤类型（submit / block / delegate / open / progress / cancel / suspend / resume / approve / reject_submit / update）
> - `is_to_down` — 过滤方向
> - 列表模式：不包含 `content` 和 `attachments`

### 9.2 获取单个 Feedback（详情模式）

`GET /feedbacks/:feedback_id`

```json
Response 200
{
  "feedback": {
    "id": "guid",
    "brief_id": "guid",
    "brief_version": 1,
    "is_to_down": false,
    "type": "progress",
    "content": "...",              // 完整内容
    "attachments": [               // 完整附件
      { "name": "截图.png", "url": "/api/v1/files/...", "type": "image" }
    ],
    "from_user_id": "guid",
    "from_user_name": "李四",
    "to_user_id": "guid",
    "to_user_name": "张三",
    "is_auto_generated": false,
    "created_at": "2026-06-20T23:00:00Z",
    "confirmed_at": null
  }
}
```

> 大部分状态变更 feedback 通过 upstream-actions / downstream-actions 端点创建。
> progress 类型可通过此接口查询。

---

## 10. Brief Chain（`/chains`）

### 10.1 列出我的 Chains

`GET /chains`

```json
Response 200
{
  "chains": [
    {
      "chain_id": "guid",
      "title": "Q3 性能优化项目",
      "owner_id": "guid",
      "owner_name": "张三",
      "priority": "p1",
      "root_brief_id": "guid",
      "brief_count": 5,
      "created_at": "2026-06-20T22:00:00Z"
    }
  ]
}
```

> owner_id / owner_name / priority 从 brief_chains 表冗余字段直接读取，不需要 JOIN briefs + users

### 10.2 获取 Chain 详情（含树形结构）

`GET /chains/:chain_id`

```json
Response 200
{
  "chain": {
    "chain_id": "guid",
    "title": "Q3 性能优化项目",
    "owner_id": "guid",
    "owner_name": "张三",
    "priority": "p1",
    "root_brief": { 
      "brief_id": "guid", 
      "title": "...",
      "upstream_state": "in_process",
      "downstream_state": "opened",
      "priority": "p1",
      "created_by_id": "guid",
      "created_by_name": "张三",
      "assigned_to_id": "guid",
      "assigned_to_name": "李四",
      "updated_at": "2026-06-20T22:00:00Z"
    },
    "tree": {
      "brief_id": "root_guid",
      "title": "...",
      "upstream_state": "in_process",
      "downstream_state": "opened",
      "children": [
        {
          "brief_id": "child_guid",
          "title": "...",
          "upstream_state": "done",
          "downstream_state": null,
          "children": []
        }
      ]
    }
  }
}
```

> `root_brief` 使用详情模式
> `tree` 使用列表模式（只包含 `brief_id`, `title`, `upstream_state`, `downstream_state`, `children`）

---

## 11. 用户（`/users`）

### 11.1 获取用户列表

`GET /users?role=created&upstream_state=editing`

```json
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

### 11.2 获取单个用户

`GET /users/:user_id`

```json
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

---

## 12. 文件上传（`/files`）

### 上传流程

1. 客户端调 `POST /files/upload` 上传文件，拿到 `url`
2. 创建/更新 Brief 或 Feedback 时，将 `url` 填入 `attachments` 数组

### 12.1 上传文件

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

### 12.2 获取文件

`GET /files/:file_id`

> 服务端返回文件流（通过 Storage Adapter）

---

## 附录 A：状态组合转移图

```
(editing, null) ──send──→ (sent, null)
(sent, null) ──send──→ (sent, null)           // 替换邀约（version 更新）
                           ↓ accept                ↓ reject
                    (in_process, opened)       → (editing, null)

(in_process, opened) ──downstream 自由──→ (in_process, delegated)
                                       → (in_process, blocked)
                                       → (in_process, submitted)

(in_process, *) ──update──→ (in_process, opened)    // 更新版本，强制下游重开（记录在 feedbacks）
(in_process, submitted) ──approve──→ (done, preserved)
(in_process, submitted) ──reject_submit──→ (in_process, opened)
(in_process, *) ──cancel──→ (cancelled, preserved)   // downstream_state 保留
(in_process, *) ──suspend──→ (suspended, preserved)  // downstream_state 保留
(suspended, preserved) ──resume──→ (in_process, preserved)  // 原样恢复
```

> send 是邀约阶段桥梁（editing/sent → transfer_history），update 是合约期间桥梁（in_process → feedbacks）。两者对 version 操作相同（version→final, current_version 更新）。

---

## 附录 B：动作与端点对照表

| 端点分组 | URL | action | 操作对象 | upstream_state 变更 | downstream_state 变更 | 创建的 feedback type |
|---------|-----|--------|---------|:-------------------:|:-------------------:|---------------------|
| **Editing** | `POST /briefs/:id/editing` | patch | version only | 不变 |         不变          | — |
| | | submit-review | version only | 不变 |         不变          | — |
| **Transfer** | `POST /briefs/:id/transfer` | send（from editing） | version + brief | → sent |         不变          | — (transfer_history) |
| | | send（from sent） | version + brief | 不变 |         不变          | — (transfer_history) |
| | | accept | brief only | → in_process |      → opened       | — (transfer_history) |
| | | reject | brief only | → editing |       → null        | — (transfer_history) |
| **Upstream-action** | `POST /briefs/:id/upstream-actions` | cancel | brief only | → cancelled |         保留          | cancel |
| | | suspend | brief only | → suspended |         保留          | suspend |
| | | resume | brief only | → in_process |         保留          | resume |
| | | approve | brief only | → done |         保留          | approve |
| | | reject_submit | brief only | 不变 |      → opened       | reject_submit |
| | | update | version + brief | 不变 |      → opened       | update |
| **Downstream-action** | `POST /briefs/:id/downstream-actions` | process | brief only | 不变 |         不变          | progress |
| | | submit | brief only | 不变 |     → submitted     | submit |
| | | open | brief only | 不变 |      → opened       | open |
| | | delegate | brief only | 不变 |     → delegated     | delegate |
| | | block | brief only | 不变 |      → blocked      | block |

> **version 与 state 解耦**：Editing 组只操作 version，Upstream/Downstream-action 组只操作 brief 状态（update 除外，同时操作 version + brief）。Transfer 组的 send 是邀约阶段桥梁，Upstream-action 的 update 是合约期间桥梁。

---

## 附录 C：冗余字段对照表

| 表 | 冗余字段 | 来源 | 写入时机 |
|---|---------|------|---------|
| briefs | created_by_name | users.name | 创建 brief 时 |
| briefs | assigned_to_name | users.name | send / accept / 临时用户升级时 |
| feedbacks | from_user_name | users.name | 创建 feedback 时 |
| feedbacks | to_user_name | users.name | 创建 feedback 时 |
| brief_transfer_history | from_user_name | users.name | send 时 |
| brief_transfer_history | to_user_name | users.name | send 时 |
| brief_chains | owner_id / owner_name | root_brief.created_by + users.name | 创建 chain 时 |
| brief_chains | priority | root_brief.priority | root_brief priority 变更时同步 |

> 合约语义：名字是操作时的快照（"当时签合约的人叫什么"），不是实时值。用户改名不自动同步，除非主动触发。

---

## 附录 D：MVP 不做的功能

- ❌ Arbiter LLM 自动审查（人工替代）
- ❌ Task / Kanban 子系统（后续设计）
- ❌ 跨系统互操作（bc:// 协议）
- ❌ 可配置工作流模板
- ❌ 微信/三方登录（先邮箱/手机注册）
- ❌ 细粒度权限（先 created_by 全权限）
- ❌ 手机号验证码登录（MVP 只支持密码登录）
- ❌ 邀请链接验证码（MVP 只做信任场景，详见 05-invite-link-design.md）
- ❌ feedbacks 中 upstream→downstream 类型的 Arbiter 审查（MVP 不审查）
