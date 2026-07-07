## Why

目前登录/注册页面和 invite 页面对新用户缺乏产品价值说明，用户进入应用后不知道 BriefChain 解决什么问题。增加产品特点介绍可以降低首次使用时的认知门槛，同时让左上角的 BriefChain 品牌链接指向一个独立的落地页，统一对外表达产品价值主张。

## What Changes

- 新增一个公开或半公开的 `/landing`（或 `/about`）页面，集中展示三条产品特点。
- 在登录页面（`/login`）和注册页面（`/register`）下方增加产品特点介绍区块。
- 在 invite 页面（`/invites/[token]`）下方增加产品特点介绍区块。
- 将系统左上角 BriefChain 品牌链接从当前默认跳转（如 `/briefs`）改为指向新的介绍页面。
- 介绍内容固定为以下三条，分别配图或图标：
  1. **团队间以 brief 转移为工作天然分界**，团队内支持传统看板模式
  2. **平等对待上下游**，以 AI 审核优化需求质量
  3. **全链路透明闭环**，自动聚合下游进展

## Capabilities

### New Capabilities

- `product-slogans`: 在产品关键入口（登录、注册、invite、品牌链接落地页）展示统一的产品价值主张。

### Modified Capabilities

- 无现有 spec 需要变更需求（openspec/specs 目录为空）。

## Impact

- 前端：新增落地页面组件，修改 `AppShell`/`Sidebar` 中的品牌链接，修改 `login/page.tsx`、`register/page.tsx`、`invites/[token]/page.tsx`。
- 后端：无需改动 API；落地页为静态内容，可公开访问。
- 路由：新增 `/` 或 `/landing` 路由；需要确认根路径 `/` 当前行为并决定是否替换为落地页。
- 设计：需要一套统一的 Slogan 卡片样式，与现有设计系统保持一致。
