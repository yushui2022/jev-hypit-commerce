# 技术表述与动态素材调研

## Jev

TypeSafe 官方说明 Jev 属于 System One Models，以 Reinforcement Learning for Calibrated Decisions（RLCD）进行校准决策，返回类型化决策及置信度。影片不展示未经验证的倍速、准确率或“零幻觉”承诺。

- https://typesafe.ai/
- https://docs.typesafe.ai/introduction

本项目实际使用 `choice` 问题，将已提取的商品特征与角色候选描述交给 Jev，得到角色类别/候选与 confidence。当前已存配对在类内轮换示意人物；不宣称是脸部性格分析或身份推断。图像理解由独立媒体模型完成。

## Hypit

使用 Hypit 0.2.12 的 SVML / SVRun、结构化场景包、程序化 VisualTrack、精确字体和视频采样、AudioTrack、多轨 Film 合成与 HyperFrames 渲染。UGC 视频由 TokensFactory 模型生成，Hypit 负责素材及动画的时间线编排。

- https://github.com/hypit-ai/hypit

## GitHub 人物动态素材

检索了以下项目：

- https://github.com/KlingAIResearch/LivePortrait ：人物动画驱动工具，可以从图像和驱动信息合成人物动作；不是与本项目角色及商品对应的即用 UGC 素材库。
- https://github.com/tcwang0509/TalkingHead-1KH ：YouTube 说话人研究数据集，项目说明个人视频为 CC BY 3.0，脚本与元数据另有许可；素材不对应当前虚构角色或商品交互。
- https://github.com/taichuai/awesome-human-video-generation-corpus ：人物视频数据集索引，主要面向研究。

本片没有挪用上述人物素材。采用用户指定的 TokensFactory，以当前人物和对应商品作为双参考，生成 4 条新的 UGC。
