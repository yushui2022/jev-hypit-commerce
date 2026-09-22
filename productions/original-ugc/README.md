# 原音乐、原节奏 + UGC · 26 秒

在原高清复刻版上仅替换填表后的一段人物展示：三栏静态人物改为真实生成的 UGC 片段，商品小图始终对应当前片段。保留原音乐及整条时间线，不延长成片。

- 0–1 秒：原来的一句话开场。
- 1–14.7 秒：原商品与人物逐格填入矩阵，速度和布局保持。
- 14.7–16.967 秒：香水、音箱支架、随行杯三栏 UGC 同时播放。
- 16.967–18.4 秒：跟原切点切换条纹包、香水、音箱支架。
- 18.4–23.1 秒：原版 12 → 24 → 40 → 60 → 99 的矩阵扩张。
- 23.1–26 秒：原 GitHub 片尾。

UGC 作为短促的动态商品展示嵌入，静音以完整保留原参考音轨。完整版带英语同期声的 UGC 仍在 `productions/advanced/assets/ugc/`。

[贯一科技版](videos/guanyi-original-ugc.mp4) · [Yeadon 版](videos/yeadon-original-ugc.mp4) · [双版本预览](index.html)

## 重新导出

```sh
npm ci
npm run setup
npm run video:original-ugc
```

输出到 `output/original-ugc/`，同时生成两个品牌版本。Hypit 工程入口 `runs/main.svrun`，场景组件 `packages/original-ugc/`。使用已有高清商品、人物和 UGC，无新模型请求。

原音轨和商品媒体的来源与范围见 [媒体说明](../hd-fast/MEDIA-NOTICE.md)。生成视频来源见 [UGC 记录](../advanced/GENERATION-TASKS.json)。

## 导出检查

两种水印成片均为 26 秒、1280×720、30fps。已抽帧核对两组三栏 UGC 与对应商品；解码后的音频 SHA-256 与原高清复刻版完全一致。
