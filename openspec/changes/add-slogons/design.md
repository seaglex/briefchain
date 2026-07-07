## Context

BriefChain 当前登录/注册页面只有表单，invite 页面只有邀请信息和操作，对未登录或首次访问的用户没有产品价值说明。本次变更要在这些关键入口增加统一的产品特点介绍，并提供一个独立的落地页作为品牌链接目标。

## Goals / Non-Goals

**Goals:**
- 在 `/login`、`/register`、`/invites/[token]` 下方展示三条固定产品特点。
- 新增 `/landing` 页面集中展示产品特点。
- 将 AppShell 中左上角 BriefChain 品牌链接指向 `/landing`。
- 使用共享组件保证三处 slogan 展示样式一致。

**Non-Goals:**
- 不改动后端 API 或数据模型。
- 不实现可配置的后台文案系统（slogans 内容硬编码）。
- 不替换根路径 `/`（当前保持原逻辑，除非用户后续要求）。

## Decisions

### 独立落地页路径使用 `/landing`
- **Rationale**: 不改变根路径 `/` 的现有行为（目前可能是重定向到 `/briefs` 或登录页），同时给品牌链接一个明确的目标。`/landing` 语义清晰，对外分享也稳定。
- **Alternative considered**: 把 `/` 直接做成落地页。放弃，因为当前 `/` 已承担入口跳转职责，改动会影响现有流程。

### Slogans 封装为共享客户端组件 `ProductSlogans`
- **Rationale**: 登录、注册、invite 三处都需要同样的展示，组件化避免重复。该组件只负责静态展示，无业务逻辑，可标记为 `"use client"` 或保持为服务端组件均可；为简单起见作为普通 React 组件即可。
- **Alternative considered**: 在每页直接写死 JSX。放弃，因为重复代码难以维护。

### 品牌链接仅修改 `AppShell`/`Sidebar` 中的 `<Link href="/">`
- **Rationale**: 目前左上角品牌链接大概率在 `AppShell` 或 `Sidebar` 中指向 `/`，统一改为 `/landing` 即可。需要确认未登录状态下的公共头部是否也有该链接。
- **Alternative considered**: 修改 `next.config.js` 重定向。放弃，因为直接改链接更直观，也允许用户先看到落地页再手动进入应用。

### 使用 Lucide 图标或纯 CSS 图标
- **Rationale**: 无需引入新的图标库。项目若已有 Lucide 依赖可直接使用；否则用简单 CSS 形状或 emoji 作为占位，保持轻量。
- **Open**: 实际实现时根据项目依赖决定。

## Risks / Trade-offs

- [Risk] `/landing` 页面未登录用户访问时可能需要特殊处理（当前 AppShell 会要求登录） → **Mitigation**: 落地页不使用 `AppShell`，直接渲染独立布局；或在 `AppShell` 中允许 `/landing` 公开访问。
- [Risk] 品牌链接改为 `/landing` 后，老用户习惯点击回首页 → **Mitigation**: 落地页提供明显的“进入应用”按钮跳转 `/briefs`。
- [Risk] Invite 页面是客户端组件，引入新的服务端组件可能需要注意数据流 → **Mitigation**: `ProductSlogans` 为纯展示组件，无 props 依赖，可直接嵌入。

## Migration Plan

1. 创建 `ProductSlogans` 共享组件和 `/landing` 页面。
2. 修改 `login/page.tsx`、`register/page.tsx`、`invites/[token]/page.tsx` 引入组件。
3. 修改 `AppShell`/`Sidebar` 品牌链接指向 `/landing`。
4. 本地验证三处入口的 slogan 显示和品牌链接跳转。
5. 无需数据库迁移或后端部署。

## Open Questions

- 项目是否已安装 Lucide 图标库？若无，是否接受使用 emoji 或简单 CSS 图形？
- 根路径 `/` 当前行为是什么？是否需要后续把 `/` 也指向落地页？
