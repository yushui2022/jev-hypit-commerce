# 运行手册

## 配置

| 环境变量 | 默认 / 用途 |
|---|---|
| CREATOR_DATA | `data`，SQLite、向量和输出目录，默认相对当前目录 |
| CREATOR_ROOT | 仓库根目录；用于读取工作台、示例、Hypit |
| CREATOR_API_TOKEN | 可选 API Bearer token；非 localhost 绑定强制要求 |
| JEV_API_KEY | 仅服务端读取，不写入任务或前端 |
| CREATOR_RETRIEVAL | `lexical` 或 `hybrid` |
| QDRANT_URL / QDRANT_API_KEY | 可选远程 Qdrant 地址和密钥 |
| CHROME_PATH | Hypit 初始化时的 Chrome / Chromium 路径 |

默认仅监听 127.0.0.1。若开启外部访问，使用 TLS 反向代理和 API token。静态工作台与归档演示媒体公开可读；API、业务目录和生成文件受 token 保护。本版是单工作空间，token 不是多用户身份系统。不可把私密素材放入公开展示媒体目录。

## 独立 worker

```sh
creator-network serve --external-worker
# 同一台机器、同一 CREATOR_DATA，另一个终端：
creator-network worker
```

本地演示默认内嵌一个 worker。视频渲染会占用该 worker，因此排队的匹配可能等待。需要隔离时未来增加 job kind 队列路由；当前不要宣称独立渲染集群。多 worker 下不要共享本地 Qdrant 文件，应使用远程 Qdrant。

## API 示例

服务运行后访问 `/docs` 获取由 Pydantic 生成的完整 OpenAPI。以下示例是无 token 的 localhost 模式；远程模式需 `Authorization: Bearer ...`。

```sh
curl http://127.0.0.1:8890/api/catalog
curl -X POST http://127.0.0.1:8890/api/matches \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: demo-match-1' \
  -d '{"product_id":"speaker","engine":"baseline","top_k":3}'
```

返回 202 和 job ID。查询 `/api/jobs/{id}`，完成后查看 result.candidates，再 POST `/api/matches/{id}/review`，正文 `{"action":"approve","creator_id":"tech","note":"Reviewed"}`。之后 POST `/api/renders`，正文 `{"match_job_id":"..."}`。视频完成后通过 result.files 中的 URL 下载两种水印版本。

`POST /api/catalog` 接收 `{"items":[...]}`。项目内已有图片放到 `examples/assets/`，image 字段填写相对路径；不支持任意远程 URL 拉取。产品与达人 ID 不得冲突，import 是 upsert，不删除未传入条目。完整字段可在 `/docs` 查看。

## 故障处理

- Jev 没有配置 / 响应非法：任务失败，不返回基线冒充结果。
- worker 中断：90 秒租约到期后，在下一次领取时标记失败；检查后手动重试，最多三次。
- 渲染失败：检查 `data/jobs/{id}/render.log`。先运行 `npm run setup`，确认 Chrome、FFmpeg 和 Hypit runtime 可用。
- 语义模型下载失败：检查网络和模型文件访问；或主动切换 lexical，服务不会偷偷降级。
- 导出的任务视频是配对模板，30 秒展示片需运行 `npm run video:matrix`。归档 UGC 不等于自动视频生成供应商接入。

## 部署与备份

`deploy/compose.yaml` 提供匹配 API 和可选 Qdrant 容器。容器不包含 Chrome/Hypit 视频环境；视频请使用主机 worker。单机部署可定期通过 SQLite online backup API 备份数据库，并同步 `data/jobs`。不要在运行时只复制 `.sqlite3` 而遗漏 WAL。

核心配置与依赖锁定、生产监控、访问审计身份、数据删除策略、数据库迁移工具和灾备演练仍需部署者按环境完善。

启动匹配容器：

```sh
docker compose -f deploy/compose.yaml up --build -d api
docker compose -f deploy/compose.yaml exec api creator-network seed
```

容器仅包含原创演示素材；归档影片查看和完整 Hypit 渲染请使用克隆后的主机安装。可选 Qdrant 服务通过 `docker compose -f deploy/compose.yaml --profile semantic up -d qdrant` 单独启动，在主机运行 `QDRANT_URL=http://127.0.0.1:6333 CREATOR_RETRIEVAL=hybrid creator-network serve` 连接。
