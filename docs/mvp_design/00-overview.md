# BriefChain 设计文档（总入口）

> 最后更新：2026-06-21

## 文档结构

| 文档 | 内容 |
|---|---|
| [01-brief-feedback-design.md](01-brief-feedback-design.md) | Brief / Feedback 子系统（核心业务流程） |
| [02-user-design.md](02-user-design.md) | User 子系统（用户、团队、三方登录） |
| [03-api-design.md](03-api-design.md) | REST API 设计（MVP 端点定义） |

## 产品定位

BriefChain 是一个 Agent 增强的项目管理工具，用 Agent 约束需求和反馈质量，提升项目执行效率，同时约束项目内容和状态更新可靠性，提升组织迭代效率。

与传统工具（Jira、钉钉）的核心区别：传统工具面向需求方，需求质量无约束，过程管理靠人工维护。BriefChain 平等对待需求方和执行方，以 brief 转移来自动获得项目的执行记录。

## 产品原则

1. **平等对待 upstream 和 downstream**
2. **以 brief 的转移为工作天然分界**，工作转移需经过中立裁判 Arbiter，评估 brief 质量、brief 修改影响等
3. **全链路透明闭环**，downstream 完成工作同步更新链路上所有 upstream 需求方状态
4. **支持跨系统使用**，两个不同 BriefChain 服务可以互操作

## 核心概念

### Brief

Brief 是 BriefChain 的核心实体，代表需求方提给执行方的一个工作单元。涵盖了 idea，以及常见的 epic / story / task / sub-task / bug 等所有类型。

- 选择 "Brief" 而非 "Task" / "Issue" 的原因：Brief 强调需求方的主动写作行为，是从意图开始的，而非已分解的工作单元
- "Chain" 代表树形结构的全链路透明，每个环节都有 Arbiter 审查

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
├── Spec A（子 brief）
│   ├── Task A1（叶子）
│   └── Task A2（叶子）
└── Spec B（子 brief）
    └── Task B1（叶子）
```

- 根 brief = 原始想法
- 叶子 brief = 可执行的最小单元
- 整棵树可见，全链路透明

## 进度

- [x] 产品定位与原则
- [x] 核心概念定义
- [x] 状态机设计
- [x] Brief / Feedback 子系统数据库设计
- [x] User 子系统数据库设计
- [x] REST API 设计
- [ ] Arbiter 审查维度与 LLM Prompt 设计
- [ ] 内部状态表设计
- [ ] MVP 范围定义
- [ ] 跨系统互操作协议设计
