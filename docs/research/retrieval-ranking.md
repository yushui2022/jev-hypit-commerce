# 商品 → 数字达人：检索与排序选型

研究日期：2026-09-22。以下是公开一手资料，未复制其业务实现，也没有把未接入系统描述为已接入。

| 项目 | 可借鉴能力 | 本仓库的选择 |
|---|---|---|
| [Qdrant](https://github.com/qdrant/qdrant) | 向量检索、payload 过滤、hybrid query | 实际可选依赖；存文字描述向量，过滤当前有效候选 |
| [FastEmbed](https://github.com/qdrant/fastembed) | 本地轻量 embedding，支持检索相关组件 | 实际可选依赖；使用 BGE small 英文 embedding |
| [Gorse](https://github.com/gorse-io/gorse) | 推荐服务、不同召回源、任务与反馈层次 | 参考其服务分层；未引入 Gorse 服务或训练模型 |
| [FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) | BGE 检索与 reranker 生态 | 模型选型参考；未集成其训练框架或交叉编码器 |

## 为什么不是“快速排序一下”

排序算法并不提供商品与达人的相关性。需要先定义画像和相关性，再通过检索减少候选，最后做决策。Qdrant 官方的 [Hybrid Queries](https://qdrant.tech/documentation/search/hybrid-queries/) 和 [FastEmbed reranking](https://qdrant.tech/documentation/fastembed/fastembed-rerankers/) 都区分了召回与后续排序。

本项目先落地：资格过滤 → BM25 / dense 召回 → RRF → Top K → Jev choice → 人工审核。RRF 只融合顺序，不能解读为匹配概率。Jev 的返回置信度也不能直接当成转化率。

[Jev 官方文档](https://docs.typesafe.ai/introduction) 提供结构化决策接口。本仓库用真实的 `choice` 契约限定候选；没有声称调用其不存在的快速排序 API。当前向量匹配是**描述级语义**，图像需要先有可信描述。

## 本次没有引入的复杂度

- 没有足够真实点击 / 转化标签，暂不训练协同过滤或学习排序模型。
- 没有大规模向量压力，Qdrant 作为可选适配器，默认 BM25 能独立运行。
- 没有跨租户隔离需求的完整实现，明确保持单工作空间模式。
- 没有为展示引入 Kubernetes、Kafka 或空壳 Agent 微服务。

## 许可与模型选择

上述项目代码的许可与具体模型权重许可应分别检查。本仓库不打包第三方权重；首次启用语义检索由 FastEmbed 下载配置模型。官方 reranking 教程里的示例模型不代表均可商用，未来更换模型时应逐个核对模型卡和许可。
