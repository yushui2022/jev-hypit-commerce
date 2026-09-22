# Jev × Hypit Commerce

**让商品，匹配 AI 数字达人。**

Yeadon 发起的电商数字达人匹配原型。输入商品图片、名称和数字人库，使用 Jev 选择合适的创作者，再由 Hypit 输出商品与人物同步切换的矩阵视频。

当前版本已实现完整 CLI 流程，支持 1–200 组配对，不依赖本仓库之外的私有工程。示例使用原创插画及虚构商品，克隆后即可渲染，无需模型密钥。

```text
商品图 + 名称 ─→ 可选 Gemini 识图 ─→ Jev 匹配具体候选 ─→ storyboard.json ─→ Hypit ─→ MP4
                                      ↑
                         数字人图片 + 场景 / 风格描述
```

![原创插画样例渲染预览](docs/demo-preview.jpg)

## 三步跑通无密钥演示

需要 **Node.js 22+、Python 3.10+、FFmpeg / FFprobe、Chrome 或 Chromium**。已在 macOS 验证；Linux 可通过 `CHROME_PATH` 指定浏览器。Windows 尚未验证。

```sh
git clone https://github.com/Yeadon8888/jev-hypit-commerce.git
cd jev-hypit-commerce
npm ci
npm run setup
npm run demo
```

结果在 `output/demo/video.mp4`：15 秒、1280×720、30fps。开头一秒说明，中段商品与人物同步闪切，片尾展示仓库地址。默认无音轨，不包含参考视频配乐。

`setup` 会配置本地 Hypit 运行环境、安装 Inter 和思源黑体字体包并启动渲染服务。找不到浏览器时先设置：

```sh
export CHROME_PATH="/path/to/chrome"
```

**离线样例的配对是手工 fixture，不伪装成 AI 判断。** 示例中三个不同候选保证可观察配对切换；自己的输入可以包含更多人物和商品。

## 使用自己的商品和形象库

参考 `examples/catalog.json`：

```json
{
  "products": [{
    "id": "serum-01",
    "name": "植物精华",
    "image": "assets/serum.jpg",
    "visual_features": "绿色瓶身、米色标签，护肤品类"
  }],
  "avatars": [{
    "id": "creator-01",
    "image": "assets/creator.jpg",
    "description": "虚构成年创作者，米色上衣，绿色植物与护肤工作台背景"
  }]
}
```

图片路径相对于输入 JSON 所在目录。图片、商品名、场景描述保留在最终配对结果中。Jev 本身接收文本视觉特征；它不直接接收图片。模型返回的 confidence 不是准确率保证。

### 1. 可选：自动识图

已有 `visual_features` 可跳过。缺少时，把 TokensFactory 密钥放在环境变量 `TOKENSFACTORY_API_KEY`，然后：

```sh
python3 analyze.py input/catalog.json --output output/analyzed.json
```

使用 `gemini-3.8-flash`，支持本地 PNG、JPEG、WebP。会把商品图片发送到指定服务。人物图的生成不在本版本范围，数字人库由使用者提供。

### 2. 真实 Jev 匹配

在环境中设置 `JEV_API_KEY`，然后：

```sh
python3 commerce.py output/analyzed.json --output output/storyboard.json
# 若直接使用含 visual_features 的目录：
python3 commerce.py input/catalog.json --output output/storyboard.json
```

每件商品从给定人物候选中选一个，依据商品类别、可见风格与背景场景。允许多个商品匹配同一个候选，不强制一对一分配；不以面部推断国籍、性格或商业成效。

只想检查请求而不调用接口：

```sh
python3 commerce.py examples/catalog.json --prepare-only --output output/request.json
```

### 3. 导出视频

```sh
python3 render.py build output/storyboard.json --output output/my-video
```

结果：`output/my-video/video.mp4`。生成的 `main.svml`、`main.svs` 和 `main.svrun` 可继续编辑，或用 Hypit Studio 打开：

```sh
npx hypit studio --run output/my-video/main.svrun
```

## 项目结构

| 文件 | 职责 |
| --- | --- |
| `analyze.py` | 可选图片识别，生成商品视觉特征 |
| `commerce.py` | Jev 请求、校验和配对数据 |
| `render.py` | 整理素材、生成 Hypit 工程、渲染与导出 |
| `packages/commerce-scene` | 可接收任意配对数量的 Hypit 组件 |
| `examples` | 可分发的原创插画、虚构商品与离线配对 |
| `tests` | 输入、缺失素材、配对和接口边界测试 |

## 验证

```sh
npm test
npm run build
```

CI 执行类型检查、单元测试及演示工程生成，不调用收费接口。完整本地渲染由 `npm run demo` 验证。

## 边界与方向

当前是可运行的本地原型：静态形象卡动效，不是口型视频；没有账号登录、自动发帖、聊天、人格记忆或自动商业合作。未来围绕独立角色档案、持续故事、人工调整、效果评估和多 Agent 协作扩展。

图像识别和 Jev 调用可能产生服务费用，服务故障会明确报错，不用模拟结果替代。代码不保存密钥；`input/`、`output/` 和本地运行配置默认不进入 Git。更大批次需按业务成本与服务限制拆分。

## License

代码及原创示例素材：MIT，© 2026 Yeadon。Jev、Hypit 及模型服务分别遵循其自身条款。项目非官方出品。
