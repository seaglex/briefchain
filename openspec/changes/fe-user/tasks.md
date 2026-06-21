## 1. 项目初始化与目录结构

- [x] 1.1 在 `web/` 目录下初始化 Next.js 项目（App Router），配置 TypeScript 与基础依赖。
- [x] 1.2 从 `docs/mvp_design/04-frontend-prototype.html` 提取 CSS 变量与通用类名，写入 `web/app/globals.css`。
- [x] 1.3 创建共享认证工具函数 `web/lib/auth.ts`，统一处理 `/api/auth/*` 请求与后端错误解析。

## 2. 认证 API Route（后端代理）

- [x] 2.1 创建 `web/app/api/auth/login/route.ts`，接收 `{ email_or_phone, password }`，转发到后端 `POST /auth/login`，成功后设置 `httpOnly` Cookie。
- [x] 2.2 创建 `web/app/api/auth/register/route.ts`，接收 `{ name, email?, phone?, password }`，转发到后端 `POST /auth/register`，成功后设置 `httpOnly` Cookie。
- [x] 2.3 创建 `web/app/api/auth/logout/route.ts`，转发到后端 `POST /auth/logout` 并清除 `httpOnly` Cookie。
- [x] 2.4 Cookie 属性配置：`httpOnly`、`Secure`（生产环境）、`SameSite=Lax`、路径 `/`。

## 3. 登录页面

- [x] 3.1 创建 `web/app/login/page.tsx`，实现登录表单（邮箱/手机号、密码），复用 `globals.css` 样式。
- [x] 3.2 实现前端基础校验：邮箱/手机号与密码必填。
- [x] 3.3 实现登录提交逻辑：调用内部 `POST /api/auth/login`，成功跳转 `/`，失败展示后端错误信息。
- [x] 3.4 在登录页添加“还没有账号？注册”链接，跳转 `/register`。

## 4. 注册页面

- [x] 4.1 创建 `web/app/register/page.tsx`，实现注册表单（姓名、邮箱、手机号、密码），复用 `globals.css` 样式。
- [x] 4.2 实现前端基础校验：姓名、密码必填；邮箱与手机号至少填一项；邮箱格式合法；密码不少于 6 位。
- [x] 4.3 实现注册提交逻辑：调用内部 `POST /api/auth/register`，成功跳转 `/`，失败展示后端错误信息。
- [x] 4.4 在注册页添加“已有账号？登录”链接，跳转 `/login`。

## 5. 路由守卫与主应用

- [x] 5.1 创建 `web/middleware.ts`，未登录用户访问 `/` 等受保护路由时重定向到 `/login`。
- [x] 5.2 在 `middleware.ts` 中处理已登录用户访问 `/login`、`/register` 时重定向到 `/`。
- [x] 5.3 对 `/api/auth/*`、静态资源、`_next/*` 等路径在 middleware 中放行。
- [x] 5.4 创建/更新 `web/app/page.tsx` 作为主应用入口，并在 topbar 中实现 logout 按钮，调用 `/api/auth/logout` 后跳转 `/login`。

## 6. 验证

- [x] 6.1 启动 Next.js dev server 与后端服务，验证注册成功并跳转主应用。
- [x] 6.2 验证登录成功并跳转主应用；验证错误密码时展示错误信息且不跳转。
- [x] 6.3 验证未登录访问 `/` 被重定向到 `/login`；已登录访问 `/login`、`/register` 被重定向到 `/`。
- [x] 6.4 验证登出后 Cookie 被清除并返回 `/login`。
- [x] 6.5 验证 JWT 仅存在于 `httpOnly` Cookie 中，前端 JS 无法读取。
