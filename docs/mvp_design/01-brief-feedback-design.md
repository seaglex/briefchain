# Brief / Feedback 子系统设计

> 最后更新：2026-06-21

## 1. 状态机

### 1.1 主状态（跨人转移，upstream 视角）

```
draft
  ↓ (提交 Arbiter 审查，通过)
reviewed
  ↓ (发送)
sent
  ↓ (发送给 downstream，记录在 brief_transfer_history)
accepted ─── OR ─── (downstream 拒绝，brief.status 回到 draft)
  ↓                                   ↓ (upstream 修改后重新发送)
                                     reviewed
done or cancelled (upstream 撤回)

accepted → blocked (downstream 发出 blocked feedback)
blocked  → accepted (阻塞解除)
```

状态枚举（`briefs.status`）：
```
"draft"      // 编辑中 / 被 downstream 拒绝后修改中
"reviewed"   // Arbiter 通过，待分配 downstream（发送前状态）
"sent"       // 已发送给 downstream，等待响应
"accepted"   // downstream 接受，执行中
"done"       // 完成，有 evidence（completion feedback 通过 Arbiter 审查后自动转）
"blocked"    // downstream 发出 blocked feedback，已通知 upstream
"cancelled"  // upstream 撤回
```

### 1.2 内部状态（downstream 视角，使用方自管理）

- 辅助使用方自己管理进度，不阻塞跨人转移
- 支持自定义模板，每个人/团队选择自己的模板

**简化模式（MVP）：预留标签触发内置行为**

下列标签有内置语义，使用这些标签时自动触发对应行为：
- `accepted` → 无自动行为（主状态已由 brief 流转管理）
- `blocked` → 自动生成 blocked feedback 发给 upstream
- `done` → 提示可以提交 completion feedback

**完整模式（后续）：模板配置**

模板中每个状态可配置：
- 是否通知 upstream
- 通知内容模板（可引用 brief 字段）

MVP 阶段使用简化模式，后续开放完整配置。

## 2. 数据库设计

### 2.1 briefs（实体表）

```sql
briefs {
  brief_id: GUID          -- 主键
  root_id: GUID           -- 根 brief，O(1) 追溯整棵树（根节点 root_id = brief_id）
  parent_id: GUID | null  -- 父 brief，null = 根节点
  is_root: boolean        -- true = 这是根 brief，也是 chain 的代表

  current_version: number -- 当前最新版本号
  status: enum            -- 主状态（跨人转移）

  created_by: GUID        -- upstream，写这个 brief 的人
  assigned_to: GUID | null -- downstream，null = 还没分配

  created_at: timestamp
  updated_at: timestamp
}
```

设计决策：
- `children_ids` 不存储，查子节点用 `WHERE parent_id = ?`
- `root_id` 在根节点指向自己，查询整棵树统一用 `WHERE root_id = X`
- `sent_at` 不存储，发送时间记录在 brief_transfer_history 表
- `source_system` MVP 阶段忽略，跨系统后续再加

---

### 2.2 brief_versions（版本表）

每次内容修改都生成新 version，完整保留历史，用于 track 变更对项目整体投入的影响。

```sql
brief_versions {
  brief_id: GUID              -- 联合主键
  version: number              -- 联合主键，从 1 开始

  title: string
  content: string              -- 自由格式，不限制结构（Arbiter 管质量标准）
  attachments: json            -- [{name, url, type}]

  priority: enum               -- "p0" | "p1" | "p2" | "p3"
  estimated_man_days: number | null

  is_upstream_changed: boolean -- 是否因上游变更而修改
  revision_reason: string      -- 修改原因，自由文本

  modified_by: GUID
  modified_at: timestamp       -- brief 内容修改时间
  change_summary: string       -- LLM 自动生成 + 人工确认

  created_at: timestamp
  updated_at: timestamp
}
```

---

### 2.3 brief_transfer_history

一次交互一条记录，覆盖 sent → accepted / rejected 完整生命周期。

```sql
brief_transfer_history {
  id: GUID
  brief_id: GUID
  brief_version: number       -- 发送的是哪个版本

  arbiter_review_id: GUID     -- 本次发送前通过的 Arbiter 审查记录

  from_user: GUID             -- upstream
  to_user: GUID               -- downstream

  sent_at: timestamp          -- 发送时间
  accepted_at: timestamp | null -- downstream 接受时间
  rejected_at: timestamp | null -- downstream 拒绝时间

  rejection_reason: string | null -- 拒绝理由（downstream 填写）
}
```

查询示例：
- 正在等待下游响应：`WHERE accepted_at IS NULL AND rejected_at IS NULL`
- 某 brief 被拒绝过几次：`WHERE brief_id = X AND rejected_at IS NOT NULL`

---

### 2.4 brief_chains（链元数据表）

root brief 天然是 chain 的代表，`brief_chains` 只存链级元数据，不冗余存储成员关系。

```sql
brief_chains {
  chain_id: GUID             -- = root_brief_id，不重复
  title: string              -- 链/项目名称
  created_at: timestamp
  updated_at: timestamp
}
```

成员关系通过 `briefs WHERE root_id = chain_id` 反查，不需要成员表。

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

### 2.6 feedback_arbiter_reviews（Feedback 审查表）

feedbacks（blocked / completion）发出前必须经过 Arbiter 审查。

```sql
feedback_arbiter_reviews {
  id: GUID
  feedback_id: GUID          -- 关联 feedbacks 表

  arbiter_id: GUID

  status: "passed" | "failed" | "force_skipped"

  result: json               -- 审查结果，因 feedback type 而异
  -- completion 类型结构：
  --   {"evidence_check": "pass"|"fail", "missing": string[], "can_auto_done": boolean}
  -- blocked 类型结构：
  --   {"block_confirmed": boolean, "suggest_swap": boolean, "reason": string}

  reviewed_at: timestamp
  created_at: timestamp
  updated_at: timestamp
}
```

---

### 2.7 feedbacks（反馈表）

BriefChain 是正式沟通渠道，闲聊用其他 IM，沟通完再总结成 feedback 发出。

feedbacks 发出后也要经过 Arbiter 审查（2.6）。

```sql
feedbacks {
  id: GUID
  brief_id: GUID
  brief_version: number      -- 关联的 brief 版本

  type: "blocked" | "progress" | "completion"
  is_auto_generated: boolean -- true = LLM 汇总 children 完成情况生成，需人工确认

  content: string             -- 反馈内容，completion 里包含 evidence 描述
  attachments: json           -- [{name, url, type}]

  from_user: GUID             -- 发出反馈的人（通常是 downstream）
  created_at: timestamp
  confirmed_at: timestamp | null  -- 人工确认时间（is_auto_generated=true 时）
  updated_at: timestamp
}
```

**汇总 feedback 机制：**
- 某 brief 的所有 children 全部 done → 自动触发 LLM 汇总所有 children 的 completion feedback
- 生成草稿 → 当前 downstream 确认/修改 → 作为一条 feedback 发给 parent brief 的 upstream
- 这条 feedback 也要走 Arbiter 审查（关联 feedback_arbiter_reviews）
- 最终 root brief 收到总 feedback

---

### 2.8 内部状态相关表（待设计）

使用方自己的工作进度管理，不阻塞跨人转移，支持自定义模板。

- `internal_status_templates`（模板表）
- `internal_statuses`（模板内状态定义）
- `brief_internal_status_log`（实际使用记录）

## 3. 已完成

- [x] briefs 实体表设计（2.1）
- [x] brief_versions 版本表设计（2.2）
- [x] brief_transfer_history 流转记录表设计（2.3）
- [x] brief_chains 链元数据表设计（2.4）
- [x] brief_arbiter_reviews Brief 审查表设计（2.5）
- [x] feedback_arbiter_reviews Feedback 审查表设计（2.6）
- [x] feedbacks 反馈表设计（2.7）
- [x] 状态机定义（第 1 章）
- [x] 汇总 feedback 机制设计（2.7）

## 4. 待讨论（暂缓）

- [ ] 内部状态相关表的完整设计（2.8）
- [ ] Arbiter 审查的具体维度（LLM prompt / 评分标准）
- [ ] MVP 范围定义（哪些表先不做）
- [ ] 跨系统互操作协议设计（`bc://` 协议）
