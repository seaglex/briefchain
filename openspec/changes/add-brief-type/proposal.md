## Why

Brief 目前缺少对内容粒度的分类，导致用户无法一眼区分一个 brief 是原始想法、大型史诗、功能需求还是具体需求。引入类型字段可以让 brief 在创建和展示时语义更清晰，也便于后续按类型做筛选和流转控制。

## What Changes

- 在 `Brief` 与 `BriefVersion` 数据模型上新增 `type` 字段，类型枚举为 `idea / epic / feature / story`，默认值为 `idea`。
- 在 Pydantic schema 中新增 `BriefType` 枚举，并在 `BriefCreateRequest`、`BriefPatchRequest`、`BriefUpdateActionRequest`、`BriefListItem`、`BriefDetail` 中暴露该字段。
- 在 brief 列表页和详情页返回 `type`，并在 brief 详情页头部标题前展示类型，例如 `Idea - Brief 详情`。
- 创建 brief 的表单和编辑 brief 的表单增加类型选择器。
- 数据库现有 brief 会回填为默认值 `idea`，不会破坏已有数据。

## Capabilities

### New Capabilities

- `brief-type`: 为 brief 引入类型维度（idea / epic / feature / story），支持创建、编辑、展示和默认回填。

### Modified Capabilities

- 无现有 spec 需要变更需求（openspec/specs 目录为空）。

## Impact

- 后端：`src/briefchain/models/brief.py`、`src/briefchain/models/enums.py`、`src/briefchain/api/schemas/briefs.py`、brief service 层和路由响应。
- 前端：`web/app/briefs/[brief_id]/page.tsx`、`BriefDetail` 组件、创建/编辑 brief 的相关组件与类型定义。
- 数据库：需要为 `briefs` 和 `brief_versions` 表增加 `type` 列并设置默认值。
- API：brief 相关请求和响应会新增 `type` 字段；未传该字段时使用默认值 `idea`。
