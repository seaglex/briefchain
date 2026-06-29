# Brief / Feedback 子系统设计

> 最后更新：2026-06-28（v5：send/update 分离）

## 1. 状态机

### 1.1 双状态模型

Brief 的状态由两个字段共同表达：`upstream_state` 和 `downstream_state`。这使视角归属在数据模型层面就清晰可见，无需额外文档说明。

**upstream_state 枚举（6 个）：**

```
"editing"     // upstream 编写中（替代原 draft/reviewed 在 briefs 层级）
"sent"        // 已发送给 downstream，等待响应（邀约）
"in_process"  // downstream 已接单，brief 正在执行
"suspended"   // upstream 暂停（downstream_state 保留不动）
"cancelled"   // 取消（终态，downstream_state 保留用于历史审计）
"done"        // upstream 验收通过（终态）
```

**downstream_state 枚举（4 个 + null）：**

```
null           // upstream_state 不是 in_process 时，无 downstream 角色
"opened"       // downstream 已接单，正在执行（首次接单 / 重新打开 / 上游打回 / 上游推送更新）
"delegated"    // downstream 已拆解委派（可选中间状态）
"blocked"      // downstream 遇阻，需 upstream 介入
"submitted"    // downstream 提交完成，等待 upstream review
```

> `draft` / `reviewed` 只存在于 `brief_versions.status`，不在 briefs 层级。brief 层级用 `editing` 统一表达"upstream 正在编写"。

### 1.2 有效状态组合矩阵

上下游状态尽量解耦，尽量少限制，前端可以只提供合理的操作，后端不限制。
- editing / edit，还没有建立联系，后端不能有任何状态
- in_process / suspended / cancelled / done，虽然后三者不需要再投入，但是更新进度还是可以的。

动作限制类似
- version 在 draft 状态，才能 view 动作
- version 在 reviewed 状态，才能 send / update 动作
- upstream 在 send 状态，downstream 只能有 accept or reject 动作，upstream 可以再 sent（先修改）
- upstream 在 in_process / suspended 状态，自己才能 update
- upstream 在 in_process / suspended / cancelled / done 状态，downstream 都可以修改状态
- downstream 在 submitted 状态，upstream 才能 approve or reject_submit

### 1.3 状态流转图

```
editing ──(send)──→ sent ──(send)──→ sent    // 替换邀约（version 更新，brief 状态不变）
                      ↓ accept               ↓ reject
                 (in_process, opened)      → (editing, null)

(in_process, opened) ──downstream 自由切换──→ (in_process, delegated)
                                            → (in_process, blocked)
                                            → (in_process, submitted)

(in_process, *) ──(update)──→ (in_process, opened)    // 更新版本，强制下游重开
(suspended, *) ──(update)──→ (suspended, opened)    // 更新版本，强制下游重开

(in_process, submitted) ──approve──→ (done, preserved)
(in_process, submitted) ──reject_submit──→ (in_process, opened)
(in_process, *) ──cancel──→ (cancelled, preserved)   // downstream_state 保留
(in_process, *) ──suspend──→ (suspended, preserved)  // downstream_state 保留
(suspended, preserved) ──resume──→ (in_process, preserved)  // 原样恢复
```

### 1.3.1 version 与 state 解耦

**核心原则：version 生命周期和 brief 状态机是两条独立的线，`send`（邀约阶段）和 `update`（合约期间）是两座桥梁。**
- sent 后，breif 和 version 关联起来，如果被 rejected，依然关联，这时 version 状态是 final
- version.final 代表 version 不能随便修改了
- brief.version 代表 brief 和 version 的关联
- brief.upstream_state & brief.downstream_state 代表 brief状态

| 操作 | 作用域 | 说明                                          |
|------|--------|---------------------------------------------|
| patch | 只改 version.status 和内容 | 不碰 upstream_state / downstream_state        |
| submit-review | 只改 version.status | draft → reviewed，不碰 brief 状态                |
| send | 桥梁：version → final + brief 状态变更 | 唯一同时操作两边的动作，version必须是reviewed状态（或者是final状态） |
| accept / reject / cancel / suspend / resume / approve / reject_submit | 只改 brief 状态 | 不碰 version                                  |
| process / submit / open / delegate / block | 只改 brief 状态 | 不碰 version                                  |

**send 的两种场景（邀约阶段，记录在 transfer_history）：**

| brief 状态 | send 的效果                                         | transfer_history |
|-----------|--------------------------------------------------|-----------------|
| editing | 首次发送：current_version null→N，brief editing→sent   | ✅ 新记录 |
| sent | 替换邀约：current_version 更新，brief 状态不变，或者是被拒绝后重新sent | ✅ 新记录 |

**update 的场景（合约期间，记录在 feedbacks）：**

| brief 状态 | update 的效果 | feedback |
|-----------|---------------|----------|
| in_process / suspended | 更新合约：current_version 更新，downstream→opened | type=update |

> **version 必须处于 reviewed 状态**（与 send 相同）。update 前需先 submit-review 通过审查。

> final 状态下也允许 send：upstream 发出邀约后、downstream 响应前，upstream 可以修改并重新发送，代价更小（还没建立合约）。

**patch 的版本行为（只看 version.status，不看 brief 状态）：**

| version.status | patch 效果 |
|---------------|-----------|
| draft | 原地修改，version 不变 |
| reviewed | 原地修改，status 重置为 draft |
| final | 不能修改，自动创建新版本 v(n+1) draft；如已存在 v(n+1) 则报错 |

> patch 不需要检查 upstream_state。只要 upstream_state 不是 cancelled/done（终态），upstream 随时可以 patch 编辑版本内容。



### 1.4 状态分组（降低认知负担）

| 分组 | 组合 | 直觉 |
|------|------|------|
| 编写中 | (editing, null) | "我还在想" |
| 等候中 | (sent, null) | "等对方回应" |
| 执行中 | (in_process, opened/delegated) | "在推进" |
| 待审 | (in_process, submitted) | "交卷了等批" |
| 阻塞 | (in_process, blocked) | "卡住了" |
| 暂停 | (suspended, any) | "冻结" |
| 结束 | (done, null) / (cancelled, any) | "落幕" |

### 1.5 关键设计决策

- **version 与 state 解耦**：version 生命周期（draft/reviewed/final）和 brief 状态机（upstream_state + downstream_state）是两条独立的线。patch 和 submit-review 只操作 version，不碰 brief 状态；accept/cancel/suspend 等只操作 brief 状态，不碰 version。`send` 是唯一同时操作两边的桥梁
- **双状态替代单状态**：`upstream_state` + `downstream_state` 替代原来的单一 `status`（11 enum）。视角归属在数据模型层面表达，无需文档补充说明
- **`previous_status` 不再需要**：suspend 只改 `upstream_state` → suspended，`downstream_state` 自然保留不动；resume 时 `upstream_state` → in_process，`downstream_state` 原样恢复。不再需要额外字段记录"之前的状态"
- **`editing` 替代 brief 层级 draft/reviewed**：draft/reviewed 只在 `brief_versions.status`，brief 层级统一用 `editing` 表达"upstream 正在编写"
- **`update` 独立于 `send`**：send 用于邀约阶段（editing/sent，记录在 transfer_history），update 用于合约期间（in_process，记录在 feedbacks）。两者对 version 的操作相同（version→final, current_version 更新），但记录位置不同——send 是初始交接，update 是合约期通知
- **`opened` 替代 `accepted` + `reopened`**：多条路径汇入 opened（首次接单、上游打回、上游推送更新、下游从 submitted 自行撤回、从 delegated/block 解除），用 `opened` 比用 `accepted` 更中性
- **downstream 自由控制 downstream_state**：downstream 可从任意下游状态切换到 opened/delegated/blocked/submitted（只要 upstream_state = in_process），不需要为每个动作起独立名字
- **upstream `update` 强制 downstream_state → opened**：需求变更后下游必须基于新版本重新执行，无论下游当时处于什么状态
- **upstream `reject_submit` 强制 downstream_state → opened**：upstream 打回提交，downstream 必须重做
- **cancel 保留 downstream_state**：便于历史审计（可看到取消时下游处于什么状态）
- **suspended 保留 downstream_state**：resume 时原样恢复，不需要 `previous_status` 字段
- **Brief 状态变更在详情页操作**，不在 Kanban 拖拽 — Brief 是合约性质，状态变更需要完整语境和审慎操作
- **sent / accept / reject 走 brief_transfer_history**（初始交接/邀约阶段）
- **其他状态变更通知走 feedbacks 表**（合约期间的正式合同通知）
- **冗余存储人名**：briefs / feedbacks / transfer_history / chains 表都冗余存储用户名字（name 快照）。合约记录"当时签合同的人叫什么名字"，不是"这个人现在叫什么名字"。列表查询不需要 JOIN users 表，O(1) 拿到人名
- **API 聚类**：端点按状态阶段分为 4 组（editing / transfer / upstream-action / downstream-action），每组用路径表达阶段 + `action` 参数表达动作，结构完全一致

### 1.6 suspended 的挂起与恢复

**可从哪些状态挂起：**

| upstream_state | 合理性 |
|:--------------:|--------|
| sent | ✅ upstream 发出后改主意 |
| in_process | ✅ 暂停执行 |

**不可挂起：** editing（还没发出去，直接编辑即可）、done、cancelled（已终态）

**恢复后：** `upstream_state` → in_process，`downstream_state` 不变（保留原值）。不再需要 `previous_status` 字段。

### 1.7 Brief 详情页的操作设计

Brief 是合约，操作是审慎的。前端根据当前用户角色 + brief 状态 + version 状态，显示可用动作。

**get_brief 返回 `unfinalized_version` 字段**（版本号，非 id）：
- current_version = null → 返回最新 draft 版本内容，unfinalized_version = 该版本号
- current_version = N，存在 N+1 draft → 返回 vN 内容（final），unfinalized_version = N+1
- current_version = N，无更高版本 → 返回 vN 内容，unfinalized_version = null

**前端行为按角色区分：**

**downstream（自己 = assigned_to）：**
- 只能查看关联版本（current_version 对应的 final 版本），看不到 draft
- upstream = sent → 支持 accept / reject
- upstream ≠ cancelled / done / sent → 支持变更为 delegated / blocked / opened / submitted

**upstream（自己 = created_by）：**
- 打开关联版本（current_version 对应的 final 版本）：
  - upstream ≠ cancelled / done → 支持修改（patch 在 final 上自动创建新 draft）
  - 如存在更高 draft 版本，前端自动 load 该版本（在此基础上修改）
  - 修改后打开的就是非关联版本（draft）
- 打开非关联版本（draft）：
  - upstream ≠ cancelled / done → 支持修改
  - draft 状态 → 支持提交审查（submit-review）
  - reviewed 状态 → 支持发送
    - assigned_to 为空（editing/sent 状态）→ send（需选择接收方：首次发送 / 替换邀约）
    - assigned_to 不为空（in_process 状态）→ update（直接确认，更新合约）

```
[upstream=editing, version=draft] [upstream 视角]
  → [编辑 PATCH] [提交审查 → reviewed]

[upstream=editing, version=reviewed] [upstream 视角]
  → [编辑 PATCH → draft] [发送 send → 选择接收方]

[upstream=sent, version=reviewed] [upstream 视角]
  → [编辑 PATCH → draft] [重新发送 send → 替换邀约]

[upstream=sent] [downstream 视角]
  → [接受 → (in_process, opened)] [拒绝 → editing]

[upstream=in_process, version=reviewed] [upstream 视角]
  → [编辑 PATCH → draft] [更新 update → 更新合约（直接确认）]

[upstream=in_process, downstream=opened] [downstream 视角]
  → [委派 → delegated] [标记阻塞 → blocked] [提交完成 → submitted]

[upstream=in_process, downstream=submitted] [upstream 视角]
  → [验收通过 → (done, perserved)] [打回 → (in_process, opened)]

[upstream=in_process, downstream=submitted] [downstream 视角]
  → [撤回 → opened]（自己觉得做得不够好）

[upstream=in_process, downstream=blocked] [downstream 视角]
  → [解除阻塞 → opened/delegated]

[upstream=suspended] [upstream 视角]
  → [恢复 → resume] [取消 → cancel]
```

### 1.8 Agent 估算 sub-tree 进展

upstream 在 `delegated` 状态下，看到的不只是一个静态状态，而是可以通过 agent 实时获得整个 sub-tree 的进展估算：

```
Brief: "重构认证模块" (in_process, delegated)
  ├─ Task: 设计新架构 [done]
  ├─ Task: 实现 OAuth [in_progress]
  ├─ Task: 迁移旧逻辑 [todo]
  └─ Brief: 文档更新 (in_process, opened)

Agent 估算: 约 40% 完成，预计还需 2 天
```

这让 `delegated` 不再是"黑盒等待"，upstream 可以随时了解进展而不需要催 downstream。`status_changed_at` 和 `status_changed_by` 字段为此提供基础数据。

## 2. 数据库设计

### 2.1 briefs（实体表）

```sql
briefs {
  brief_id: GUID              -- 主键
  root_id: GUID               -- 根 brief，O(1) 追溯整棵树（根节点 root_id = brief_id）
  parent_id: GUID | null      -- 父 brief，null = 根节点
  is_root: boolean            -- true = 这是根 brief，也是 chain 的代表

  current_version: number | null  -- 最新正式（已 final）版本号；null = 还没有任何 final 版本

  upstream_state: enum         -- 6 个状态（见 1.1）
  downstream_state: enum | null -- 4 个状态 + null（见 1.1）

  title: string               -- 当前正式版本的标题（= brief_versions[current_version].title，current_version=null 时取 v1）
  priority: enum              -- 当前正式版本的优先级（"p0"|"p1"|"p2"|"p3"）

  expected_completion_at: timestamp | null  -- 预期完成时间（upstream 在 brief 中填写，可在版本中调整）

  created_by: GUID            -- upstream，写这个 brief 的人
  created_by_name: string     -- 冗余：创建时 upstream 的名字快照（合约签名语义）
  assigned_to: GUID | null    -- downstream，null = 还没分配
  assigned_to_name: string | null -- 冗余：分配时 downstream 的名字快照

  status_changed_at: timestamp -- 最后一次状态变更时间（agent 估算进展用）
  status_changed_by: GUID     -- 最后一次状态变更的操作人
  status_changed_by_name: string -- 冗余：最后一次状态变更操作人的名字快照

  created_at: timestamp
  updated_at: timestamp
}
```

设计决策：
- `children_ids` 不存储，查子节点用 `WHERE parent_id = ?`
- `root_id` 在根节点指向自己，查询整棵树统一用 `WHERE root_id = X`
- **双状态替代单状态 + previous_status**：原来 `status`（11 enum）+ `previous_status` → 现在 `upstream_state`（6 enum）+ `downstream_state`（4 enum + null）。suspend 只改 upstream_state，downstream_state 自然保留，resume 原样恢复，不再需要 previous_status
- `status_changed_at` 区分"内容改了"和"状态变了"，agent 估算 sub-tree 进展时需要知道每个子 brief 停在某个状态多久了
- briefs 表只管"当前状态"，状态变更的原因和历史都在 feedbacks 表查
- **冗余人名字段**：`created_by_name` / `assigned_to_name` / `status_changed_by_name` 在创建/分配/状态变更时从 users 表读取并写入，列表查询不需要 JOIN。合约语义上，名字是操作时的快照——"当时签合约的人叫什么"，不是实时值。如果用户改名，合约上的名字不变（除非主动触发同步）

**版本字段说明：**
- `current_version` 是权威字段，语义为"最新 final（正式）版本号"。初始值为 `null`（还没有任何 final 版本）；只有该版本被标记为 final 后才更新为版本号。所有读取方直接用 briefs 表，不需要 JOIN 版本表再筛选
- `title` / `priority` 是 denormalize 字段，等于 `brief_versions WHERE version = current_version` 的对应值（`current_version = null` 时取 v1），新版本被标记为 final 时同步更新。避免列表查询 JOIN 版本表
- `content` / `attachments` 不 denormalize（体积大，只有详情页需要，从 brief_versions 读）

---

### 2.2 brief_versions（版本表）

每次内容修改都生成新 version，完整保留历史，用于 track 变更对项目整体投入的影响。

```sql
brief_versions {
  brief_id: GUID              -- 联合主键
  version: number              -- 联合主键，从 1 开始

  status: enum                 -- 版本生命周期状态
  -- "draft":     upstream 编辑中，未交付（只对 upstream 可见，downstream 看不到）
  -- "reviewed":  Arbiter 审查通过，待交付
  -- "final":      已交付给 downstream（正式版本，有约束力）— 版本终态，不再变化

  title: string
  content: string              -- 自由格式，不限制结构（Arbiter 管质量标准）
  attachments: json            -- [{name, url, type}]

  priority: enum               -- "p0" | "p1" | "p2" | "p3"
  estimated_man_days: number | null
  expected_completion_at: timestamp | null  -- 预期完成时间（从 briefs 表同步，版本中可调整）

  arbiter_review_id: GUID | null -- 该版本最终通过/force_skip 的 Arbiter 审查记录
  -- 指向 brief_arbiter_reviews.id
  -- 同一版本可能多次审查（失败后重审、force_skip），此处指向最新有效的那次
  -- send 时 transfer_history.arbiter_review_id 从此字段读取，无需再查 reviews 表

  is_upstream_changed: boolean -- 是否因上游变更而修改
  revision_reason: string      -- 修改原因，自由文本

  modified_by: GUID
  modified_by_name: string    -- 冗余：修改人名字快照
  modified_at: timestamp       -- brief 内容修改时间
  change_summary: string       -- LLM 自动生成 + 人工确认

  created_at: timestamp
  updated_at: timestamp
}
```

#### 版本生命周期流转

```
[新建 brief]          → v1: draft（briefs.current_version = null，upstream_state = editing）
[upstream patch]      → v1: draft（原地修改，version 不变）
[upstream 提交审查]    → v1: reviewed（arbiter_review_id 填入）
[upstream send]       → v1: final（briefs.current_version = 1，title/priority 同步）
                       upstream_state = sent, downstream_state = null

[downstream accept]   → upstream_state = in_process, downstream_state = opened

[upstream patch]      → v2: draft（v1 是 final 不能改，自动创建 v2）
[upstream update]     → v2: final（briefs.current_version = 2，title/priority 同步）
                       downstream_state = opened（强制重开）
                       feedback(type=update) 创建
```

**send 从 sent 状态发起（替换邀约）：**
```
[upstream send from sent] → v2: final（briefs.current_version = 2）
                           upstream_state 不变（仍为 sent），downstream_state 不变（null）
                           无 feedback（尚未建立合约）
                           transfer_history 新增记录
```

**关键规则：**
- `briefs.current_version` 初始值为 `null`（还没有任何 final 版本）；只有版本 status 变为 `final` 时才更新为版本号，draft/reviewed 不影响
- downstream 执行的"当前正式版本" = `briefs.current_version`，不需要查 brief_versions 的 status
- `final` 是版本终态，不再变化；新版本 final 后，旧版本通过 `briefs.current_version` 增大自动作废，无需显式标记
- patch 只看 version.status：draft/reviewed → 原地改（reviewed 重置为 draft）；final → 创建新版本
- send 是邀约阶段桥梁：version → final 同时触发 brief 状态变更（首次发送/替换邀约，记录在 transfer_history）；update 是合约期间桥梁：version → final + downstream → opened（记录在 feedbacks）
- send / update 走完整 Arbiter 审查（draft → reviewed → final），MVP: auto-pass

---

### 2.3 brief_transfer_history

一次交互一条记录，覆盖 sent → accepted / rejected 完整生命周期（邀约阶段）。

```sql
brief_transfer_history {
  id: GUID
  brief_id: GUID
  brief_version: number       -- 发送的是哪个版本

  arbiter_review_id: GUID     -- 本次发送前通过的 Arbiter 审查记录（从 brief_versions.arbiter_review_id 读取）

  from_user: GUID             -- upstream
  from_user_name: string      -- 冗余：发送时 upstream 的名字快照
  to_user: GUID               -- downstream
  to_user_name: string        -- 冗余：发送时 downstream 的名字快照

  sent_at: timestamp          -- 发送时间
  accepted_at: timestamp | null -- downstream 接受时间
  rejected_at: timestamp | null -- downstream 拒绝时间

  rejection_reason: string | null -- 拒绝理由（downstream 填写）
}
```

---

### 2.4 brief_chains（链元数据表）

root brief 天然是 chain 的代表，`brief_chains` 只存链级元数据，不冗余存储成员关系。

```sql
brief_chains {
  chain_id: GUID             -- = root_brief_id，不重复
  title: string              -- 链/项目名称
  owner_id: GUID             -- 冗余：root_brief 的 created_by
  owner_name: string         -- 冗余：owner 的名字快照
  priority: enum             -- 冗余：root_brief 当前优先级（"p0"|"p1"|"p2"|"p3"）
  created_at: timestamp
  updated_at: timestamp
}
```

成员关系通过 `briefs WHERE root_id = chain_id` 反查，不需要成员表。

冗余字段说明：
- `owner_id` / `owner_name`：chains 列表需要知道"谁负责这个项目"，避免 JOIN briefs + users
- `priority`：chains 列表需要显示项目优先级，避免 JOIN briefs
- root_brief 的 title/priority 变更时，同步更新 brief_chains

---

### 2.5 brief_arbiter_reviews（Brief 审查表）

brief 在发送前必须经过 Arbiter（LLM）审查，审查不通过则不允许发送。

```sql
brief_arbiter_reviews {
  id: GUID
  brief_id: GUID
  brief_version: number      -- 审查的是哪个版本

  arbiter_id: GUID           -- LLM 实例标识，或 "admin"（强制跳过）

  status: "passed" | "failed" | "force_skipped"
  score: number              -- 0-100，质量评分

  issues: json               -- 具体问题列表
  -- 结构：[{"field": string, "severity": "blocker"|"major"|"minor", "message": string}]
  -- field 指向 brief_versions 的具体字段（title/content/attachments/priority 等）

  suggestions: json          -- ["建议补充具体的数据指标", ...]
  -- 结构：string[]

  reviewed_at: timestamp
}
```

---

### 2.6 feedbacks（正式合同通知表）

BriefChain 的正式沟通渠道。feedbacks 是合约期间的**正式合同通知**，不是聊天消息。

- 闲聊用其他 IM，沟通完再总结成 feedback 发出
- 每个 feedback type（除 progress 外）都跟一个状态变更绑定
- 双向统一：up→down 和 down→up 都走同一张表，用 `is_to_down` 区分方向
- 天然支持多次反复：每次 reject_submit、每次 suspend/resume 都是一条新记录，完整历史
- feedbacks 发出后根据类型可能需要 Arbiter 审查

```sql
feedbacks {
  id: GUID
  brief_id: GUID
  brief_version: number      -- 关联的 brief 版本

  is_to_down: boolean        -- true = upstream→downstream；false = downstream→upstream
  type: enum
  -- is_to_down=true:  "cancel" | "suspend" | "resume" | "approve" | "reject_submit" | "update"
  -- is_to_down=false: "submit" | "block" | "delegate" | "open" | "progress"

  content: string             -- 说明 / 原因 / 反馈内容
  attachments: json           -- [{name, url, type}]

  from_user: GUID             -- 发出方
  from_user_name: string      -- 冗余：发出方名字快照
  to_user: GUID               -- 接收方
  to_user_name: string        -- 冗余：接收方名字快照

  is_auto_generated: boolean  -- true = LLM 汇总 children 完成情况生成，需人工确认
  confirmed_at: timestamp | null -- 人工确认时间（is_auto_generated=true 时）

  created_at: timestamp
  updated_at: timestamp
}
```

#### type → 状态变更映射

| is_to_down | type | upstream_state 变更 | downstream_state 变更 | 说明 |
|:----------:|------|:-------------------:|:---------------------:|------|
| true | cancel | → cancelled | 保留（不变） | upstream 取消合约 |
| true | suspend | → suspended | 保留（不变） | upstream 暂停 |
| true | resume | → in_process | 保留（不变） | upstream 恢复暂停 |
| true | approve | → done | 保留（不变） | upstream 验收通过，终态 |
| true | reject_submit | 不变 | → opened | upstream 打回提交 |
| true | update | 不变 | → opened | upstream update（从 in_process），推送新版本，强制下游重开 |
| false | submit | 不变 | → submitted | downstream 提交完成 |
| false | block | 不变 | → blocked | downstream 遇阻 |
| false | delegate | 不变 | → delegated | downstream 拆解委派 |
| false | open | 不变 | → opened | downstream 主动重开（从 submitted 撤回等） |
| false | progress | 不变 | 不变 | 进度更新，不触发状态变更 |

#### content 规则

| type | content 是否必填 | 说明 |
|------|:----------------:|------|
| cancel | 必填 | 取消原因 |
| suspend | 必填 | 暂停原因 |
| resume | 必填 | 恢复原因 |
| approve | 必填 | 验收说明 |
| reject_submit | 必填 | 打回原因 |
| update | 必填 | 变更说明 |
| submit | 必填 | 完成说明 |
| block | 必填 | 阻塞原因 |
| delegate | **可空** | 可以只说"已拆解"或不写 |
| open | 必填 | 重开原因 |
| progress | **可空** | 纯进度更新 |

#### reject_submit vs update 的区别

两者都导致 downstream_state → opened，但语义不同：

| | reject_submit | update |
|---|--------------|--------|
| brief 内容 | 不变 | **新版本 final**（version +1，旧版本自动作废） |
| 场景 | "验收标准没达到，继续改" | "需求变了，按新版本重新做" |
| downstream 看到 | 原版本 + 打回原因 | 新版本 + 变更说明 |
| briefs.current_version | 不变 | +1（新版本被标记为 final 时更新） |
| 版本生命周期 | 不涉及新版本 | draft → reviewed → final（走完整 Arbiter 审查） |
| downstream 是否可以 block | 不可以（打回是强制动作） | 可以（block 原因："不接受更新"） |
| API 端点 | upstream-actions?action=reject_submit | upstream-actions?action=update |

#### Arbiter 审查规则

| feedback type | 需审查？ | 说明 |
|---------------|---------|------|
| submit | ✅ | completion evidence 审查 |
| block | ❌ | downstream 反馈，MVP 不审查 |
| progress | ❌ | 进度更新不审查 |
| delegate / open | ❌ | downstream 内部操作 MVP 不审查 |
| cancel / suspend / resume | ❌ | upstream 指令 MVP 不审查 |
| approve / reject_submit / update | ❌ | upstream 操作 MVP 不审查 |

---

### 2.7 feedback_arbiter_reviews（Feedback 审查表）

部分 feedbacks（submit）发出前必须经过 Arbiter 审查。

```sql
feedback_arbiter_reviews {
  id: GUID
  feedback_id: GUID          -- 关联 feedbacks 表

  arbiter_id: GUID

  status: "passed" | "failed" | "force_skipped"

  result: json               -- 审查结果，因 feedback type 而异
  -- submit 类型结构：
  --   {"evidence_check": "pass"|"fail", "missing": string[], "can_auto_done": boolean}
  -- block 类型结构：
  --   {"block_confirmed": boolean, "suggest_swap": boolean, "reason": string}

  reviewed_at: timestamp
  created_at: timestamp
  updated_at: timestamp
}
```

---

### 2.8 状态变更与记录对照表

| 状态变更 | 发起方 | 记录位置 |
|---------|--------|---------|
| (editing, null) → (sent, null) | upstream: send（首次） | brief_transfer_history |
| (sent, null) → (sent, null) | upstream: send（替换邀约） | brief_transfer_history |
| (sent, null) → (in_process, opened) | downstream: accept | brief_transfer_history |
| (sent, null) → (editing, null) | downstream: reject | brief_transfer_history + rejection_reason |
| (in_process, *) → (in_process, opened) | upstream: update | feedbacks (type=update, is_to_down=true) |
| downstream_state → submitted | downstream: submit | feedbacks (type=submit, is_to_down=false) |
| downstream_state → delegated | downstream: delegate | feedbacks (type=delegate, is_to_down=false) |
| downstream_state → blocked | downstream: block | feedbacks (type=block, is_to_down=false) |
| downstream_state → opened | downstream: open | feedbacks (type=open, is_to_down=false) |
| (in_process, submitted) → (done, preserved) | upstream: approve | feedbacks (type=approve, is_to_down=true) |
| (in_process, submitted) → (in_process, opened) | upstream: reject_submit | feedbacks (type=reject_submit, is_to_down=true) |
| (in_process, *) → (suspended, preserved) | upstream: suspend | feedbacks (type=suspend, is_to_down=true) |
| (suspended, preserved) → (in_process, preserved) | upstream: resume | feedbacks (type=resume, is_to_down=true) |
| (in_process, *) → (cancelled, preserved) | upstream: cancel | feedbacks (type=cancel, is_to_down=true) |
| 进度更新（无状态变化） | downstream: process | feedbacks (type=progress, is_to_down=false) |

---

## 3. 已完成

- [x] briefs 实体表设计（2.1）— 双状态模型（upstream_state + downstream_state），删除 previous_status
- [x] brief_versions 版本表设计（2.2）— version 与 state 解耦，send/update 是两座桥梁
- [x] brief_transfer_history 流转记录表设计（2.3）
- [x] brief_chains 链元数据表设计（2.4）
- [x] brief_arbiter_reviews Brief 审查表设计（2.5）
- [x] feedbacks 正式沟通表设计（2.6）— 11 个 type，content 规则
- [x] feedback_arbiter_reviews 审查表设计（2.7）
- [x] 状态机定义（第 1 章）— 双状态模型，6 upstream + 4 downstream + null
- [x] type → 状态变更映射（2.6）
- [x] 状态变更与记录对照表（2.8）

## 4. 待讨论（暂缓）

- [ ] Task 数据模型设计（brief_id required）
- [ ] Kanban & Task 子系统设计
- [ ] Arbiter 审查的具体维度（LLM prompt / 评分标准）
- [ ] MVP 范围定义（哪些表先不做）
- [ ] 跨系统互操作协议设计（`bc://` 协议）
