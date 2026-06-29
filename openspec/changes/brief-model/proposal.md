## Why

Brief 是 BriefChain 的核心实体，整个产品的工作流转、版本追踪、反馈闭环都围绕 Brief 展开。MVP 阶段需要先落地一组稳定、可扩展的数据模型，为后续 API、状态机、Arbiter 审查和 Feedback 机制提供持久化基础。

## What Changes

- 基于 SQLAlchemy 定义 Brief 子系统全部核心表模型，并同步设计文档 v4 的表结构变化：
  - `briefs`：Brief 主表，使用 `upstream_state` + `downstream_state` 双状态；增加 `title`、`priority`、`expected_completion_at`、`created_by_name`、`assigned_to_name`、`status_changed_at`、`status_changed_by` 等字段
  - `brief_versions`：版本历史表，增加 `status`、`arbiter_review_id`、`expected_completion_at`、`is_upstream_changed`、`revision_reason`、`modified_by`、`modified_at`、`change_summary`
  - `brief_transfer_history`：跨人流转记录表，覆盖 sent / accepted / rejected 全生命周期，增加 `from_user_name` / `to_user_name` 名字快照
  - `brief_chains`：链元数据表，增加 `owner_id`、`owner_name`、`priority` 冗余字段
  - `brief_arbiter_reviews`：Brief 发送前 Arbiter 审查记录，明确 `issues` / `suggestions` JSON 结构
  - `feedbacks`：正式合同通知表，增加 `is_to_down`、`from_user_name`、`to_user_name`，`type` 按方向拆分为 11 个值
  - `feedback_arbiter_reviews`：Feedback 发送前 Arbiter 审查记录，按 feedback type 定义 `result` 结构
- 使用 UUID 主键、时间戳、标准 SQLAlchemy ORM 声明式映射
- 配置 Alembic 迁移工具并生成初始迁移脚本
- 使用 SQLite 内存数据库编写单元测试，覆盖 3 个 brief 插入与一个 chain 列表查询
- 类型注解、Google docstring、基类复用等遵循 `CODING_GUIDELINES.md`

## Capabilities

### New Capabilities

- `brief-entity`：Brief 主表实体建模，包含树形关系、`upstream_state`/`downstream_state` 双状态、优先级/标题/人名冗余快照、状态变更跟踪
- `brief-versioning`：Brief 版本历史建模，支持版本生命周期状态（draft/reviewed/final）、关联审查记录、变更原因与变更摘要
- `brief-transfer`：Brief 流转历史建模，记录发送/接受/拒绝事件及收发人名字快照
- `brief-chain`：Brief Chain 元数据建模，包含 owner 与 priority 冗余，root brief 作为 chain 代表
- `brief-arbiter-review`：Brief 发送前 Arbiter 审查记录建模，含结构化 issues 与 suggestions
- `feedback`：Feedback 实体建模，支持 `is_to_down` 方向与 11 种 feedback type，含收发人名字快照
- `feedback-arbiter-review`：Feedback 发送前 Arbiter 审查记录建模，按 type 区分 result schema

### Modified Capabilities

- 无上游外部能力变更（本 change 只调整 Brief 子系统内部数据模型定义，不修改已对外暴露的 spec 需求）

## Impact

- 数据库 schema 新增/调整 7 张表，字段和枚举与设计文档 v4 对齐
- 后续 Brief API、Feedback API、Arbiter 服务均依赖这些模型
- 不影响现有 User 子系统设计，仅通过外键引用 user id；用户名字段作为快照冗余存储
