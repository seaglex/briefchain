## Context

BriefChain 的 brief 当前只有 `priority`、`upstream_state`、`downstream_state` 等元信息，没有内容粒度分类。本次变更在数据模型、API schema、服务端逻辑和前端展示中引入 `type` 字段，取值范围为 `idea / epic / feature / story`，默认 `idea`。该字段同时保存在 `briefs` 和 `brief_versions` 上，确保版本快照能保留历史类型。

## Goals / Non-Goals

**Goals:**
- 为 brief 增加类型维度，支持创建、编辑、存储、API 返回和前端展示。
- 在 brief 详情页头部按 `Type - Brief 详情` 的格式展示类型。
- 创建/编辑 brief 的表单中增加类型选择器。
- 对历史数据友好：未设置类型的 brief 默认按 `idea` 处理。

**Non-Goals:**
- 基于类型做工作流限制或权限控制（例如只有 epic 才能拆分子 brief）。
- 在 brief 列表页增加按类型筛选（可在后续迭代中扩展）。
- 修改 task 或 kanban 的类型系统。

## Decisions

### 在 `Brief` 和 `BriefVersion` 同时保存 `type`
- **Rationale**: `Brief` 上的 `type` 是当前有效值，用于列表和详情展示；`BriefVersion` 上的 `type` 保证每个版本快照保留其创建时的类型，避免回溯历史版本时类型丢失。
- **Alternative considered**: 仅在 `Brief` 上保存，通过版本号间接查找。放弃，因为版本内容应自包含，便于审计和回放。

### 新增 `BriefType` StrEnum，数据库用 `String(20)`
- **Rationale**: 与现有 `BriefPriority`、`BriefUpstreamState` 等枚举保持一致，便于扩展且人类可读。
- **Alternative considered**: 用 small int 存储以节省空间。放弃，因为字符串更直观，且数据量不大。

### API 默认值为 `idea`，schema 层允许可选字段
- **Rationale**: 保持 API 向后兼容，旧客户端不传 `type` 也能正常工作；新客户端传值则被接受。
- **Alternative considered**: 强制所有请求都传 `type`。放弃，因为这会破坏现有集成和脚本。

### 前端标题展示使用首字母大写格式
- **Rationale**: `Idea - Brief 详情` 比 `idea - Brief 详情` 更符合中文/英文混排页面的视觉习惯。
- **Implementation note**: 在后端返回原始小写枚举值，前端通过简单的 label map 进行展示格式化，避免展示文本硬编码在 API 中。

## Risks / Trade-offs

- [Risk] 数据库迁移后现有 brief 全部显示为 `idea`，可能与用户预期不符 → **Mitigation**: 这是预期行为，产品层面默认所有历史 brief 为 idea 类型；如需批量修改可后续提供管理功能。
- [Risk] 前端类型选择器与后端枚举不同步 → **Mitigation**: 前端从共享类型定义（TypeScript 类型或 API 文档）生成选项，避免硬编码。
- [Risk] 新增字段导致 brief 列表 API 响应体积轻微增加 → **Mitigation**: 字段为短字符串，影响可忽略；必要时后续可支持字段裁剪。

## Migration Plan

1. 生成并执行 Alembic 迁移脚本，为 `briefs` 和 `brief_versions` 表添加 `type` 列，默认值为 `idea`，非空。
2. 部署后端服务。
3. 部署前端服务。
4. 无需回滚策略，因为新增列带默认值，删除列即可回滚。

## Open Questions

- 是否需要为 Alembic 迁移脚本单独提交一个 change？本次 tasks 中将其作为 implementation step 包含在内。
