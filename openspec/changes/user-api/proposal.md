## Why

User 子系统的 SQLAlchemy 模型已经落地，但项目目前缺少对外暴露的 HTTP API。为了实现 MVP 中注册、登录、用户信息查询以及临时用户邮件 token 访问 brief 的完整流程，需要基于 FastAPI 实现 `/auth`、`/users` 和 `/tokens` 相关的用户 API。

## What Changes

- 新增 `src/briefchain/api/` 模块，基于 FastAPI 定义用户相关路由。
- 实现 `/auth` 路由：注册、登录、获取当前用户、登出。
- 实现 `/users` 路由：用户列表、获取单个用户（含敏感信息脱敏）。
- 实现 `/tokens` 路由：验证邮件 token、通过 token 接受/拒绝 brief。
- 新增 Pydantic schema 用于请求/响应校验。
- 新增依赖注入项：数据库 session、当前登录用户。
- 使用 JWT 作为认证凭证，登录/注册成功后返回 `token`。
- 补充单元测试，覆盖正常流程与错误校验。

**Note**: 微信/三方 OAuth 登录本次不实现（MVP 后续需要资质与前端展示支持）。

## Capabilities

### New Capabilities

- `user-auth`: 用户注册、登录、获取当前用户、登出。
- `user-profile`: 用户列表查询与单个用户详情（含 email/phone 脱敏）。
- `email-token`: 邮件 token 验证与基于 token 的 brief 接受/拒绝。

### Modified Capabilities

- 无

## Impact

- 新增 FastAPI、python-jose、pydantic 等运行时依赖（如尚未添加）。
- 新增 `/api/v1/auth`、`/api/v1/users`、`/api/v1/tokens` 路由。
- 不改动现有 SQLAlchemy 模型表结构。
