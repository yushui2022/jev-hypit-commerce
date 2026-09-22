# 高清商品 × 数字达人快闪 · Hypit 完整工程

无 UGC 的归档基准版：原音乐与原节奏的 26 秒高清复刻版，1280×720、30fps。包含 99 张真实商品主图、5 张生成式人物图集、现有配对数据、时间线、场景组件、音乐、品牌图及两份 MP4。

[![贯一科技版预览](preview.jpg)](videos/guanyi-hd.mp4)

- [打开双版本预览页](index.html)
- [观看 / 下载贯一科技版](videos/guanyi-hd.mp4)
- [观看 / 下载 Yeadon 版](videos/yeadon-hd.mp4)
- [编辑时间线](authors/main.svml)
- [编辑动效与布局](../../packages/hd-fast/src/render.ts)
- [编辑商品与角色映射](../../packages/hd-fast/src/content.ts)

## 从仓库重新导出

在仓库根目录运行（环境要求见主 README）：

```sh
npm ci
npm run setup
npm run video:hd
```

导出到 `output/hd-fast/guanyi-hd.mp4` 和 `output/hd-fast/yeadon-hd.mp4`。无需 Jev 或图像模型密钥：本工程重放已保存的匹配结果，不重新调用模型。

Hypit 负责完整画面和音轨；`export.py` 最后通过 FFmpeg 叠加品牌署名，生成与发布版本相同设计的两种成片。不同渲染环境下编码文件不保证逐字节相同。

打开可编辑工程：

```sh
npm run build
npx hypit studio --run productions/hd-fast/runs/main.svrun
```

Studio 展示叠加品牌署名前的完整基础时间线。署名位置和尺寸在 `export.py` 中修改。

## 文件说明

| 路径 | 内容 |
| --- | --- |
| `authors/main.svml`、`main.svs` | 26 秒时间线、素材引用、画布与样式 |
| `runs/main.svrun` | 渲染入口 |
| `../../packages/hd-fast/src` | Hypit 场景组件、动效和已保存配对 |
| `assets/products` | 99 张高清商品图，600–5120 像素 |
| `assets/avatars` | 5 张合计 100 个虚构成年人物的图集 |
| `assets/branding` | 贯一科技、Yeadon 透明署名 |
| `assets/soundtrack.wav` | 当前成片使用的参考音轨 |
| `videos` | 已导出的两份 MP4 |
| `assets-manifest.json` | 107 个媒体文件的 SHA-256 校验 |
| `NEXT-VERSION.md` | 进阶版创意方案与实现记录 |

校验原始发布素材：`python3 productions/hd-fast/export.py --check-assets`。主动替换素材后无需保持原始哈希。

## 素材与匹配说明

商品来自用户提供的商品目录，按相同商品 ID 获取高清主图；编号 096 在 US 地区不可用，已移除。本工程保留原商品编号，因此 095 后是 097。

Jev 为商品选择 beauty / style / active / home / tech 角色类别，类别内轮换示意人物；这支影片不代表逐张人脸的匹配评分，也不展示真实人物口型表演。生成头像为面向美国电商场景设计的虚构角色。

当前音轨沿用[Hypit.ai 参考视频](https://weixin.qq.com/sph/AUNjS9Tfh7)，尚未换成下一版讨论的新配乐。商品图片、音乐、品牌标识及生成媒体不随代码的 MIT 许可证授予第三方权利；详见 [MEDIA-NOTICE.md](MEDIA-NOTICE.md)。原始 Excel、服务密钥、调用日志和本机配置不在工程中。

## 当前剪辑方向

按 2026-09-22 的最新反馈，恢复此版作为后续微调的基准：保留原音乐、原卡点、逐格填入和矩阵扩张；保留高清商品、一句话开场、GitHub 片尾和双水印。后续调整集中在局部清晰度与版面，不延长解释或重排整条节奏。30 秒 UGC 版与 42 秒进阶版作为试验归档保留。

最新交付已在保留本版音乐与切点的基础上接入 UGC，见 [原节奏 + UGC](../original-ugc/README.md)。
