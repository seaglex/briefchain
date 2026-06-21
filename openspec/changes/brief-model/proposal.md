## Why

Brief 是 BriefChain 的核心实体，整个产品的工作流转、版本追踪、反馈闭环都围绕 Brief 展开。MVP 阶段需要先落地一组稳定、可扩展的数据模型，为后续 API、状态机、Arbiter 审查和 Feedback 机制提供持久化基础。

## What Changes

- 基于 SQLAlchemy 定义 Brief 子系统全部核心表模型：
  - `briefs`：Brief 主表，包含树形结构字段与主状态机
  - `brief_versions`：版本历史表，完整保存每次内容变更
  - `brief_transfer_history`：跨人流转记录表，覆盖 sent / accepted / rejected 全生命周期
  - `brief_chains`：链元数据表，root brief 即 chain 代表
  - `brief_arbiter_reviews`：Brief 发送前 Arbiter 审查记录
  - `feedbacks`：反馈表，支持 blocked / progress / completion 类型
  - `feedback_arbiter_reviews`：Feedback 发送前 Arbiter 审查记录
- 使用 UUID 主键、时间戳、标准 SQLAlchemy ORM 声明式映射
- 配置 Alembic 迁移工具并生成初始迁移脚本
- 使用 SQLite 内存数据库编写单元测试，覆盖 3 个 brief 插入与一个 chain 列表查询
- 类型注解、Google docstring、基类复用等遵循 `CODING_GUIDELINES.md`

## Capabilities

### New Capabilities

- `brief-entity`：Brief 主表实体建模，包含树形关系与状态枚举
- `brief-versioning`：Brief 版本历史建模，支持版本递增与内容快照
- `brief-transfer`：Brief 流转历史建模，记录发送/接受/拒绝事件
- `brief-chain`：Brief Chain 元数据建模，root brief 作为 chain 代表
- `brief-arbiter-review`：Brief 发送前 Arbiter 审查记录建模
- `feedback`：Feedback 实体建模，支持多种反馈类型
- `feedback-arbiter-review`：Feedback 发送前 Arbiter 审查记录建模

### Modified Capabilities

- 无（本 change 只新增数据模型，不修改已有 spec 需求）

## Impact

- 数据库 schema 新增 7 张表
- 后续 Brief API、Feedback API、Arbiter 服务均依赖这些模型
- 不影响现有 User 子系统设计，仅通过外键引用 user id
