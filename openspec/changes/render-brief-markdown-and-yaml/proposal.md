## Why

当前 Brief 详情页把 `brief.content` 当作纯文本直接渲染，格式表现力差；同时 brief 的元数据（标题、优先级、预估人天、预期完成时间）散落在页面各处，用户难以快速获取结构化摘要。通过将内容渲染为 Markdown，并提供一个 YAML 格式的元数据摘要，可以显著提升 Brief 的可读性和专业感。

## What Changes

- 将 Brief 详情页的内容区从纯文本改为 Markdown 渲染。
- 新增一个 YAML formatter 组件，展示当前 brief 的 `title`、`priority`、`estimated_man_days`、`expected_completion_at` 四个字段。
- YAML 摘要组件放置在内容区上方或侧边，便于用户在阅读正文前先查看关键信息。
- 保持现有功能不变（版本切换、流转历史、Feedback、操作按钮）。

## Capabilities

### New Capabilities

- `brief-content-markdown`: 在 Brief 详情页将 `brief.content` 渲染为 Markdown。
- `brief-yaml-metadata`: 以 YAML 格式展示 brief 的核心元数据字段。

### Modified Capabilities

- 无现有 spec 需要变更需求（openspec/specs 目录为空）。

## Impact

- 前端：`web/components/BriefDetail.tsx` 的内容渲染逻辑、`web/app/briefs/[brief_id]/page.tsx` 的数据传递、可能新增一个 Markdown/YAML 工具组件。
- 后端：无需改动；`brief.content` 仍由后端返回原始字符串。
- 依赖：需要引入一个轻量 Markdown 渲染库（如 `marked` 或 `react-markdown`），或基于项目约束自行实现。
