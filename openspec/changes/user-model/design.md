## Context

BriefChain MVP 的 User 子系统设计已在 [docs/mvp_design/02-user-design.md](../../../docs/mvp_design/02-user-design.md) 中定义，包含用户类型、三方登录、临时用户邮件令牌。当前项目已落地 Brief 子系统的 SQLAlchemy 模型与 Alembic 迁移，User 子系统需要以一致的风格补齐，为后续 `/auth` 和 `/users` API 提供数据基础。

本 change 暂不实现团队与成员关系表（`teams`、`team_memberships`），留待后续 change 处理。

## Goals / Non-Goals

**Goals:**
- 使用 SQLAlchemy 2.0 声明式风格定义 User 子系统 3 张核心表（users / user_identities / email_tokens）
- 字段、类型、约束与 `02-user-design.md` 保持一致
- 复用已有 `briefchain.models.base` 中的 `Base`、`UUIDPrimaryKeyMixin`、`TimestampMixin`
- 添加 `UserType` 枚举
- 更新 Alembic 迁移，新增用户相关表
- 使用 SQLite 内存数据库编写单元测试：覆盖用户创建、身份绑定、邮件令牌
- 代码符合 `CODING_GUIDELINES.md`：类型注解、Google docstring、模块单一职责

**Non-Goals:**
- 不实现团队与成员关系表（`teams`、`team_memberships`），留待后续 change
- 不实现密码哈希逻辑（仅保留字段）
- 不实现 OAuth 登录流程
- 不实现邮件发送逻辑
- 不实现 Repository / Service / API 层

## Decisions

- **模块组织**：新建 `src/briefchain/models/user.py`，集中存放 `User`、`UserIdentity`、`EmailToken`，保持 User 子领域内聚。团队相关模型（`Team`、`TeamMembership`）不在本次实现。
- **用户类型枚举**：使用 `StrEnum` 定义 `UserType`，取值为 `registered`、`oauth`、`external`、`temporary`，数据库层存储字符串，避免通过字段组合推断类型。
- **主键与外键**：所有主键使用 `UUID`；`users.id` 被 `user_identities.user_id` 引用。`email_tokens` 按设计文档仅关联 `brief_id`，通过 `email` 与 `temporary` 类型用户隐式关联，本次不添加外键。
- **字段可空性**：
  - `email`、`phone`、`password_hash`、`source_system`、`external_ref` 均允许 null
  - `user_type` 直接决定哪些字段生效，数据库层不做 CHECK 约束
- **关系设计**：
  - `User.identities` → `UserIdentity`
  - 所有关系使用 `relationship(..., lazy="raise")`，防止业务代码中无意识地触发 N+1 查询；需要访问关系时必须显式使用 `joinedload` / `selectinload` 等 eager load 策略
- **密码字段**：`password_hash` 使用 `String(255)`，后续由 service 层写入哈希值，模型层不处理。
- **Alembic 迁移**：基于模型自动生成新 revision，与已有 brief models migration 形成线性历史。
- **测试数据库**：继续使用 SQLite `:memory:`，通过 `Base.metadata.create_all()` 创建 schema。

## Risks / Trade-offs

- **external 用户 `external_ref` 防恶作剧** → 缓解：设计上要求写入时 `external_ref = id`，但数据库层暂不强制；后续在创建逻辑中校验。
- **多身份绑定** → 缓解：`user_identities` 的 `provider` + `provider_user_id` 添加唯一约束，避免重复绑定。
- **temporary 用户复用** → 缓解：通过 email 匹配复用 `users` 记录，但 MVP 先简单创建新记录，后续做账号合并。

## Open Questions

- 是否需要为 `users.user_type` 增加数据库层 CHECK 约束？
- `email_tokens` 是否关联 `users` 表的外键？设计文档中临时用户流程是隐式关联，本次暂不添加外键。
