# Contributing

优先贡献：商品与达人相关性标注、检索评估、渲染模板、供应商适配器、可观测性和工作台体验。

1. Fork / 创建分支；安装 `pip install -e '.[test]'` 和 `npm ci`。
2. 保持召回、Jev 决策、人工审核三种来源明确分离。
3. 修改状态机或供应商接口时补充失败和边界测试。
4. 运行 `pytest -q`、`creator-network evaluate`、`npm run build`。
5. PR 写清用户行为改变、验证范围和仍未覆盖的环境。

不提交 API keys、运行数据库、人物私密信息或无权公开的媒体。不接受虚构 benchmark、star 数、客户案例或未实现能力的宣传。
