## Context

BriefChain MVP 的数据层需要支撑 Brief 的全生命周期：创建、版本迭代、跨人流转、Arbiter 审查、Feedback 闭环。设计文档 [docs/mvp_design/01-brief-feedback-design.md](../../../docs/mvp_design/01-brief-feedback-design.md) 已给出 7 张核心表的字段与状态机定义，但尚未落地为可执行的 SQLAlchemy 模型。

本 change 的目标是把设计文档中的表结构转换为声明式 ORM 模型，为后续 Alembic 迁移、API 实现和单元测试提供基础。

## Goals / Non-Goals

**Goals:**
- 使用 SQLAlchemy 2.0 声明式风格定义 7 张核心表
- 模型字段、类型、约束、索引与 `01-brief-feedback-design.md` 保持一致，表名 `transfer_history` 统一改为 `brief_transfer_history`
- 提供表关系（brief ↔ version、brief ↔ transfer、brief ↔ feedback 等）
- 配置 Alembic 迁移并生成初始 revision
- 使用 SQLite 内存数据库编写单元测试：插入 3 个 briefs 并查询 chain 列表
- 代码符合 `CODING_GUIDELINES.md`：类型注解、Google docstring、模块单一职责

**Non-Goals:**
- 不实现 Repository / Service / API 层
- 不实现 Arbiter LLM 审查逻辑
- 不实现内部状态模板相关表（设计文档 2.8 已标记为待设计）

## Decisions

- **ORM 风格**：采用 SQLAlchemy 2.0 `DeclarativeBase` + `mapped_column`，统一使用 `Mapped[T]` 类型注解。
- **主键类型**：所有主键使用 `UUID`（`uuid.UUID`），数据库层存储为 UUID，应用层也使用 UUID，避免 ID 冲突并兼容跨系统互操作。
- **枚举实现**：状态、优先级、反馈类型等使用 Python `enum.StrEnum`，数据库层存储为字符串，便于可读性和未来扩展。
- **JSON 字段**：`attachments`、`issues`、`result` 等结构化数据使用 `JSON` 类型，映射为 `dict` / `list`，保持灵活性。
- **时间戳**：所有表统一包含 `created_at` 和 `updated_at`，使用 `DateTime(timezone=True)` 并设置 `server_default=func.now()`。
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
- **树形查询性能** → 缓解：MVP 通过 `root_id` 一次性查整棵树；若后续层级深、数据量大，再考虑 CTE 或 `ltree`。
- **UUID 作为主键的索引与排序开销** → 缓解：MVP 数据量小，可接受；后续如需要顺序分页，可加入 `created_at` 复合索引。
- **SQLite 与生产数据库方言差异** → 缓解：模型使用通用类型（UUID 在 SQLite 以 BLOB/STRING 兼容存储），Alembic 迁移脚本在 SQLite 上先行验证，后续 PostgreSQL 适配时再调整。

## Open Questions

- 是否需要为 `briefs.status` 增加数据库层 CHECK 约束？
- `attachments` 的 JSON schema 是否需要在模型层定义辅助 Pydantic 模型？（本次不在模型层实现）
