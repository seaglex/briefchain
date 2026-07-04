# BriefChain Task & Kanban REST API 设计文档

> 版本：MVP v0.1
> 最后更新：2026-07-04
> 基础路径：`/api/v1`
> 配套设计文档：[06-task-kanban-design.md](06-task-kanban-design.md)

---

## 设计原则

- **JWT 认证**：登录后所有请求带 `Authorization: Bearer <token>`
- **user_id 解析**：所有 Task / Comment 读写操作，后端从 JWT 解析 `user_id`，校验操作权限。前端不传 user_id
- **权限模型（MVP）**：`created_by` 全权限；`assignee_id` 可变更状态；`team_id` 非 null 时团队管理员有全权限
- **状态码**：标准 HTTP 状态码，错误返回统一格式
- **分页**：游标分页（cursor-based），避免 offset 性能问题
- **冗余存储人名**：tasks / task_comments 表冗余存储用户名字（name 快照），列表查询无需 JOIN users
- **轻量操作**：Task 操作无 Arbiter 审查，无 feedbacks 通知，与 Brief 子系统解耦
- **Task 与 Kanban 完全解耦**：task 只存 `status`，无 kanban 引用。看板查询时动态计算列归属

---

## 统一错误格式

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task 不存在或无权限访问",
    "details": {}
  }
}
```

---

## 1. Kanban 看板查询（`/kanban`）

> 看板查询分个人看板和团队看板。先查 kanbans 获取配置，再查 tasks 获取数据，按 kanban_template_columns 列映射渲染。

### 1.1 获取个人看板

`GET /kanban/personal?group=:group`

查询参数：
- `group` — 泳道分组方式：`none` / `assignee` / `brief` / `priority`（可选，默认 `none`；未传时使用 kanbans 存储的 group）

```json
// Response 200
{
  "kanban": {
    "kanban_id": 1,
    "kanban_template_id": 1,
    "kanban_template_mode": "simple",
    "group": "none",
    "done_visible_days": 14,
    "is_default": true
  },
  "columns": [
    {
      "column_id": 2,
      "status_key": "todo",
      "name": "待办",
      "color": "#3498db",
      "is_hidden": false,
      "position": 1,
      "swimlanes": [
        {
          "swimlane_key": null,
          "tasks": [
            {
              "task_id": 1,
              "type": "task",
              "title": "设计数据库 schema",
              "status": "todo",
              "priority": "p1",
              "assignee_id": null,
              "assignee_name": null,
              "brief_id": "guid",
              "brief_title": "优化首页加载速度",
              "estimated_hours": 4,
              "actual_hours": null,
              "due_date": null,
              "updated_at": "2026-07-02T01:00:00Z"
            }
          ]
        }
      ]
    },
    {
      "column_id": 3,
      "status_key": "in_progress",
      "name": "进行中",
      "color": "#e67e22",
      "is_hidden": false,
      "position": 2,
      "swimlanes": [ ... ]
    },
    {
      "column_id": 4,
      "status_key": "in_review",
      "name": "审查中",
      "color": "#9b59b6",
      "is_hidden": false,
      "position": 3,
      "swimlanes": [ ... ]
    },
    {
      "column_id": 5,
      "status_key": "done",
      "name": "已完成",
      "color": "#27ae60",
      "is_hidden": false,
      "position": 4,
      "swimlanes": [ ... ]
    }
  ]
}
```

> **查询逻辑（后端）：**
> ```
> 1. 查个人看板配置：
>    kanbans WHERE owner_type='user' AND owner_id=JWT.user_id AND is_default=true
>
> 2. 查列映射（simple 模式）：
>    kanban_template_columns WHERE kanban_template_id = kanbans.kanban_template_id
>                   AND is_hidden = false
>                   ORDER BY position
>
> 3. 查 tasks（task 和 kanban 完全解耦，不按 kanban 过滤）：
>    WHERE team_id IS NULL
>      AND is_deleted = false
>      AND type IN ('task', 'bug')
>      AND status IN (步骤 2 的 status_key 列表)
>      AND (status != 'done'
>           OR (status = 'done' AND updated_at >= NOW() - 模板.done_visible_days))
>
> 4. 按 kanban_template_columns.status_key 分组 task → 每个 status 一列
>
> 5. 按 kanbans.group 做泳道二次分组
> ```

> **task 对象无 kanban 字段**：task 响应中不含 `kanban_template_id`、`column_id` 等字段。task 只关心自己的 `status`，在哪个看板显示由看板查询动态决定。

### 1.2 获取团队看板(MVP 不实现)

`GET /kanban/team/:team_id?group=:group`

查询参数：
- `team_id` — 团队 ID（路径参数）
- `group` — 泳道分组方式（可选，默认使用 kanbans 存储的 group）

```json
// Response 200（结构同 1.1）
{
  "kanban": { ... },
  "columns": [ ... ]
}
```

> **查询逻辑（后端）：**
> ```
> 1. 查团队看板配置：
>    kanbans WHERE owner_type='team' AND owner_id=:team_id AND is_default=true
>
> 2. 同个人看板步骤 2
>
> 3. 查 tasks：
>    WHERE team_id = :team_id
>      AND is_deleted = false
>      AND type IN ('task', 'bug')
>      ...
>
> 4-5. 同个人看板
> ```

---

## 2. Task CRUD（`/tasks`）

### 2.1 创建 Task

`POST /tasks`

```json
// Request
{
  "brief_id": "guid",              // 可选，type=task 时建议提供，type=bug 时可 null
  "type": "task",                  // 必填："task" | "bug" | "sub_task"
  "parent_task_id": null,          // 可选，type=sub_task 时必填
  "team_id": "guid",               // 可选，null = 私人 task

  "title": "设计数据库 schema",
  "content": "需要包含 users / tasks / briefs 三张表，参考 [[设计文档]](url)",

  "status": "todo",                 // 可选，默认 "todo"。从看板列 head 新建时传对应列的 status
  "priority": "p1",               // 可选，默认 p2
  "assignee_id": "guid",          // 可选，未分配为 null
  "estimated_hours": 4,           // 可选
  "due_date": "2026-07-05T00:00:00Z"  // 可选
}

// Response 201
{
  "task": {
    "task_id": 1,
    "brief_id": "guid",
    "parent_task_id": null,
    "team_id": "guid",

    "type": "task",
    "title": "设计数据库 schema",
    "content": "需要包含 users / tasks / briefs 三张表，参考 [[设计文档]](url)",

    "status": "todo",
    "priority": "p1",

    "assignee_id": "guid",
    "assignee_name": "李四",

    "estimated_hours": 4,
    "actual_hours": null,
    "due_date": "2026-07-05T00:00:00Z",

    "status_changed_by": null,
    "status_changed_at": null,

    "created_by": "guid",
    "created_by_name": "张三",
    "created_at": "2026-07-02T01:00:00Z",
    "updated_at": "2026-07-02T01:00:00Z",

    "is_deleted": false,
    "deleted_by": null,
    "deleted_at": null
  }
}
```

> **校验规则：**
> - `type=task` → `brief_id` 可选
> - `type=bug` → `brief_id` 可选（可为 null）
> - `type=sub_task` → `parent_task_id` 必填
> - `team_id` 非 null → team 必须存在
> - 默认 `status = "todo"`，从看板列 head 新建时可指定（如 `"in_progress"`）
> - `created_by` / `created_by_name` 从 JWT 解析并冗余存储
> - 传入 `status` 时同时写入 `status_changed_by` / `status_changed_at`

### 2.2 列表查询 Task

`GET /tasks?brief_id=:brief_id&type=task&status=todo&team_id=:team_id&page_cursor=abc&page_size=20`

查询参数：
- `brief_id` — 过滤关联 Brief
- `type` — 过滤类型
- `status` — 过滤状态
- `team_id` — 过滤团队
- `assignee_id` — 过滤执行人
- `priority` — 过滤优先级
- `page_cursor` — 分页游标
- `page_size` — 每页数量，默认 20

```json
// Response 200
{
  "tasks": [
    {
      "task_id": 1,
      "type": "task",
      "title": "设计数据库 schema",
      "status": "todo",
      "priority": "p1",
      "assignee_id": "guid",
      "assignee_name": "李四",
      "brief_id": "guid",
      "updated_at": "2026-07-02T01:00:00Z"
    }
  ],
  "next_cursor": "next_page_token_or_null"
}
```

> 列表模式：不包含 `content` 字段，减少响应大小。

### 2.3 获取单个 Task（详情模式）

`GET /tasks/:task_id`

```json
// Response 200
{
  "task": {
    "task_id": 1,
    "brief_id": "guid",
    "parent_task_id": null,
    "team_id": "guid",

    "type": "task",
    "title": "设计数据库 schema",
    "content": "需要包含 users / tasks / briefs 三张表，参考 [[设计文档]](url)",

    "status": "todo",
    "priority": "p1",

    "assignee_id": "guid",
    "assignee_name": "李四",

    "estimated_hours": 4,
    "actual_hours": null,
    "due_date": "2026-07-05T00:00:00Z",

    "status_changed_by": null,
    "status_changed_at": null,

    "created_by": "guid",
    "created_by_name": "张三",
    "created_at": "2026-07-02T01:00:00Z",
    "updated_at": "2026-07-02T01:00:00Z",

    "is_deleted": false,
    "deleted_by": null,
    "deleted_at": null
  },
  "sub_tasks": [ ... ],
  "comments": [ ... ]
}
```

> `sub_tasks` 使用列表模式（不包含 content），`comments` 只返回最新 5 条。

### 2.4 更新 Task

`PUT /tasks/:task_id`

```json
// Request（只传需要更新的字段）
{
  "title": "新标题",              // 可选
  "content": "更新后的内容",      // 可选
  "status": "in_progress",       // 可选：直接改状态（不走拖拽）
  "priority": "p0",              // 可选
  "assignee_id": "guid",         // 可选
  "estimated_hours": 8,          // 可选
  "actual_hours": 3,             // 可选
  "due_date": "2026-07-10T00:00:00Z"  // 可选
}

// Response 200
{
  "task": { ... }  // 完整 task 对象（详情模式）
}
```

> **校验规则：**
> - user_id 从 JWT 解析
> - 操作人必须是 `created_by` 或 `assignee_id`（MVP 简化权限）
> - 更新 `status` 时，同时更新 `status_changed_by` / `status_changed_at`
> - 更新 `assignee_id` 时，自动更新 `assignee_name`（冗余快照）

### 2.5 拖拽 Task（变更状态）

`PUT /tasks/:task_id/drag`

```json
// Request
{
  "kanban": {
    "kanban_id": 1,
    "kanban_template_id": 1,
    "kanban_template_mode": "simple",
    "group": "none",
  },                              // 给 kanban 信息，方便同时处理 task 和 task_columns 关系
  "status": "in_progress",        // 目标状态
  "column_id": 1,                 // 目标column
  "position": null                // 在目标列中的排序位置（MVP 不更新）
}

// Response 200
{
  "task": {
    "task_id": 1,
    "status": "in_progress",
    "status_changed_by": "guid",
    "status_changed_at": "2026-07-02T02:00:00Z",
    ...
  },
  "message": "Task 已移动到 进行中"
}
```

> **校验规则：**
> - user_id 从 JWT 解析，抽取方法校验权限 （目前是`assignee_id` 或 `created_by`）
> - `status` 必须是有效枚举值
> - 后端写入 `status_changed_by`（JWT user_id）和 `status_changed_at`（NOW()）
> - 如果拖拽同时变更了泳道（如 group=assignee 时拖到别人的泳道），前端额外传 `assignee_id`：
>   ```
>   { "status": "in_progress", "assignee_id": "guid" }
>   ```

### 2.6 删除 Task（软删除）

`DELETE /tasks/:task_id`

```
Response 204
```

> **校验规则：**
> - user_id 从 JWT 解析，校验 = `created_by`
> - 软删除：设置 `is_deleted = true`、`deleted_at = NOW()`、`deleted_by = JWT.user_id`
> - 级联软删除所有 `parent_task_id = 该 task` 的 sub_task
> - 级联软删除所有关联的 task_comments

---

## 3. Task Comments（`/tasks/:task_id/comments`）

### 3.1 列出 Comments

`GET /tasks/:task_id/comments?page_cursor=abc&page_size=20`

```json
// Response 200
{
  "comments": [
    {
      "id": 1,
      "content": "已完成 users 表设计",
      "created_by": "guid",
      "created_by_name": "李四",
      "created_at": "2026-07-02T01:30:00Z",
      "updated_at": "2026-07-02T01:30:00Z"
    }
  ],
  "next_cursor": null
}
```

### 3.2 创建 Comment

`POST /tasks/:task_id/comments`

```json
// Request
{
  "content": "已完成 users 表设计"
}

// Response 201
{
  "comment": {
    "id": 1,
    "content": "已完成 users 表设计",
    "created_by": "guid",
    "created_by_name": "李四",
    "created_at": "2026-07-02T01:30:00Z",
    "updated_at": "2026-07-02T01:30:00Z"
  }
}
```

> `created_by` / `created_by_name` 从 JWT 解析

### 3.3 更新 Comment

`PUT /comments/:comment_id`

```json
// Request
{
  "content": "已完成 users 表设计，待 review"
}

// Response 200
{
  "comment": { ... }
}
```

> 校验：`created_by` = JWT user_id

### 3.4 删除 Comment

`DELETE /comments/:comment_id`

```
Response 204
```

> 校验：`created_by` = JWT user_id

---

## 4. Kanban 配置

### 4.1 获取看板配置

`GET /kanbans/:kanban_id`

```json
// Response 200
{
  "kanban": {
    "kanban_id": 1,
    "kanban_template_id": 1,
    "name": "XX的kanban",
    "owner_type": "user",
    "owner_id": "guid",
    "group": "none",
    "done_visible_days": 14,
    "is_default": true,
    "created_at": "2026-07-02T00:00:00Z",
    "updated_at": "2026-07-02T00:00:00Z"
  },
  "template": {
    "kanban_template_id": 1,
    "name": "默认模板",
    "kanban_template_mode": "simple",
    "created_by": "guid" 
  },
  "columns": [
    {
      "column_id": 1,
      "status_key": "backlog",
      "name": "Backlog",
      "color": null,
      "is_hidden": true,
      "position": 0
    },
    {
      "column_id": 2,
      "status_key": "todo",
      "name": "待办",
      "color": "#3498db",
      "is_hidden": false,
      "position": 1
    },
    { ... }
  ]
}
```

> 校验：个人看板 → JWT user_id = owner_id；团队看板 → 操作人是团队成员

### 4.2 更新看板个性化配置

`PUT /kanbans/:kanban_id`

```json
// Request
{
  "name": "xx's kanban",          // 可选：切换名字
  "kanban_template_id": 2,        // 可选：切换看板使用的模板
  "group": "assignee",           // 可选：切换泳道分组方式
  "done_visible_days": 30        // 可选：调整 done 列任务保留天数
}

// Response 200
{
  "kanban": { ... },
  "columns": [ ... ]             // 切换模板时返回新模板的列配置
}
```

> 校验：个人看板 → JWT user_id = owner_id；团队看板 → 操作人是团队管理员
> 可更新字段：`kanban_template_id` / `group` / `done_visible_days` / `name`
> 切换 `kanban_template_id` 时同步更新 `kanban_template_mode`（冗余字段）

---

## 5. Kanban 列管理

> 列配置通过 `PUT /kanbans/:kanban_id/columns` 修改。**前端不直接操作 `kanban_template_columns`**——后端统一处理 fork 判断。
> 前端在配置页编辑列名/颜色/隐藏后，点「保存」发送完整列配置。后端对比变化，决定直接修改原模板还是 fork 新模板。

### 5.1 更新看板列配置

`PUT /kanbans/:kanban_id/columns`

```json
// Request（完整列配置）
{
  "name": "",
  "kanban_template_mode": "simple",
  "is_public": false,
  "columns": [
    { "column_id": 2, "status_key": "todo",    "name": "待办事项", "color": "#3498db", "is_hidden": false, "position": 1 },
    { "column_id": 3, "status_key": "in_progress", "name": "开发中", "color": "#e67e22", "is_hidden": false, "position": 2 },
    { "column_id": 4, "status_key": "in_review", "name": "审阅中", "color": "#9b59b6", "is_hidden": false, "position": 3 },
    { "column_id": null, "status_key": "done",    "name": "已完成", "color": "#27ae60", "is_hidden": false, "position": 4 }
  ]
}  // column_id = null，说明是新建 column

// Response 200
{
  "kanban": {
    "kanban_id": 1,
    "kanban_template_id": 10,       // 可能变了（fork 了新模板）
    "kanban_template_mode": "simple",
    ...
  },
  "columns": [
    { "column_id": 100, "status_key": "todo", "name": "待办事项", "color": "#3498db", "is_hidden": false, "position": 1 },
    { "column_id": 101, "status_key": "in_progress", "name": "开发中", "color": "#e67e22", "is_hidden": false, "position": 2 },
    { "column_id": 102, "status_key": "in_review", "name": "审阅中", "color": "#9b59b6", "is_hidden": false, "position": 3 },
    { "column_id": 103, "status_key": "done", "name": "已完成", "color": "#27ae60", "is_hidden": false, "position": 4 }
  ]
}
```

> **后端处理逻辑：**
> ```
> 1. 查 kanbans.kanban_template_id → 获取当前模板
> 2. IF template.created_by ≠ JWT.user_id:
>       → 新建私有 kanban_template（复制当前列配置，is_public=false）
>       → 更新 kanbans.kanban_template_id → 新模板
> 3. 对比传来了 columns 和当前 columns，只更新有变化的字段
> 4. 返回更新后的 kanban + columns
> ```
>
> **校验规则：**
> - 个人看板 → JWT user_id = owner_id；团队看板 → 操作人是团队管理员
> - `column_id` 必须属于当前 kanban 的模板
> - `status_key` 不可改（simple 模式 1:1 映射）
> - `position` 不可改（simple 模式 position 由 status_key 顺序决定）
>
> **注意**：响应中的 `kanban_template_id` 和 `column_id` 可能已变化（fork 了新模板），前端需用响应数据更新本地状态。

---

## 6. Kanban 模板管理（`/kanban-templates`）

> 模板是列映射的共享实体。用户在配置页选择模板、预览列、保存为公开模板。

### 6.1 列出公开模板

`GET /kanban-templates?page_cursor=abc&page_size=20`

```json
// Response 200
{
  "templates": [
    {
      "kanban_template_id": 1,
      "name": "默认模板",
      "kanban_template_mode": "simple",
      "created_by": "guid",
      "created_by_name": "系统",
      "is_public": true,
      "created_at": "2026-07-01T00:00:00Z",
      "updated_at": "2026-07-01T00:00:00Z"
    },
    {
      "kanban_template_id": 3,
      "name": "研发看板",
      "kanban_template_mode": "simple",
      "created_by": "guid",
      "created_by_name": "张三",
      "is_public": true,
      "created_at": "2026-07-02T00:00:00Z",
      "updated_at": "2026-07-02T00:00:00Z"
    }
  ],
  "next_cursor": null
}
```

> 查询条件：`is_public = true`，或 `created_by = JWT.user_id`（自己的私有模板也可见）

### 6.2 获取模板详情（含列配置）

`GET /kanban-templates/:kanban_template_id`

```json
// Response 200
{
  "template": {
    "kanban_template_id": 3,
    "name": "研发看板",
    "kanban_template_mode": "simple",
    "created_by": "guid",
    "created_by_name": "张三",
    "is_public": true,
    "created_at": "2026-07-02T00:00:00Z",
    "updated_at": "2026-07-02T00:00:00Z"
  },
  "columns": [
    {
      "column_id": 10,
      "status_key": "backlog",
      "name": "Backlog",
      "color": null,
      "is_hidden": true,
      "position": 0
    },
    {
      "column_id": 11,
      "status_key": "todo",
      "name": "待开发",
      "color": "#3498db",
      "is_hidden": false,
      "position": 1
    },
    { ... }
  ]
}
```

> 用于配置页预览模板列配置，决定是否选用。
> 校验：模板 `is_public = true` 或 `created_by = JWT.user_id`

### 6.3 创建看板

`POST /kanbans`

```json
// Request
{
  "owner_type": "user",               // "user" | "team"
  "owner_id": "guid",                  // user_id 或 team_id
  "kanban_template_id": 1,            // 引用哪个模板
  "group": "none",                    // 可选，默认 none
  "done_visible_days": 14,            // 可选，默认 14
  "is_default": false                 // 可选，默认 false
}

// Response 201
{
  "kanban": {
    "kanban_id": 10,
    "kanban_template_id": 1,
    "kanban_template_mode": "simple",
    "owner_type": "user",
    "owner_id": "guid",
    "group": "none",
    "done_visible_days": 14,
    "is_default": false,
    "created_at": "2026-07-03T00:00:00Z",
    "updated_at": "2026-07-03T00:00:00Z"
  }
}
```

> **用途：** 个人看板不存在时前端提示创建（兜底，正常注册时 auto-init）。
> **校验规则：**
> - `owner_type=user` → `owner_id` 必须 = JWT.user_id
> - `owner_type=team` → 操作人必须是团队成员
> - `kanban_template_id` 必须存在且可访问（`is_public=true` 或 `created_by=JWT.user_id`）

---

## 附录 A：Task 状态转移图

```
todo ──拖拽──→ in_progress
in_progress ──拖拽──→ in_review
in_progress ──拖拽──→ done
in_review ──拖拽──→ in_progress（打回修改）
in_review ──拖拽──→ done
done ──拖拽──→ in_progress（重新打开）
```

> Task 状态流转完全自由，无限制。无 `cancelled`（软删除替代）。

---

## 附录 B：端点对照表

| 功能 | Method | URL | 说明 |
|---|---|---|---|
| **看板查询** | | | |
| 个人看板 | `GET` | `/kanban/personal` | 先查 kanbans 再查 tasks，动态映射列 |
| 团队看板 | `GET` | `/kanban/team/:team_id` | 同上 |
| **Task CRUD** | | | |
| 创建 Task | `POST` | `/tasks` | team_id 非 null 进团队看板，null 进个人 |
| 列表查询 | `GET` | `/tasks` | 支持多条件过滤 |
| 获取详情 | `GET` | `/tasks/:task_id` | 含 sub_tasks 和最新 comments |
| 更新 Task | `PUT` | `/tasks/:task_id` | 部分字段更新 |
| 拖拽 Task | `PUT` | `/tasks/:task_id/drag` | 传 status |
| 删除 Task | `DELETE` | `/tasks/:task_id` | 软删除，级联 sub_task + comments |
| **Comments** | | | |
| 列出 Comments | `GET` | `/tasks/:task_id/comments` | |
| 创建 Comment | `POST` | `/tasks/:task_id/comments` | |
| 更新 Comment | `PUT` | `/comments/:comment_id` | |
| 删除 Comment | `DELETE` | `/comments/:comment_id` | |
| **看板配置** | | | |
| 获取看板配置 | `GET` | `/kanbans/:kanban_id` | 含 kanban + template + columns |
| 更新看板配置 | `PUT` | `/kanbans/:kanban_id` | kanban_template_id / group / done_visible_days |
| 创建看板 | `POST` | `/kanbans` | 个人看板不存在时创建（兜底） |
| **列管理** | | | |
| 更新列配置 | `PUT` | `/kanbans/:kanban_id/columns` | 完整列配置，后端 fork 判断 |
| **模板管理** | | | |
| 列出公开模板 | `GET` | `/kanban-templates` | is_public=true 或自己的模板 |
| 获取模板详情 | `GET` | `/kanban-templates/:kanban_template_id` | 含列配置，用于预览 |
| 保存为公开模板 | `POST` | `/kanban-templates` | 从现有看板列配置复制 |

---

## 附录 C：与 03-api-design.md 的差异

| 维度 | Brief API（03） | Task API（07） |
|---|---|---|
| **认证** | JWT | JWT（一致） |
| **user_id 来源** | JWT 解析 | JWT 解析（一致） |
| **权限模型** | created_by 全权限 | created_by 全权限，assignee_id 可拖拽 |
| **操作方式** | 详情页按钮 + 确认表单 | Kanban 拖拽 + API |
| **审查机制** | Arbiter LLM 审查（MVP 跳过） | 无审查 |
| **通知机制** | feedbacks 正式通知 | 无通知（团队内当面沟通） |
| **状态流转** | 双状态模型（upstream + downstream） | 单状态 status，自由流转 |
| **看板耦合** | 无 | 完全解耦——task 不存 kanban 引用 |
| **版本管理** | brief_versions | 无版本（content 直接覆盖） |
| **冗余字段** | created_by_name / assigned_to_name | created_by_name / assignee_name |
| **列管理** | 无 | 通过 kanban_template_columns 独立管理 |

---

## 附录 D：MVP 不做的功能

- ❌ `customized` 模式（多列映射同 status + task_columns 表）
- ❌ 泳道前端 UI（`group=assignee/brief/priority` 后端支持，前端暂不渲染泳道）
- ❌ 自建看板（多看板管理，MVP 只用 auto-init 的默认看板）
- ❌ 统计类 API（进度报表、工时汇总等）
- ❌ 批量操作 API（批量改 status/assignee/priority）
- ❌ Task 与 Brief 自动联动
- ❌ 看板筛选器（按人 / 优先级 / 到期日过滤）
- ❌ Task 分配通知（无 feedbacks，团队内 IM 沟通）
- ❌ 子任务 Kanban 视图（sub_task 只在 task 详情页展开）
- ❌ 团队看板查询（`GET /kanban/team/:team_id`）
- ❌ 获取默认看板快捷接口（`GET /kanban-config`）
