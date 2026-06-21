## Context

Brief 和 Feedback 模型当前以 JSON 列表保存附件元数据（`name`、`url`、`type`），但没有统一的文件存储层。业务代码若直接操作文件系统，未来切换到对象存储时会产生大量改动。本 change 引入对象存储适配器模式，将「保存/读取/删除/生成 URL」等操作抽象为统一接口，MVP 用本地文件系统实现，后续可通过新增适配器支持 S3/MinIO 等对象存储。该存储层可存放任意文件，并支持按组（group/bucket）隔离。

## Goals / Non-Goals

**Goals:**
- 定义统一的对象存储抽象接口（`ObjectStorage`）。
- 实现本地文件系统适配器（`LocalObjectStorage`）。
- 定义文件元数据模型（`StoredObject` / `ObjectInfo`）。
- 支持按组（group/bucket）隔离文件。
- 提供配置驱动的适配器实例化机制。
- 编写单元测试覆盖本地存储的完整生命周期与分组隔离。

**Non-Goals:**
- 不实现对象存储（S3/MinIO）适配器（仅预留接口）。
- 不修改现有 `brief_versions.attachments` / `feedbacks.attachments` 的数据库结构。
- 不提供 HTTP 上传/下载接口（由后续 API change 实现）。
- 不实现大文件分片上传、断点续传、CDN 回源等高级功能。

## Decisions

- **抽象接口**：使用 Python `Protocol` 或抽象基类定义 `ObjectStorage`，核心方法包括：
  - `save(file: BinaryIO | bytes, filename: str, content_type: str, group: str | None = None) -> StoredObject`
  - `get(key: str, group: str | None = None) -> BinaryIO`
  - `delete(key: str, group: str | None = None) -> None`
  - `get_url(key: str, group: str | None = None) -> str`
  - `list(group: str | None = None) -> list[StoredObject]`（可选，用于列举组内对象）
- **元数据模型**：使用 Pydantic 模型 `StoredObject` 描述文件，字段包括 `key`、`filename`、`content_type`、`size`、`url`、`group`、`created_at`。
- **本地存储实现**：`LocalObjectStorage` 将文件写入项目目录下的 `.storage/`，按 `group/key` 组织目录。若未指定 group，则使用默认组（如 `default`）。
- **Key 生成策略**：默认使用 UUID 作为存储 key，保留原始 filename 仅用于元数据和下载时的 `Content-Disposition`。
- **URL 生成**：本地适配器返回可配置的 base URL + group + key，未来对象存储适配器返回预签名 URL 或公开 bucket URL。
- **配置方式**：通过环境变量 `OBJECT_STORAGE_TYPE`（默认 `local`）和 `OBJECT_STORAGE_PATH`（默认项目目录下 `.storage/`）实例化对应适配器。
- **模块组织**：
  - `src/briefchain/storage/base.py`：抽象接口与元数据模型
  - `src/briefchain/storage/local.py`：本地文件系统实现
  - `src/briefchain/storage/factory.py`：适配器工厂函数
  - `src/briefchain/storage/__init__.py`：公开 API

## Risks / Trade-offs

- **本地存储与生产环境差异** → 缓解：接口与实现解耦，生产环境只需新增配置和对象存储适配器，业务代码无需改动。
- **文件名冲突** → 缓解：存储 key 使用 UUID，原始文件名仅保存为元数据。
- **本地存储目录权限** → 缓解：启动时检查并创建目录，测试使用临时目录。
- **URL 可访问性** → 缓解：本地适配器生成逻辑 URL，实际 HTTP 服务由 API 层提供；对象存储适配器可返回真实可访问 URL。
- **组名称安全性** → 缓解：对 group 名称做合法性校验，禁止 `..` 和路径分隔符穿越。

## Open Questions

- 是否需要限制单文件大小和允许的文件类型？（MVP 先不限制，后续在 API 层控制。）
- 对象存储适配器是否需要支持预签名 URL 过期时间？（接口设计时预留参数。）
- 是否需要实现跨组复制/移动对象？（MVP 先不实现。）
