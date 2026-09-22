# 矩阵 → UGC · 30 秒双版本

开头只保留「让商品，自动匹配 AI 数字达人」，随后立即进入大商品图、大人物图、右侧矩阵逐格填入。UGC 在填满后出现，不打断商品与人物对应关系。

- **0–1s**：一句开场
- **1–12s**：99 组商品与人物快闪，矩阵逐格填满
- **12–24s**：4 段 UGC，各 3 秒，保留同期英语声音
- **24–27s**：人物与商品矩阵扩张
- **27–30s**：Jev × Hypit 与真实 GitHub 地址

[贯一科技 MP4](videos/guanyi-matrix-ugc.mp4) · [Yeadon MP4](videos/yeadon-matrix-ugc.mp4)

![关键画面](preview.jpg)

## 编辑和重现

```sh
npm ci
npm run setup
npm run video:matrix
```

在根目录运行。输出在 `output/matrix-ugc/`，每次同时生成 `guanyi-matrix-ugc.mp4` 和 `yeadon-matrix-ugc.mp4`。基础画面统一，品牌在最后一步独立叠加。

- `authors/main.svml`：资源、音轨与时间线
- `runs/main.svrun`：可编辑 Hypit 入口
- `packages/matrix-ugc/src/render.ts`：填格、快闪、UGC 采样和矩阵扩张
- 高清商品与人物来自 `productions/hd-fast/assets/`
- UGC 与原始提示词来自 `productions/advanced/`
- 配乐为项目原创电子编排，非参考视频原曲

此版本复用已生成的 UGC，无需再次调用付费模型。生成片段可能有手部 / 包装文字变化，应作为合成演示素材而非真实使用证言。媒体使用范围继承 [高清素材说明](../hd-fast/MEDIA-NOTICE.md) 和 [UGC 来源记录](../advanced/GENERATION-TASKS.json)。

## 交付约定

从本版开始，后续每次品牌视频交付必须同时提供「贯一科技」与「Yeadon」。开头保持一句话，不恢复长机制解说；商品与人物填入矩阵优先，UGC 排在其后。
