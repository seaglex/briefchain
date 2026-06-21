## Why

Brief 和 Feedback 目前把附件描述以 JSON 形式直接保存在数据库中，缺少统一的文件存储抽象。为了在 MVP 阶段支持本地文件上传，同时保留未来无缝切换到对象存储（S3/MinIO 等）的扩展性，需要引入一个可插拔的对象存储适配器。该存储层不仅用于附件，也可存放任意文件，并支持按组（bucket/前缀）隔离。

## What Changes

- 新增 `src/briefchain/storage/` 模块，定义统一的对象存储抽象接口（如 `ObjectStorage`）。
- 实现 `LocalObjectStorage` 适配器，MVP 阶段将文件存储在项目目录下的 `.storage/` 中。
- 定义文件元数据模型（`StoredObject` / `ObjectInfo`），用于描述文件名、MIME 类型、存储 key、公开 URL 等。
- 支持按组（group/bucket）隔离文件，方法接口接受可选的 `group` 参数。
- 提供工厂函数或配置驱动的适配器实例化方式，便于后续切换为 S3/MinIO 实现。
- 编写单元测试覆盖本地存储的保存、读取、删除、URL 生成和分组隔离。

## Capabilities

### New Capabilities

- `object-storage`: 统一的对象存储抽象与本地文件系统实现，支持分组隔离。

### Modified Capabilities

- 无

## Impact

- 新增 `src/briefchain/storage/` 模块。
- 不改动现有 `brief_versions.attachments` 和 `feedbacks.attachments` 的 JSON 列结构；后续 API 层可将存储后的元数据写入这些字段。
- 新增本地存储目录配置项，默认使用项目根目录下的 `.storage/`。
- 为后续对象存储适配器预留接口。
