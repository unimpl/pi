# 验证记录

验证日期：2026-09-23。源码基线见 `manifest.json`。

## 已通过

- `python3 study/verify.py`：44 个 HTML 页面、18,737 个本地链接/锚点、9 张 Mermaid 图和 30 份引用文件哈希全部通过。
- 九张图全部由 Mermaid 定义并预渲染；页面不含手写 SVG 图表、动画、图表下载入口或 Mermaid 源文件入口。
- `node --check study/assets/book.js` 与 `node --check study/render-diagrams.mjs`：语法检查通过。
- 所有预渲染结果均为合法 XML，无脚本、foreignObject、远程字体或外部资源；生成器移除了渲染工具自动加入的 Google Fonts 导入。
- 每章均包含“为什么需要、行业常见做法、自己实现时、现在可以忽略”四项设计判断，并标注掌握优先级。
- 第一章以 Pi 对象模型为主线，区分 AgentSession、SessionManager、Agent、run、turn、message、toolCall、toolResult、Model 与 StreamFn，并用 Mermaid 表示包含关系和执行顺序。
- 九章均提供自测问题和默认折叠的参考答案；使用原生 details/summary，无 JavaScript 时仍可展开并支持键盘操作。
- 内置浏览器验证：桌面与移动端 390×844 无横向溢出，Mermaid 图正常加载；移动端重点框改为单列，目录按钮可见。
- 页面中不存在阅读进度、localStorage 进度数据、教学动画或演示控制；JavaScript 仅用于移动目录和本地全文搜索。
- 基础设施章节已压缩为模块定位、问题边界和引入时机；Chord、protocol、Durable 不作为基础实现要求。
- Git 检查：仅新增 `study/`；未修改产品代码、根依赖元数据或锁文件，未提交 Git。

## 检查限制

根目录 `npm run check` 已执行：Biome 检查 1,363 个文件，无修改；固定版本、运行依赖、TS 导入、入口图、shrinkwrap、install-lock 检查均通过。在 `tsgo --noEmit` 阶段失败，后续 browser-smoke 未运行。

当前工作区不存在 `packages/ai/src/providers/data/`，模型目录导入被推断为 `unknown`，继而出现模型 ID 参数为 `never` 等类型错误，涉及现有 ai/agent/coding-agent 源码和测试。本次只增加静态学习网站，没有通过修改产品类型或生成模型目录绕过这些错误。

安装根检查依赖时使用 `npm ci --ignore-scripts`；因默认 npm 缓存存在权限问题，改用临时缓存。最终检查使用本机已提供的 Node 24.19.0。安装过程仍有既有依赖的 engine/deprecation 提示；未更改它们。

设计检测器返回空发现列表，但缺少 HTML/CSS 解析依赖，降级为正则检查；这不构成完整的无障碍或对比度审计。

内置浏览器策略禁止访问 `file://`，因此未进行直接打开本地 HTML 的浏览器实测，也未尝试绕过该策略。页面使用相对资源、经典脚本和预渲染内容，无 fetch/CDN 依赖；静态完整性检查和本地 HTTP 预览均已通过。推荐使用本地 HTTP 预览，以获得一致的导航和搜索行为。

未运行真实模型、真实工具副作用、根 build 或完整测试套件。本书引用已有测试作为设计证据，不将这些测试标记为本次已运行。
