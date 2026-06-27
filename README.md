# BriefChain

AI-reviewed briefs for smoother handoffs — better outcomes for both sides.

## Background

传统工具的问题
- 设计面向需求方，经常由于需求描述不够清楚而导致执行偏差、返工等问题
- 状态需要人工维护，可靠性差
- 项目owner（如果不是产研）不用，项目本身需求质量和透明度不够

## BriefChain产品设计原则

1. **平等对待 upstream (通常是需求方) 和 downstream (通常是执行方)**
2. **以 brief 的转移为工作天然分界**，工作从项目owner开始，转移需经过中立裁判 Arbiter，评估 brief 质量、brief 修改影响等
3. **全链路透明闭环**，downstream 重要更新同步链路上所有 upstream，保证所有 upstreams 随时了解工作状态
4. **支持跨系统使用**，两个不同 BriefChain 服务可以互操作，支持跨组织协作

效果说明

- Arbiter 中立审查，提前发现可能存在的需求歧义等
- Brief 从真正owner开始，在不同人/团队间转移自动记录工作状态，无需额外维护且绝对可靠
- Feedback 沿 chain 自动向 upstream 传递，便于每个节点的 owner 了解进度、风险和执行差异
- 同一个人 / 团队内部协作基于传统的 task 和 kanban，工作状态变化不严谨，但不影响组织效能分析——比如排期/开发/测试时间都是开发团队内部消耗

## 核心概念

### Brief

Brief 是 BriefChain 的核心实体，代表 upstream 提给 downstream 的一个工作单元，涵盖了 idea，以及常见的 epic / feature / story 等类型。

Brief 经过 arbiter 审查才能发送给 downstream，downstream 可以额外审查（包括基于 AI），拒绝或接受。

Feedback 是 downstream 结果更新，比如完成、部分完成、被阻塞，feedback 会逐级更新 chain 上的 upstream，并总结状态、和原始需求的差别等，让整个 chain 上 upstreams 保持透明。

### 角色关系：Upstream / Downstream

不使用固定的角色标签（如"需求方/执行方"），而是用位置关系描述：

- **Upstream**：当前 brief 的创建者
- **Downstream**：当前 brief 的接收者

实际场景中，一个人对上游是 downstream，对下游是 upstream（如产品对运营是 downstream，对开发是 upstream）。

### Feedbacks

包含两类
- Downstream 的项目进度更新、状态更新
- Upstream 的状态更新（暂停、取消、审核）

### Arbiter

中立裁判 Agent。

在 brief 从 upstream 发送给 downstream 时执行审查：
- 评估 brief 质量（完整性、歧义、验收标准等）
- 评估 brief 修改的影响

在 feedback 从 downstream 发送给 upstream 时同样执行审查
- 评估 feedback 的质量（完整性、是否完全满足原来需求）

### Chain 树形结构

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

### Task & Kanban

Task 和 Kanban 是最终执行者自己的工具，brief chain 只汇总进度，一般不用关心。

Brief 是两个人 / 两个团队的自然工作边界，对应强烈的边界感，也只能有粗粒度标准状态。执行时可以基于Brief自动或手动拆成Tasks。
- 需要更细节的流程（比如开发、测试、联调、上线）
- 团队内希望当面沟通、快速协调而非文档
- TL需要掌控感，希望能看到每个人具体的工作

Kanban & Task (Task / sub-tasks / bug)
- 为了方便内部执行的工具，没有 arbiter 审查
- 除 Bug 外都要关联一个 Brief 提供背景
- Sub-task 不进入 Kanban，只是 task 详情

### 命名

- **Brief**：强调 upstream 的主动写作行为，是从意图开始的，而非已分解的工作单元（Task / Issue）
- **Chain**：代表树形结构的全链路透明

## 当前工作状态

🚧 MVP (WIP) 包含以下子系统：
- Brief（核心业务流程）
- User（支持邮箱注册）
- 权限系统

技术栈
- 后端 python + FastAPI + SQLAlchemy
- 前端 Next.js
- 数据库 PostgreSQL + sqlite（本地最简模式）
- object storage MinIO + 本地文件adapter（本地最简模式）

设计文档：[docs/mvp_design/](docs/mvp_design/)

## 本地开发环境

### 前置依赖

- **Python** `>=3.13`
- **uv** `>=0.9.0`（推荐 `0.9.2+`）
- **Node.js** `>=22`（推荐 `24.7.0+`）
- **npm** `>=10`（推荐 `11.5.1+`）
- **PostgreSQL** 或 SQLite（默认使用 SQLite，零配置启动）

### 1. 安装后端依赖并同步虚拟环境

```bash
# 进入项目根目录
cd briefchain

# 创建/同步虚拟环境并安装依赖
uv sync

# 安装开发依赖（用于测试、lint）
uv sync --extra dev
```

### 2. 数据库迁移（Alembic）

默认使用 SQLite：`sqlite:///./briefchain.db`。

```bash
# 应用所有迁移到最新版本
uv run alembic upgrade head
```

### 3. 启动后端服务

```bash
# 开发模式（带热重载）
uv run uvicorn briefchain.api.main:app --reload --host 0.0.0.0 --port 8000
```

API 默认地址：`http://localhost:8000`  
健康检查：`http://localhost:8000/health`

### 4. 安装前端依赖

```bash
cd web

npm install
```

### 5. 启动 Next.js 前端

```bash
# 开发模式（带热重载）
npm run dev
```

前端默认地址：`http://localhost:3000`

## License

License：Apache-2.0
