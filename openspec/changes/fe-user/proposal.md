## Why

BriefChain MVP 的认证后端（`/auth/register`、`/auth/login`、`/auth/me`）已经实现，但前端缺少对应的注册与登录入口。没有登录页，用户无法完成注册、获取 JWT 并完成后续 Brief 操作，因此需要补齐认证相关的前端页面与交互流程。

## What Changes

- 新增登录页面：邮箱/手机号 + 密码表单，调用 `POST /auth/login`。
- 新增注册页面：姓名、邮箱（可选）、手机号（可选）、密码表单，调用 `POST /auth/register`；邮箱与手机号至少填一项。
- 复用 `docs/mvp_design/04-frontend-prototype.html` 中的配色、字体、卡片与按钮样式，保持 BriefChain 视觉一致性。
- 实现 API 错误提示（统一错误格式）与前端基础校验（必填、格式、密码长度）。
- 登录/注册成功后保存 JWT，跳转至应用主界面；未登录访问主界面时重定向到登录页。
- 提供登录/注册切换链接。

## Capabilities

### New Capabilities

- `fe-auth-pages`: 前端认证页面（登录、注册）及其与后端 `/auth` 接口的集成。

### Modified Capabilities

<!-- 无现有 spec 需要修改 -->

## Impact

- 新增前端页面文件与认证相关脚本（具体技术栈由 design.md 确定）。
- 依赖后端 `/auth` 接口，需要与 `03-api-design.md` 保持一致。
- 影响未认证用户的访问控制：主界面需在缺少有效 token 时重定向。
