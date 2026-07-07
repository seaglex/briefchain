## Context

当前 `BriefDetailView` 使用 `<p style={{ whiteSpace: "pre-wrap" }}>{brief.content}</p>` 展示内容，不支持 Markdown 格式，也没有结构化的元数据摘要。本次变更要在详情页增加 Markdown 渲染和 YAML 元数据展示。

## Goals / Non-Goals

**Goals:**
- 将 `brief.content` 渲染为 Markdown。
- 提供 YAML 格式的元数据摘要，字段限定为 `title`、`priority`、`estimated_man_days`、`expected_completion_at`。
- 保持现有详情页布局和功能不变。

**Non-Goals:**
- 不实现 Markdown 编辑器（仅渲染）。
- 不支持 YAML 中除这四个字段以外的其他字段。
- 不修改后端 API 或数据库存储格式。

## Decisions

### 使用 `marked` 库渲染 Markdown
- **Rationale**: `marked` 体积小、无 React 依赖、可直接在服务端组件和客户端组件中使用。纯字符串输入输出，便于与现有代码集成。
- **Alternative considered**: `react-markdown` 功能更丰富但体积更大，且依赖较多。对于 MVP 的只读渲染，`marked` 足够。

### YAML formatter 自行实现
- **Rationale**: 字段固定且简单，直接拼接字符串即可，无需引入 `yaml` 库。输出为等宽字体代码块样式，便于阅读。
- **Implementation**: 根据字段值生成如下格式的代码块：
  ```yaml
  title: "Brief title"
  priority: p2
  estimated_man_days: 5
  expected_completion_at: "2026-07-10T10:00:00+00:00"
  ```

### YAML 摘要放在内容卡片顶部
- **Rationale**: 用户阅读正文前可以快速获取关键信息，且不破坏现有的标签页结构。

## Risks / Trade-offs

- [Risk] `marked` 的默认配置会渲染原始 HTML，存在 XSS 风险 → **Mitigation**: 使用 `marked` 的 `sanitize` 选项或只转义 HTML 标签；MVP 阶段内容由内部用户产生，风险可控，但仍建议关闭原始 HTML 渲染。
- [Risk] Markdown 渲染样式与现有设计系统不一致 → **Mitigation**: 为渲染后的内容添加 scoped CSS 类，覆盖 heading、list、code 等基础样式。

## Migration Plan

1. 安装 `marked` 依赖。
2. 新增 Markdown 渲染组件和 YAML formatter 组件。
3. 修改 `BriefDetailView` 使用新组件展示内容和元数据。
4. 验证现有 brief 页面正常渲染，且 Markdown 语法正确解析。
5. 无需数据库迁移。

## Open Questions

- 是否需要支持代码块语法高亮？MVP 阶段暂不支持。
