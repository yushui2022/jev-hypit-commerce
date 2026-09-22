# 高清矩阵影片组件

`@jev/hd-fast@1` 是 `productions/hd-fast` 26 秒影片的专用 Hypit 场景包。

- `src/activation.ts`：声明 Scene、Message 和图像输入，注册 Hypit 包。
- `src/render.ts`：开头一秒说明、快速商品与人物配对、矩阵扩张与 GitHub 片尾；按时间确定性渲染。
- `src/content.ts`：99 件商品及其角色类别、图集单元映射。保留原编号，缺少 096。

它使用五张 4×5 人物图集和 99 张高清商品图。更换图像可修改影片的 SVML；更换配对可编辑 content.ts；布局、时序与切换速度可在 render.ts 调整。修改后运行 `npm run build`。

这是特定成片的归档组件，包含历史迭代中隐藏的文案层；当前显示状态由样式及时间逻辑决定。通用可变数量配对使用另一个 `packages/commerce-scene` 组件。完整导出与品牌叠加说明见 [工程 README](../../productions/hd-fast/README.md)。
