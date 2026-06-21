## Why

User 子系统是 BriefChain 认证、授权与协作的基础。MVP 阶段需要先落地用户主表、三方登录绑定和临时用户邮件令牌，为后续认证 API 和权限模型提供数据层支撑。

## What Changes

- 基于 SQLAlchemy 定义 User 子系统核心表模型：
  - `users`：用户主表，支持 registered / oauth / external / temporary 四种类型
  - `user_identities`：三方登录绑定表（微信/Google/GitHub）
  - `email_tokens`：临时用户邮件访问令牌表
- 复用已有 `briefchain.models.base` 中的 `Base`、`UUIDPrimaryKeyMixin`、`TimestampMixin`
- 添加用户类型枚举 `UserType`
- 更新 Alembic 迁移，新增用户相关表
- 使用 SQLite 内存数据库编写单元测试，覆盖用户创建、身份绑定、邮件令牌
- 类型注解、Google docstring、模块单一职责遵循 `CODING_GUIDELINES.md`

## Capabilities

### New Capabilities

- `user-entity`：用户主表建模，支持多种用户类型与全局唯一 GUID
- `user-identity`：三方登录绑定建模，支持一个用户绑定多个身份
- `email-token`：临时用户邮件令牌建模，支持外部用户通过邮件操作 brief

### Modified Capabilities

- 无（本 change 只新增 User 子系统模型，不修改已有 Brief 相关 spec 需求）

## Impact

- 数据库 schema 新增 3 张表
- 后续 Auth API、User API 均依赖这些模型
- 与 Brief 子系统通过 `created_by`、`assigned_to`、`from_user`、`to_user` 等外键字段隐性关联
