## Context

BriefChain MVP 的数据层需要支撑 Brief 的全生命周期：创建、版本迭代、跨人流转、Arbiter 审查、Feedback 闭环。设计文档 [docs/mvp_design/01-brief-feedback-design.md](../../../docs/mvp_design/01-brief-feedback-design.md) 已给出 7 张核心表的字段、双状态模型与冗余字段设计，但尚未完全落地为可执行的 SQLAlchemy 模型。

本 change 的目标是把设计文档中的最新表结构转换为声明式 ORM 模型，为后续 Alembic 迁移、API 实现和单元测试提供基础。

## Goals / Non-Goals

**Goals:**
- 使用 SQLAlchemy 2.0 声明式风格定义 7 张核心表
- 模型字段、类型、约束、索引与 `01-brief-feedback-design.md` 保持一致：
  - `briefs` 使用 `upstream_state` + `downstream_state` 双状态，去掉单 `status` 字段
  - `briefs` / `brief_transfer_history` / `feedbacks` / `brief_chains` 增加用户名字段冗余快照
  - `briefs` 增加 `title`、`priority`、`expected_completion_at`、`status_changed_at`、`status_changed_by` 等反范化/跟踪字段
  - `brief_versions` 增加 `status`、`arbiter_review_id`、`expected_completion_at`、`is_upstream_changed`、`revision_reason`、`modified_by`、`modified_at`、`change_summary`
  - `feedbacks` 增加 `is_to_down`、`from_user_name`、`to_user_name`，`type` 按方向拆分
- 表名 `transfer_history` 统一改为 `brief_transfer_history`
- 提供表关系（brief ↔ version、brief ↔ transfer、brief ↔ feedback 等）
- 配置 Alembic 迁移并生成初始 revision
- 使用 SQLite 内存数据库编写单元测试：插入 3 个 briefs 并查询 chain 列表
- 代码符合 `CODING_GUIDELINES.md`：类型注解、Google docstring、模块单一职责

**Non-Goals:**
- 不实现 Repository / Service / API 层
- 不实现 Arbiter LLM 审查逻辑
- 不实现内部 Task 子系统相关表（设计文档 2.8 已标记为待设计）

## Decisions

- **ORM 风格**：采用 SQLAlchemy 2.0 `DeclarativeBase` + `mapped_column`，统一使用 `Mapped[T]` 类型注解。
- **主键类型**：所有主键使用 `UUID`（`uuid.UUID`），数据库层存储为 UUID，应用层也使用 UUID，避免 ID 冲突并兼容跨系统互操作。
- **枚举实现**：状态、优先级、反馈类型等使用 Python `enum.StrEnum`，数据库层存储为字符串，便于可读性和未来扩展。
  - `BriefUpstreamState`: editing / sent / in_process / suspended / cancelled / done
  - `BriefDownstreamState`: opened / delegated / blocked / submitted（可空）
  - `BriefVersionStatus`: draft / reviewed / sent
  - `FeedbackType`: 按 `is_to_down` 方向分为 upstream→downstream（cancel / suspend / resume / approve / reject_submit / update）和 downstream→upstream（submit / block / delegate / open / progress）
- **JSON 字段**：`attachments`、`issues`、`suggestions`、`result` 等结构化数据使用 `JSON` 类型，映射为 `dict` / `list`，保持灵活性。
- **时间戳**：所有表统一包含 `created_at` 和 `updated_at`，使用 `DateTime(timezone=True)` 并设置 `server_default=func.now()`。
- **双状态模型**：`Brief.status` 不再存在，拆分为 `upstream_state` 与 `downstream_state`。`upstream_state` 表达 upstream 视角生命周期，`downstream_state` 在 `upstream_state = in_process` 时表达 downstream 视角子状态，其他情况下为 null。
- **冗余用户名字段**：`created_by_name`、`assigned_to_name`、`from_user_name`、`to_user_name`、`owner_name` 在创建/分配/发送/反馈时从 users 表读取并写入，列表查询不需要 JOIN。合约语义上，名字是操作时的快照——"当时签合约的人叫什么"，不是实时值。
- **反范化字段**：
  - `briefs.title` / `priority` / `expected_completion_at` 等于当前 sent 版本（`current_version`）的对应值；`current_version` 为 null 时取 v1。
  - `brief_chains.title` / `owner_id` / `owner_name` / `priority` 从根 brief 同步，避免 chains 列表 JOIN。
- **状态变更跟踪**：`briefs.status_changed_at` / `status_changed_by` 记录最后一次状态变更，用于 agent 估算 sub-tree 进展。
- **模块组织**：
  - `src/briefchain/models/base.py`：公共 Base、UUID 主键 mixin、时间戳 mixin
  - `src/briefchain/models/brief.py`：briefs / brief_versions / brief_transfer_history / brief_chains / brief_arbiter_reviews
  - `src/briefchain/models/feedback.py`：feedbacks / feedback_arbiter_reviews
  - 这种组织方式让 brief 与 feedback 两个子领域各自内聚，避免单文件过大。
- **关系设计**：
  - `Brief.parent_id` 自引用外键，建立树形结构
  - `Brief.root_id` 指向同表的 `brief_id`，根节点 `root_id = brief_id`
  - `BriefChain.chain_id` = 根 `brief_id`，不额外维护成员关系
  - `BriefTransferHistory`、`BriefVersion`、`Feedback` 均通过 `brief_id` 与 `Brief` 关联
  - 所有关系使用 `relationship(..., lazy="raise")`，防止业务代码中无意识地触发 N+1 查询；需要访问关系时必须显式使用 `joinedload` / `selectinload` 等 eager load 策略
- **decimal / 工时**：`estimated_man_days` 使用 `Numeric(5, 2)`，支持小数天表示。
- **表名命名**：为避免与后续其它领域（如 feedback transfer）的 history 表产生歧义，流转历史表数据库名统一为 `brief_transfer_history`，对应模型类名为 `BriefTransferHistory`。
- **Alembic 配置**：使用 `alembic init` 生成标准目录结构，配置 `sqlalchemy.url` 从环境变量读取；初始 migration 基于模型自动生成并校验 SQLite 可执行。
- **测试数据库**：单元测试使用 SQLite `:memory:` 引擎，通过 `create_all()` 或 Alembic `upgrade(head)` 创建 schema；测试用例覆盖根 brief + 2 个子 brief 的插入以及按 `root_id` 查询 chain 列表。

## Risks / Trade-offs

- **JSON 字段缺乏 schema 约束** → 缓解：在 Pydantic schema / API 层做校验，数据库层保持灵活。
- **有效状态组合仅靠应用层保证** → 缓解：业务逻辑/服务层维护状态矩阵，必要时在数据库层增加 CHECK 约束。
- **树形查询性能** → 缓解：MVP 通过 `root_id` 一次性查整棵树；若后续层级深、数据量大，再考虑 CTE 或 `ltree`。
- **UUID 作为主键的索引与排序开销** → 缓解：MVP 数据量小，可接受；后续如需要顺序分页，可加入 `created_at` 复合索引。
- **SQLite 与生产数据库方言差异** → 缓解：模型使用通用类型（UUID 在 SQLite 以 BLOB/STRING 兼容存储），Alembic 迁移脚本在 SQLite 上先行验证，后续 PostgreSQL 适配时再调整。

## Open Questions

- 是否需要为 `briefs.upstream_state` + `briefs.downstream_state` 增加数据库层 CHECK 约束？（MVP不增加）
- `attachments` / `issues` / `result` 的 JSON schema 是否需要在模型层定义辅助 Pydantic 模型？（本次不在模型层实现）
