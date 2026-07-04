# BriefChain Task & Kanban 设计文档

> 版本：MVP v0.1
> 最后更新：2026-07-04

---

## 设计原则

- **Brief = 跨团队合约，Task = 团队内部执行**。两层独立，通过 `brief_id` 关联
- **Task 操作轻快**：Kanban 拖拽流转，无 Arbiter 审查，无 feedbacks 通知
- **Task 与 Kanban 完全解耦**：task 只存 `status`，不存任何 kanban 引用。看板通过 owner 划定 task 范围，再按模板的列映射渲染
- **模板模式**：`simple`（kanban_template_columns 自定义列名/颜色，每个 status 对应一列）、`customized`（多列映射同 status，未来）
- **全局默认模板**：DB migration 时 seed `kanban_template_id=1`（`name="默认模板"`、`mode="simple"`、`is_public=true`、`created_by=null`），新用户/新团队注册时自动引用
- **看板实例（kanbans）**：团队/个人的实际看板，引用模板 + 个性化配置（泳道、done 过滤）
- **低迁移成本**：概念对齐传统项目管理工具，上手无痛
- **Task done ≠ Brief 自动完成**：团队自行判断，手动在 Brief 详情页提交
- **Task 软删除替代 cancelled**：`is_deleted` + `deleted_at` + `deleted_by`，无需额外的 cancelled 状态
- **Kanban_template 只是为了分享**：kanban 引用 template，template 修改通过 `PUT /kanbans/:kanban_id/columns` 走后端 fork 判断——若 `created_by ≠ 当前用户`，则自动新建私有模板并更新 kanban 引用；否则直接修改原模板
- **Kanban_template 与 kanban 关系**：用户一般只需要关心操作 kanban 配置，后台服务自动处理 kanban_templates，除了主动维护比如删除
---

## 1. 概念分层

```
┌─────────────────────────────────────┐
│ Brief 层（跨团队合约）               │
│ 粗粒度状态 · Arbiter 审查 · 详情页操作 │
│ upstream_state + downstream_state    │
└────────────┬────────────────────────┘
             │ 1 : N（brief_id 外键）
┌────────────▼────────────────────────┐
│ Task 层（团队内 Kanban）             │
│ 细粒度流程 · 拖拽流转 · 无审查        │
│ 完全解耦 kanban，只看 status          │
└─────────────────────────────────────┘

┌──────────┐  引用  ┌───────────────────┐
│ kanban_   │◄──────│ kanbans            │
│ templates │       │（团队/个人看板实例） │
│（列映射） │       │ 泳道、done 过滤等   │
└──────────┘       └───────────────────┘
```

| | Brief 层 | Task 层 | Kanban 层 |
|---|---|---|---|
| 边界 | 跨团队 | 团队内 / 个人 | 视图配置 |
| 操作方式 | 详情页按钮 + 确认表单 | Kanban 拖拽 | 配置页 |
| 状态变更 | 写原因，经 feedbacks 通知 | 轻快随意 | 改列名/颜色不影响 task |
| 审查 | Arbiter 审查 | 无 | 无 |
| ID 类型 | GUID（跨系统） | int（自增） | int（自增） |

---

## 2. 数据库设计

### 2.1 tasks

```
tasks {
  task_id: int (auto-increment)          -- 主键
  brief_id: GUID | null                   -- 外键 → briefs.brief_id（Bug 可为 null）
  parent_task_id: int | null              -- 外键 → tasks.task_id（子任务）
  team_id: GUID | null                    -- 所属团队，null = 私人 task（仅用户可见）

  type: enum                              -- "task" | "bug" | "sub_task"

  title: string
  content: string | null                  -- 链接直接写内容里，无 attachments 字段

  status: enum                            -- "backlog" | "todo" | "in_progress" | "in_review" | "done"
  priority: enum                          -- "p0" | "p1" | "p2" | "p3"

  created_by: GUID
  created_by_name: string                 -- 冗余快照

  assignee_id: GUID | null
  assignee_name: string | null             -- 冗余快照

  estimated_hours: int | null
  actual_hours: int | null
  due_date: timestamp | null

  status_changed_by: GUID | null          -- 最后变更状态的用户
  status_changed_at: timestamp | null     -- 最后变更状态的时间

  is_deleted: boolean (default false)     -- 软删除标记
  deleted_by: GUID | null                 -- 被谁删除
  deleted_at: timestamp | null            -- 删除时间

  created_at: timestamp
  updated_at: timestamp
}
```

**task 和 kanban 完全解耦** — 看板通过 owner（team_id / assignee_id）划定 task 范围，再按模板列映射渲染。

#### 字段说明

| 字段 | 说明                                                    |
|---|-------------------------------------------------------|
| `team_id` | 所属团队。null 表示私人 task，仅用户可见                             |
| `status` | 全局 task 状态。取值见下表。拖拽 / API PUT 时更新                     |
| `status_changed_by` / `status_changed_at` | 最近一次 status 变更人与时间|
| `content` | 无 `attachments` 字段，链接直接贴内容里                           |
| `is_deleted` / `deleted_at` | 软删除。软删除替代 cancelled，所有查询默认 `WHERE is_deleted = false` |

#### status 取值

| status | 含义 | 看板显示 | 统计用途 |
|---|---|---|---|
| `backlog` | 待排期 | 不显示（Brief 拆分后直接进 todo） | 不计入 |
| `todo` | 未开始 | 显示 | 积压量 |
| `in_progress` | 进行中（别催） | 显示 | 在途量、人均并行数 |
| `in_review` | 审查中 | 显示 | 阻塞率 |
| `done` | 完成 | 显示（按 kanbans.done_visible_days 过滤） | 吞吐量、流速 |

> `backlog` 可以不用，在 Brief 拆分后直接进 `todo`，默认隐藏

#### type 约束

| type | brief_id | parent_task_id | 进 Kanban |
|---|---|---|---|
| `task` | **required** | null | ✅ |
| `bug` | 可选 | null | ✅ |
| `sub_task` | via parent | **required** | ❌ |

### 2.2 kanban_templates

> 纯列映射模板，字段极少。被 kanbans 引用。共享的是模板（列映射），个性化配置在 kanbans。
> 全局默认模板 `kanban_template_id=1` 在 DB migration 时 seed。

```
kanban_templates {
  kanban_template_id: int (auto-increment)  -- 主键（id=1 是全局默认模板）

  name: string                              -- "默认模板" / "研发看板模板"
  kanban_template_mode: enum                -- "simple" | "customized"

  created_by: GUID | null                   -- null = 系统预置

  is_public: boolean (default false)        -- 能被其他人引用

  created_at: timestamp
  updated_at: timestamp
}
```

#### 两种模式

| mode | kanban_template_columns 表 | task_columns 表 | column = status 关系 | MVP |
|---|---|---|---|---|
| `simple` | **有记录**（名字、颜色、隐藏） | 无 | 每个 status 对应一列（1:1），列名可自定义 | ✅ |
| `customized` | 有记录 | **有记录** | 一个 status 可对应多列（1:N） | ❌ 未来 |

> `simple` 模式：kanban_template_columns 存列名、颜色、隐藏标记，前端直接用后端返回的列名渲染。
> 全局默认模板 `kanban_template_id=1` 是 simple 模式，DB seed 时写入 5 条 `kanban_template_columns`。

#### 修改时的 fork 规则

修改 kanban 的列配置（`PUT /kanbans/:kanban_id/columns`）时，后端判断：

```
IF kanban_template.created_by ≠ JWT.user_id:
    → 新建私有 kanban_template（复制当前列配置，is_public=false）
    → 更新 kanbans.kanban_template_id → 新模板
    → 在新模板上应用列修改
ELSE:
    → 直接修改当前 kanban_template 的 columns
```

> 规则：公版/他人模板不可直接修改，列变更自动产生私有副本。`is_public=true` 且 `created_by=JWT.user_id` 是例外（自己分享的模板可直接改）。

### 2.3 kanbans

> 看板实例——团队或个人的实际看板。引用一个模板获取列映射，并存储个性化配置。

```
kanbans {
  kanban_id: int (auto-increment)           -- 主键
  kanban_template_id: int                   -- 外键 → kanban_templates（默认=1）
  kanban_template_mode: enum                -- "simple" | "customized"，冗余列（避免读 kanban_templates）

  name: string                              -- 可以改名
  owner_type: enum                          -- "user" | "team"
  owner_id: GUID                            -- user_id 或 team_id

  -- 个性化配置
  group: enum                               -- "none" | "priority" | "assignee" | "brief"
  done_visible_days: int (default 14)       -- done 列任务停留天数
  is_default: boolean (default false)       -- 该 owner 的默认看板
  
  created_at: timestamp
  updated_at: timestamp
}
```

#### kanbans 与 kanban_templates 的关系

- `kanbans` 引用 `kanban_templates`——一个模板可被多个看板共用（共享模板）
- `kanban_templates` 定义"有哪些列、列名叫什么"（列映射），是共享的；非共享状态，kanban 和 template 一一对应
- `kanbans` 存储"泳道、done 过滤天数"等个性化配置，是私有的
- `kanban_templates` 纯粹为了共享而设计，一般会被包含在 kanban 的 api 中
- 一个人/团队可以有多个看板（未来），但只有一个 `is_default = true`，MVP只有一个
- 列配置修改通过 `PUT /kanbans/:kanban_id/columns` 走后端 fork 判断（见 2.2 修改时的 fork 规则）

#### 初始化规则

| 时机 | 操作 |
|---|---|
| 用户注册 | 创建 kanbans（owner_type=user，kanban_template_id=1，group=none，done_visible_days=14） |
| 团队创建 | 创建 kanbans（owner_type=team，kanban_template_id=1，group=none，done_visible_days=14） |

> 全局默认模板 `kanban_template_id=1` 在 DB migration 时作为 seed data 写入，含 5 条 `kanban_template_columns`。

### 2.4 kanban_template_columns

> simple 和 customized 模式下列定义。全局默认模板的列在 DB migration 时 seed。

```
kanban_template_columns {
  column_id: int (auto-increment)           -- 主键
  kanban_template_id: int                   -- 外键 → kanban_templates

  status_key: string                        -- 映射到 tasks.status："todo" | "in_progress" 等
  name: string                              -- 列显示名："待办" / "开发中"
  color: string | null                      -- 列头颜色标识
  is_hidden: boolean (default false)        -- 在看板上隐藏（如 backlog 列）
  position: int                             -- 从左到右排列顺序（如果一个 status 对应多个column，默认到第一个position）

  created_at: timestamp
}
```

> **约束**：simple 模式下，每个 `status_key` 在同一个 template 内只能有一条记录（1:1 映射）。由应用层保证。

#### 默认列（全局默认模板 kanban_template_id=1 的 seed data）

| status_key | name | position | is_hidden |
|---|---|---|---|
| `backlog` | Backlog | 0 | **true** |
| `todo` | Todo | 1 | false |
| `in_progress` | In Progress | 2 | false |
| `in_review` | In Review | 3 | false |
| `done` | Done | 4 | false |

### 2.5 task_comments

```
task_comments {
  id: int (auto-increment)          -- 主键
  task_id: int                      -- 外键 → tasks.task_id

  content: string

  created_by: GUID
  created_by_name: string           -- 冗余快照
  created_at: timestamp
  updated_at: timestamp
}
```

极简评论：无 type、无 Arbiter、无方向区分。后续 brief 需要 comment 时表结构直接复用。

---

## 3. Kanban 看板规则

### 3.1 两层查询模型

```
第 1 层 — 查找看板配置：

  个人看板：kanbans WHERE owner_type='user' AND owner_id=:user_id AND is_default=true
  团队看板：kanbans WHERE owner_type='team' AND owner_id=:team_id AND is_default=true

第 2 层 — 获取列映射：

  kanban_template_columns WHERE kanban_template_id = kanbans.kanban_template_id
                  ORDER BY position

第 3 层 — 划定 task 范围：

  个人看板：tasks WHERE assignee_id = :assignee_id AND type IN ('task', 'bug') AND is_deleted = false
  团队看板：tasks WHERE team_id = :team_id AND type IN ('task', 'bug') AND is_deleted = false

第 4 层 — 按列映射渲染：

  每个 task.status → 匹配 kanban_template_columns.status_key → 放入对应列
  is_hidden=true 的列不渲染（如 backlog，可以点开）
  done 列按 done_visible_days 过滤
```

> task 完全不知道自己在哪个看板、哪一列。看板是纯视图层计算。

### 3.2 显示规则

- 非 done、非 hidden 的 task 全部显示
- `backlog` 列 is_hidden = true，默认折叠
- `done` 列 task 按 `kanbans.done_visible_days` 过滤（超时折叠）
- 软删除 task 不显示（`is_deleted = false`）
- Bug 可不挂 Brief，直接出现在看板上

### 3.3 泳道分组

根据 `kanbans.group` 动态分组：

```
group=none     → swimlanes = [{swimlane_key: null, tasks: [...]}]
group=assignee → swimlanes = [{swimlane_key: "李四", tasks: [...]}, ...]
group=priority → swimlanes = [{swimlane_key: "p0", tasks: [...]}, ...]
group=brief    → swimlanes = [{swimlane_key: "优化首页加载", tasks: [...]}, ...]
```

> 泳道存 kanbans 配置，查询时动态计算，不写入 task。与传统项目管理工具一致。

### 3.4 拖拽行为

| 拖拽操作 | 后端写什么 |
|---|---|
| task 拖到另一列 | 更新 `tasks.status`、`status_changed_by`、`status_changed_at` |
| task 拖到另一泳道（group=assignee） | 更新 `tasks.assignee_id` + `tasks.status` |

> 拖拽更改 task 自身字段，也会更改 column。

### 3.5 Task 完成 ≠ Brief 自动完成

- 所有关联 task done → **不自动触发** Brief submit
- 团队自行判断验收是否通过，手动在 Brief 详情页点「提交完成」
- Brief 被 approve → done，关联 task 不做自动处理

---

## 4. MVP 范围

### 4.1 MVP 做

- [x] tasks / kanban_templates / kanbans / kanban_template_columns / task_comments 表
- [x] DB seed：全局默认模板 `kanban_template_id=1`（simple 模式，5 列）
- [x] 用户注册时自动初始化个人看板（kanbans，kanban_template_id=1）
- [x] 团队创建时自动初始化团队看板（kanbans，kanban_template_id=1）
- [x] Task CRUD API
- [x] Kanban 查询 API（个人，simple 模式，单泳道 group=none）
- [x] 拖拽 → status 变更 API
- [x] Task comment CRUD
- [x] Kanban 配置 API（修改 kanbans 的 group / done_visible_days / kanban_template_id）
- [x] Kanban 列管理 API（`PUT /kanbans/:kanban_id/columns`，后端走 fork 逻辑）

### 4.2 MVP 不做

- ❌ `customized` 模式（多列映射同 status + task_columns 表）
- ❌ 泳道前端 UI（后端支持 group=assignee/brief/priority，前端暂不渲染）
- ❌ 自建模板 / 自建看板（只用默认模板和默认看板）
- ❌ 统计类 API（进度报表、工时汇总等）
- ❌ 批量操作 API（批量改 status/assignee/priority）
- ❌ Task 与 Brief 自动联动
- ❌ 看板筛选器（按人 / 优先级 / 到期日过滤）
- ❌ 团队看板查询（`GET /kanban/team/:team_id`）

---

## 附录 A：与传统项目管理工具的迁移对照

| 传统工具概念 | BriefChain 概念 | 差异                                     |
|---|---|----------------------------------------|
| Epic | 根 Brief | BriefChain 的根 Brief 是合约实体，不仅是分类标签      |
| Story / Issue | 子 Brief（合约）+ Task（执行） | 传统工具 Issue 同时承担两种角色，BriefChain 拆成两层    |
| Board | kanbans（看板实例） | 传统工具 Board 是视图，BriefChain 的 kanbans 也是 |
| Board Column | kanban_template_columns | 一致，列名/颜色可自定义                           |
| Column Mapping | kanban_templates（模板） | 传统工具在工作流中配置，BriefChain 抽成独立模板实体        |
| Issue Status | tasks.status | 概念对齐，5 个枚举值                            |
| Sub-task | sub_task (type) | 一致，不进 Board                            |
| Bug | bug (type) | 一致，可独立可关联                              |
| Swimlane | kanbans.group（视图） | 传统工具存在 Board Config 不存 Issue，一致        |
| Assignee | assignee_id | 一致                                     |
| Sprint | **暂无** | MVP 不做迭代管理                             |

---

## 附录 B：冗余字段对照表

| 表 | 冗余字段 | 来源 | 写入时机  |
|---|---|---|-------|
| tasks | assignee_name | users.name | 分配/拖拽时 |
| tasks | created_by_name | users.name | 创建时   |
| tasks | status_changed_by | JWT user_id | status 变更时 |
| task_comments | created_by_name | users.name | 创建时   |

> 合约语义：名字是操作时的快照，用户改名不自动同步。

---

## 附录 C：customized 模式预留设计

> MVP 不实现，此处仅记录设计方向，确保 simple 模式能平滑升级。

### 新增表：task_columns

```
task_columns {
  task_id: int                        -- 外键 → tasks.task_id
  column_id: int                      -- 外键 → kanban_template_columns.column_id
  column_position: int (default 0)    -- 同列内排序（默认不设置，按某些规则排序）
}
```

### 设计规则

- 一个 status 可对应多个 kanban_template_columns（1:N 映射）
- 每个 status 必须有一个 `is_default = true` 的 kanban_template_columns 记录
- task.status 变更时，自动落入该 status 的默认 column
- 查询时：先查 task，再 LEFT JOIN task_columns 获取列名（非simple mode）

---

## 附录 D：相关文档

- [00-overview.md](00-overview.md) — 总入口，概念分层
- [01-brief-feedback-design.md](01-brief-feedback-design.md) — Brief 双状态模型
- [03-api-design.md](03-api-design.md) — Brief API 设计
- [07-task-kanban-api-design.md](07-task-kanban-api-design.md) — Task / Kanban API 设计
