## Context

User 子系统的 SQLAlchemy 模型（`User`、`UserIdentity`、`EmailToken`）和 Alembic 迁移已经落地。API 设计文档 `docs/mvp_design/03-api-design.md` 已定义 `/auth`、`/users` 和 `/tokens` 的接口规范。本 change 需要将这些接口实现为可运行的 FastAPI 路由，为前端和临时用户提供用户认证、信息查询和邮件 token 操作能力。

## Goals / Non-Goals

**Goals:**
- 基于 FastAPI 实现 `/api/v1/auth`、`/api/v1/users`、`/api/v1/tokens` 路由。
- 实现注册、登录、当前用户、登出、用户列表、用户详情。
- 邮件 token 验证与接受/拒绝 brief 不在本次实现，留给后续 change 处理临时用户流程。
- 使用 JWT Bearer token 进行认证，登录/注册成功后返回 `token`。
- 对用户 email/phone 按 viewer 身份进行脱敏处理。
- 编写覆盖主流程的单元测试。

**Non-Goals:**
- 不实现微信/Google/GitHub 等 OAuth 登录（MVP 后续需要资质与前端展示支持）。
- 不实现邮箱验证码、短信验证码、真实邮件发送。
- 不实现密码重置、邮箱修改等账户管理功能。
- 不实现 Admin 角色与细粒度权限控制（MVP 只区分本人/他人）。

## Decisions

- **Web 框架**：使用 FastAPI，利用其原生依赖注入、Pydantic 集成和自动 OpenAPI 文档生成能力。
- **路由组织**：
  - `src/briefchain/api/routes/auth.py`：`/auth` 路由
  - `src/briefchain/api/routes/users.py`：`/users` 路由
  - `src/briefchain/api/routes/tokens.py`：`/tokens` 路由
  - `src/briefchain/api/main.py`：创建 FastAPI app 并注册路由
- **依赖注入**：
  - `get_db_session`：提供 SQLAlchemy `Session`
  - `get_current_user`：从 `Authorization: Bearer <token>` 解析 JWT 并加载当前 `User`
- **Schema 组织**：
  - `src/briefchain/api/schemas/auth.py`：注册/登录请求、认证响应
  - `src/briefchain/api/schemas/users.py`：用户列表/详情响应
  - `src/briefchain/api/schemas/tokens.py`：token 验证/操作响应
- **Service 组织**：
  - `src/briefchain/api/services/users.py`：用户领域服务函数，统一封装注册、登录、当前用户、用户列表/详情等业务逻辑。
  - 路由层职责限定为：解析 HTTP 请求、调用 service 函数、将 service 返回的 schema 对象序列化后返回响应。
  - Service 层职责包括：业务规则校验、数据持久化、密码哈希/JWT 生成、敏感信息脱敏、错误语义转换。
  - Email-token 相关 service（accept/reject/verify）本次不实现，后续 change 处理临时用户流程时补充。
- **密码处理**：使用 `passlib` 的 `bcrypt` 方案对 `password_hash` 进行哈希和校验。模型层只存储哈希值，业务层负责计算。
- **JWT 实现**：使用 `python-jose` + `cryptography` 生成和校验 HS256 token，payload 包含 `sub`（user id）和 `exp`。
- **敏感信息脱敏**：
  - 本人查看本人：完整显示 email/phone
  - 其他用户查看：email 显示 `***@example.com`，phone 显示 `138****0000`
  - MVP 不实现 admin，因此只有「本人」和「他人」两种情况
- **邮件 token 流程**：
  - 本次不实现 `/tokens` 路由。
  - `EmailToken` 模型保留在数据层，后续 change 再处理临时用户通过邮件 token 访问 brief 的完整流程。
- **错误处理**：统一返回 `{ "error": { "code": "...", "message": "...", "details": {} } }` 格式，HTTP 状态码符合 REST 语义。

## Risks / Trade-offs

- **JWT secret 管理** → 缓解：通过环境变量 `JWT_SECRET_KEY` 注入，本地开发使用 fallback 值，生产必须设置。
- **密码哈希性能** → 缓解：使用 bcrypt 默认 rounds，MVP 数据量小可接受。
- **email token 安全性** → 缓解：token 使用 UUID 随机字符串，设置过期时间，使用一次后记录 `used_at`；后续可考虑一次性签名 token。
- **测试依赖 JWT secret** → 缓解：测试使用固定的 `JWT_SECRET_KEY` fixture，避免依赖外部环境变量。

## Open Questions

- `/auth/logout` 在纯 JWT 无黑名单模式下只是客户端行为，是否需要服务端记录？MVP 仅返回 204。
