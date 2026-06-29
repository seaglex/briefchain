# BriefChain 设计文档（总入口）

> 最后更新：2026-06-28（v5：send/update 分离）

## 文档结构

| 文档 | 内容 |
|---|---|
| [01-brief-feedback-design.md](01-brief-feedback-design.md) | Brief / Feedback 子系统（核心业务流程、双状态模型、正式沟通） |
| [02-user-design.md](02-user-design.md) | User 子系统（用户、团队、三方登录） |
| [03-api-design.md](03-api-design.md) | Brief REST API 设计（MVP 端点定义） |
| [05-invite-link-design.md](05-invite-link-design.md) | 邀请链接设计 |
| [06-task-kanban-design.md](06-task-kanban-design.md) | Task / Kanban 子系统（数据模型、看板配置、泳道） |
| [07-task-kanban-api-design.md](07-task-kanban-api-design.md) | Task / Kanban REST API 设计（端点定义） |

## 产品定位

BriefChain 是一个 Agent 增强的项目管理工具，用 Agent 约束需求和反馈质量，提升项目执行效率，同时约束项目内容和状态更新可靠性，提升组织迭代效率。

与传统工具的核心区别：传统工具面向需求方，需求质量无约束，过程管理靠人工维护。BriefChain 平等对待需求方和执行方，以 brief 转移来自动获得项目的执行记录。

## 产品原则

1. **平等对待 upstream 和 downstream**
2. **以 brief 的转移为工作天然分界**，工作从真正owner开始，转移和变更需经过中立裁判 Arbiter，评估 brief 质量、brief 修改影响等
3. **全链路透明闭环**，downstream 完成工作同步通知链路上所有 upstream
4. **支持跨系统使用**，两个不同 BriefChain 服务可以互操作

## 核心概念

### Brief

Brief 是 BriefChain 的核心实体，代表需求方提给执行方的一个工作单元。涵盖了 idea，以及常见的 epic / feature / story 等类型。

- 选择 "Brief" 而非 "Task" / "Issue" 的原因：Brief 强调需求方的主动写作行为，是从意图开始的，而非已分解的工作单元
- "Chain" 代表树形结构的全链路透明，每个环节都有 Arbiter 审查
- Brief 是**合约性质**的：操作审慎、需要完整语境、不可随意拖拽流转。所有状态变更在 Brief 详情页操作，不在 Kanban 上拖拽

### 角色关系：Upstream / Downstream

不使用固定的角色标签（如"需求方/执行方"），而是用位置关系描述：

- **Upstream**：当前 brief 的创建者
- **Downstream**：当前 brief 的接收者

实际场景中，一个人对上游是 downstream，对下游是 upstream（如产品对运营是 downstream，对开发是 upstream）。

### Arbiter

中立裁判 Agent，在 brief 从 upstream 发送给 downstream 时执行审查：
- 评估 brief 质量（完整性、歧义、验收标准等）
- 评估 brief 修改的影响

### 树形结构

```
Idea（根 brief）
├── PRD A（子 brief）
│   ├── Task A1（叶子）
│   └── Task A2（叶子）
└── PRD B（子 brief）
    └── Task B1（叶子）
```

- 根 brief = 原始想法
- 叶子 brief = 可执行的最小单元
- 整棵树可见，全链路透明

### Task & Kanban

Task 和 Kanban 是最终执行者自己的工具，brief chain 只汇总进度，一般不用关心。

**Brief = 跨边界合约，Task = 内部协调工具。**两者操作模式完全不同：

| | Brief | Task |
|---|-------|------|
| 性质 | 合约，操作审慎 | 工作项，操作轻快 |
| 操作位置 | 详情页（看到完整上下文再决定） | Kanban 看板（拖拽流转） |
| 操作方式 | 明确按钮 + 可能需附带信息（原因、完成说明） | 拖拽 |
| 状态变更 | 不可逆性强，需审慎 | 轻快随意 |
| 审查 | Arbiter 审查 | 无审查 |

**为什么 Brief 不适合 Kanban 操作：**
1. 状态变更需要语境 — accept 前要读描述和验收标准，submit 前要写完成说明
2. 状态变更不可逆性强 — submitted→done 是正式确认，不能随意拖拽
3. 减少误操作 — 合约状态不应轻率变更

Kanban & Task (Task / sub-tasks / bug)
- 为了方便内部执行的工具，没有 arbiter 审查
- **除 Bug 外都要关联一个 Brief（brief_id required）**，没有 Brief 就不能建 Task，从数据模型上杜绝"随便想想就开始做"
- Sub-task 不进入 Kanban，只是 task 详情

### Feedback

包含两类
- Downstream 的项目进度更新、状态更新
- Upstream 的状态更新（暂停、取消、审核）

feedbacks 是合约期间的**正式合同通知**，不是聊天消息。每个 feedback type（除 progress 外）都跟一个状态变更绑定，双向（up→down / down→up）统一走一张表，用 `is_to_down` 区分方向。所有状态变更的原因和历史都在 feedbacks 表查，天然支持多次反复（每次 reject_submit、每次 suspend/resume 都是一条新记录）。闲聊用其他 IM，沟通完再总结成 feedback 发出。

### 双状态模型

Brief 状态由 `upstream_state` 和 `downstream_state` 共同表达，视角归属在数据模型层面清晰可见。

| upstream_state | downstream_state | 含义 |
|:--------------:|:----------------:|------|
| editing | null | upstream 编写中 |
| sent | null | 等候 downstream 响应（邀约） |
| in_process | opened | downstream 执行中 |
| in_process | delegated | downstream 已委派 |
| in_process | blocked | downstream 阻塞 |
| in_process | submitted | downstream 已提交，等 upstream review |
| suspended | preserved | upstream 暂停（downstream_state 保留） |
| cancelled | preserved | 已取消（downstream_state 保留用于审计） |
| done | preserved | 验收通过，终态 |

BriefVersion 状态 代表编辑状态

|  status  |     含义     |
|:--------:|:----------:|
|  draft   |   草稿，不可发   |
| reviewed | AI 审核过，可以发 |
|  final   |  不可变更，可以发  |


**状态分组（降低认知负担）：**

| 分组 | 组合                             | 直觉 |
|------|--------------------------------|------|
| 编写中 | (editing, null)                | "我还在想" |
| 等候中 | (sent, null)                   | "等对方回应" |
| 执行中 | (in_process, opened/delegated) | "在推进" |
| 待审 | (in_process, submitted)        | "交卷了等批" |
| 阻塞 | (in_process, blocked)          | "卡住了" |
| 暂停 | (suspended, any)               | "冻结" |
| 结束 | (done, any) / (cancelled, any) | "落幕" |

详见 [01-brief-feedback-design.md](01-brief-feedback-design.md)。

## 动作盘点（12 个动作）

**核心原则：version 与 state 解耦。**

- version 状态，决定 patch 和 send 执行方式
    - draft / reviewed 随便改，final 就只能升版本
    - reviewed / final 才能 send（存在 rejected 后 re-send）
- 编辑阶段
    - 在不与 brief 关联 version 上修改
    - send （可被拒绝） / update（直接发生） 动作使得 brief 与 version 关联，version 状态为final
- 邀约阶段（send 之后）
    - upstream_state 在 editing / sent 状态（区别在于 assigned_to 是否有值）
    - downstream accept 变成 合约阶段
- 合约阶段（accept 之后）
    - brief upstream_state 不能是 editing 或 sent，其他几乎没有约束

send 是邀约阶段桥梁，update 是合约阶段桥梁，同时与 brief state 和 brief version status 相关

按 API 聚类分组：

| 分组 | 动作 | 操作方 | 操作对象 | 变更                                    |
|------|------|--------|---------|---------------------------------------|
| **编辑** | patch | upstream | version only | 修改版本内容（final→新建 draft，非 final→原地改）    |
| | submit-review | upstream | version only | 版本 draft→reviewed                     |
| **Transfer** | send | upstream | version + brief | 两种场景：首次发送 / 替换邀约（记录在 transfer_history） |
| | accept | downstream | brief only | (sent, null) → (in_process, opened)   |
| | reject | downstream | brief only | (sent, null) → (editing, null)        |
| **Upstream-action** | cancel | upstream | brief only | → (cancelled, preserved)              |
| | suspend | upstream | brief only | → (suspended, preserved)              |
| | resume | upstream | brief only | → (in_process, preserved)             |
| | approve | upstream | brief only | (in_process, submitted) → (done, preserved) |
| | reject_submit | upstream | brief only | (any, submitted) → (any, opened)      |
| | update | upstream | version + brief | downstream_state → opened + 版本+1（记录在 feedbacks） |
| **Downstream-action** | process | downstream | brief only | 不变，创建 progress feedback               |
| | submit | downstream | brief only | downstream_state → submitted          |
| | open | downstream | brief only | downstream_state → opened             |
| | delegate | downstream | brief only | downstream_state → delegated          |
| | block | downstream | brief only | downstream_state → blocked            |

**核心规则：**
- **version 与 state 解耦**：patch / submit-review 只操作 version，不碰 brief 状态；accept / cancel / suspend 等只操作 brief 状态，不碰 version。send 是邀约阶段桥梁，update 是合约期间桥梁
- downstream 自由控制 downstream_state，不需要为每个动作起独立名字
- send 从 sent 发起 = 替换邀约（downstream 还没 accept，代价更小）
- update 从 in_process / suspended 发起 = 更新合约（新版本 final + 强制 downstream_state → opened，记录在 feedbacks 而非 transfer_history）
- suspend 只改 upstream_state，downstream_state 保留不动；resume 原样恢复
- cancel 保留 downstream_state 用于历史审计

## 进度

- [x] 产品定位与原则
- [x] 核心概念定义
- [x] 状态机设计 — 双状态模型（upstream_state 6 + downstream_state 4/null）
- [x] version 与 state 解耦 — send/update 是两座桥梁，patch/submit-review 只操作 version
- [x] 动作盘点（12 动作，send/update 分离，按编辑/Transfer/Upstream-action/Downstream-action 分组）
- [x] Brief / Feedback 子系统数据库设计（feedbacks 11 type，content 规则）
- [x] User 子系统数据库设计
- [x] REST API 设计（v1.0）
- [x] 邀请链接设计
- [x] Task 数据模型设计
- [x] Kanban & Task 子系统设计
- [ ] Arbiter 审查维度与 LLM Prompt 设计
- [ ] MVP 范围定义
- [ ] 跨系统互操作协议设计
