## Context

目前 brief 的 `submit-review` 是同步 force-skip：上游调用后直接创建一个 `force_skipped` 的审核记录，然后即可 send。这没有真正评估需求质量，导致下游收到的内容可能结构不完整、目标不可衡量。

为了改善这一点，已有三份设计文档定义了完整的异步审核方案：

- `docs/mvp_design/10-arbiter-queue-design.md`：通用数据库任务队列。
- `docs/mvp_design/11-arbiter-worker-design.md`：后台 worker 子进程、Skill 执行、重试与健康回收。
- `docs/mvp_design/12-arbiter-review-api-design.md`：异步 API、webhook、与现有 send 流程的集成。

本设计文档基于上述方案，补充实现层面的技术决策与风险权衡。

## Goals / Non-Goals

**Goals:**

- 实现基于 LLM 的 brief 内容质量审核，使用 `src/briefchain/skills/brief-review` skill。
- 实现通用异步任务队列，MVP 使用数据库，接口与实现解耦。
- 实现后台 worker 子进程消费队列、分发任务、管理重试与健康回收。
- 实现异步审核 API（触发 + 查询）。
- 改造 `submit-review` action 为异步触发。
- 通过环境变量接入第三方 LLM API（base URL、model、API key）。

**Non-Goals:**

- 不实现前端 UI 的审核结果展示（仅提供 API 与 webhook）。
- 不引入 Redis / MQ 等外部队列中间件（MVP 阶段）。
- 不保证多 worker 并发下的精确一次性执行（依赖业务层幂等与重试）。
- 不实现 webhook 重试与投递保证。
- 不实现除 `review` 之外的其它任务类型（如 `summary`）。

## Decisions

### 1. 队列使用数据库实现，接口抽象隔离
- **Decision**: MVP 使用 `DELETE ... ORDER BY created_at RETURNING *` 实现 `dequeue`，队列接口不暴露数据库细节。
- **Rationale**: 最小外部依赖，与现有 PostgreSQL/SQLite 技术栈一致；未来切换到 Redis 只需替换实现类。
- **Alternatives considered**: Redis `BRPOP` —— 需要额外部署与运维，MVP 不需要高吞吐。

### 2. Worker 以子进程方式由 FastAPI 拉起
- **Decision**: 主进程启动时通过 `subprocess.Popen` 启动 worker，退出时转发信号并等待。
- **Rationale**: 零额外运维成本，共享虚拟环境与配置；避免 Celery/RQ 等调度框架。
- **Alternatives considered**: 独立 systemd 服务 / 容器 —— 增加部署复杂度；Celery —— 依赖 broker。

### 3. Skill 使用 Google ADK 加载
- **Decision**: 使用 Google ADK 的 skill 加载机制读取 `src/briefchain/skills/brief-review/SKILL.md` 及元数据。
- **Rationale**: 项目技术栈已选定 Google ADK；skill 文件本身已是结构化 Markdown，ADK 可提供统一的解析与版本管理。
- **Alternatives considered**: 自定义 YAML/JSON skill 解析 —— 与团队既定方向不一致。

### 4. LLM 配置通过环境变量注入
- **Decision**: 使用 `LLM_BASE_URL`、`LLM_MODEL`、`LLM_API_KEY` 等环境变量配置第三方 LLM 端点。
- **Rationale**: 不锁定供应商，便于切换不同模型；配置与代码分离，符合 12-factor 原则。
- **Alternatives considered**: 在数据库中配置模型 —— 增加权限与 UI 复杂度，MVP 不需要。

### 5. 审核状态由业务表管理，队列只负责投递
- **Decision**: `task_queue` 只存 `id/type/ref_id/created_at`，状态、重试、错误、webhook 全部放在 `brief_arbiter_reviews`。
- **Rationale**: 职责清晰，队列保持通用；业务表天然支持查询、幂等、健康回收。
- **Alternatives considered**: 队列表增加 `status` / `retry_count` —— 使队列与 review 耦合，降低通用性。

### 6. Webhook 在事务外发送，失败静默丢弃
- **Decision**: worker 在更新 review 的事务提交后再发送 webhook；失败仅记录日志。
- **Rationale**: 避免 webhook 失败阻塞队列；前端轮询作为兜底。
- **Alternatives considered**: 事务内发送 —— webhook 慢会拖长事务；重试队列 —— MVP 过度设计。

### 7. Worker 内部硬编码 skill 选择
- **Decision**: `type=review` 固定映射到 `brief-review@latest`，前端与 API 不指定 skill。
- **Rationale**: 审核策略是后端实现细节，不应暴露给客户端。
- **Alternatives considered**: API 传入 skill 名称 —— 增加客户端负担与安全风险。

### 8. SKIP_REVIEW 环境变量作为降级开关
- **Decision**: 当 `SKIP_REVIEW=true` 时，worker 不调用 LLM，直接将 review 标记为 `force_skipped`。
- **Rationale**: 便于在 LLM 不可用、成本敏感或演示场景下快速降级；保持原有 force-skip 行为作为可配置 fallback。
- **Alternatives considered**: 在 API 请求中传参 —— 增加客户端复杂度和误用风险；数据库配置 —— MVP 不需要。

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Worker 崩溃导致任务卡住 | 启动时与周期性健康回收扫描 `processing` 超时的 review 并重新入队 |
| LLM 调用高延迟阻塞队列 | 单 worker 串行处理，MVP 任务量小；未来可通过多 worker 或 Redis 扩展 |
| LLM 成本不可控 | 通过环境变量配置模型，可在生产环境使用更便宜的模型；后续可加 token 预算 |
| Webhook 未送达 | 失败静默丢弃 + 前端轮询兜底；后续可引入 webhook 重试与事件表 |
| 数据库队列性能瓶颈 | 接口已抽象，高吞吐时可替换为 Redis 而不改业务代码 |
| 重复审核同一版本 | API 层与 worker 层双重幂等检查 |

## Migration Plan

1. **Schema迁移**：新增 `task_queue` 表；为 `brief_arbiter_reviews` 添加字段并更新状态枚举。
2. **配置迁移**：在 `.env.example` 与部署环境中新增 `LLM_*`、`QUEUE_BACKEND`、`WORKER_*`、`ARBITER_WEBHOOK_URL`、`SKIP_REVIEW`。
3. **代码部署**：部署新 API 与 worker 代码；FastAPI 主进程会自动拉起 worker。
4. **行为切换**：`submit-review` 改为 202 异步响应，前端需要支持轮询或 webhook。
5. **回滚**：还原代码版本并恢复数据库 schema；队列中的任务会随回滚丢失或保留在旧表中，需根据情况清理。

## Open Questions

1. 生产环境使用哪家第三方 LLM API？需要确认 `LLM_BASE_URL` 与 `LLM_MODEL` 的具体值。
2. Worker 子进程崩溃后的自动重启策略是否需要在 MVP 实现，还是仅依赖健康回收？（依赖健康回收）
3. 是否需要为 `brief_arbiter_reviews` 历史记录保留多个版本，还是只保留每个 brief 的最新 review？（保留多个，因为webhook可能会变）
4. Webhook 是否需要签名验证？MVP 阶段建议先不实现，后续根据安全需求补充。（先不实现）
