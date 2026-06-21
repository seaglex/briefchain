## Context

BriefChain MVP 后端已实现 `/auth/register`、`/auth/login`、`/auth/me`、`/auth/logout` 等认证接口（见 `docs/mvp_design/03-api-design.md`）。当前仓库没有前端工程，只有 `docs/mvp_design/04-frontend-prototype.html` 这一静态原型。本次变更需要实现登录与注册页面，使用户能够完成注册、登录并进入主应用。

## Goals / Non-Goals

**Goals:**
- 使用 Next.js 构建登录与注册页面，视觉风格与 `04-frontend-prototype.html` 一致。
- 通过 Next.js API Route 代理后端 `/auth` 接口，将 JWT 写入 `httpOnly` Cookie，降低 XSS 风险。
- 使用 Next.js Middleware 做路由守卫：未登录用户访问主应用时重定向到登录页，已登录用户访问登录/注册页时重定向到主应用。
- 对表单进行基础校验并展示清晰的错误提示。

**Non-Goals:**
- 不引入微信/Google/GitHub 等第三方登录（MVP 后续）。
- 不实现手机号验证码登录（MVP 仅支持密码登录）。
- 不重写主应用页面，仅完成认证入口与必要的受保护路由判断。

## Decisions

### 1. 前端统一使用 Next.js（App Router）
- **理由**：Next.js 是当前团队统一的前端技术栈，具备 SSR/SSG、API Route、Middleware 等能力，适合构建需要认证的前端应用。
- **做法**：在 `web/` 目录下创建 Next.js 项目，使用 App Router 结构：`web/app/login/page.tsx`、`web/app/register/page.tsx`、`web/app/page.tsx`。

### 2. 目录约定使用 `web/`
- **理由**：与团队前端目录约定保持一致，避免 `frontend/` 等多种命名混用。
- **做法**：所有前端代码、样式、组件、API Route、Middleware 均放在 `web/` 下。

### 3. JWT 使用 `httpOnly` Cookie 存储
- **理由**：`localStorage` 存储 JWT 存在 XSS 风险；`httpOnly` Cookie 无法被前端 JS 读取，能显著降低 token 被盗取的风险。
- **做法**：
  - 前端不直接调用后端 `/auth/login`、`/auth/register`。
  - 前端调用同域 Next.js API Route：`/api/auth/login`、`/api/auth/register`、`/api/auth/logout`。
  - API Route 代理请求到后端，拿到 JWT 后通过 `Set-Cookie` 写入 `httpOnly`、`Secure`、`SameSite=Lax` 的 Cookie（开发环境可放宽 Secure）。
  - 登出 API Route 清除 Cookie。

### 4. 认证状态与 API 封装
- **理由**：登录、注册、登出以及后续请求都需要统一的 token 管理和错误处理。
- **做法**：
  - 创建 `web/lib/auth.ts`：封装对 `/api/auth/*` 的调用、统一解析 `{ error: { code, message } }` 错误格式。
  - 后续受保护接口请求由 Next.js 自动携带 Cookie，无需前端手动拼接 `Authorization` header。
  - `getSessionUser()` 等辅助函数可在 Server Component 或 API Route 中读取 Cookie 信息（如需）。

### 5. 路由守卫使用 Next.js Middleware
- **理由**：Middleware 在请求到达页面之前执行，适合做全局认证重定向，避免未登录用户看到主应用内容。
- **做法**：创建 `web/middleware.ts`，检查请求是否携带 session cookie：
  - 未登录访问 `/`、`/briefs` 等受保护路由 → 重定向到 `/login`。
  - 已登录访问 `/login`、`/register` → 重定向到 `/`。
  - 对 `/api/auth/*`、静态资源、`_next/*` 等路径放行。

### 6. 表单校验策略
- **理由**：减少无效请求，提升用户体验。
- **做法**：
  - 登录：邮箱/手机号、密码必填。
  - 注册：姓名、密码必填；邮箱与手机号至少填一项；邮箱格式需合法；手机号仅做非空校验（格式校验交给后端）。
  - 密码长度至少 6 位（与后端约定一致）。
  - 错误直接显示在提交按钮上方。

### 7. 样式复用
- **理由**：保持 BriefChain 品牌一致性，减少设计决策。
- **做法**：将 `04-frontend-prototype.html` 中的 CSS 变量与通用类名抽取到 `web/app/globals.css` 或 `web/styles/auth.css`，登录/注册页使用 `.login-page` + `.login-card` 布局。

## Risks / Trade-offs

- **[Risk]** Cookie 存在 CSRF 风险。  
  → **Mitigation**：使用 `SameSite=Lax`（主站同站请求可携带 Cookie，跨站 POST/嵌入请求不携带）；后续如支持跨域部署，可升级为 `SameSite=Strict` 或引入 CSRF Token。
- **[Risk]** SSR + Cookie 认证增加了前后端协作复杂度（需要处理服务端请求头转发、Cookie 透传）。  
  → **Mitigation**：MVP 阶段主要由 API Route 代理，Server Component 尽量只读；复杂数据请求后续逐步完善。
- **[Trade-off]** 引入 Next.js 相比纯静态页面更重，需要 Node 构建环境。  
  → **Mitigation**：Next.js 是团队统一方向，且本次变更范围可控，长期收益大于短期成本。

## Migration Plan

1. 在 `web/` 目录初始化 Next.js 项目（可使用 `create-next-app` 或手动配置）。
2. 创建 `web/app/login/page.tsx`、`web/app/register/page.tsx`、`web/app/page.tsx`。
3. 创建 API Route：`web/app/api/auth/login/route.ts`、`web/app/api/auth/register/route.ts`、`web/app/api/auth/logout/route.ts`。
4. 创建 `web/middleware.ts` 实现路由守卫。
5. 复用/迁移 `04-frontend-prototype.html` 样式到 `web/app/globals.css`。
6. 配置本地开发：启动 Next.js dev server（默认 `3000`），后端 `/api/v1` 可通过 Next.js rewrites 或环境变量配置代理目标。
7. 验证登录、注册、登出、路由守卫流程。

## Open Questions

- Next.js 与后端的 API 路径是否需要通过 `next.config.js` 的 `rewrites` 统一代理到 `/api/v1`？当前方案是前端只走 `/api/auth/*`，后续数据接口可再评估。
- Cookie 的 `Secure` 属性在本地开发时是否需要关闭？建议开发环境通过 `NODE_ENV` 控制。
