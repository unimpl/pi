# Pi 设计读本

在线阅读：<https://unimpl.github.io/pi/>。

也可以直接用浏览器打开 `index.html`。所有页面、图表、搜索数据与源码快照均已生成，不需要安装依赖或联网。

本地预览：

```sh
./serve.sh
```

默认访问 http://127.0.0.1:8765 。也可以指定其他端口，例如 `./serve.sh 9000`。关闭 JavaScript 后正文、图表和代码仍可读，移动目录与搜索不可用。

## 内容与证据

- `content.py`：前九章正文、术语和 Mermaid 源定义。
- `releases.html`：第十章「从发版记录理解功能演进」，按能力边界提炼重大变化，含迁移表与自测。
- `releases-chapter.html.inc` / `generate_releases.py`：第十章正文源与独立生成器，自动接入目录、前后章导航和全文搜索。
- `release-archive.html` / `releases/`：全部 263 条 GitHub 发版原文及抓取清单，覆盖 v0.12.0 至 v0.87.1（抓取于 2026-09-24）。
- `generate.py`：生成静态 HTML、全文搜索索引、源码摘录、完整源码快照和哈希清单。
- `diagrams/`：Mermaid 图表定义及离线预渲染结果。
- `assets/`：离线 CSS、原生 JavaScript 与数据。
- `sources/`：带行号锚点的源码快照。
- `manifest.json`：代码提交、生成日期、工作区差异和引用文件哈希。
- `PRODUCT.md` / `DESIGN.md`：受众、目标和视觉约定。

正文中的当前实现、项目文档和分析推断分别标识。研究对象是本地代码快照，不宣称完整安全审计或行业排名。新协议与持久化架构单独说明其演进状态。

第十章采用独立的 GitHub Releases 证据基线，区分正式功能、实验功能、示例和后续移除项；它不自动更新前九章的源码结论。原文可离线阅读，在线引用仅链接到 GitHub 发布页，不加载远程资源。

## 更新读本

此仓库保存预生成网站。重新生成源码证据时，需要把本目录作为 Pi 源码仓库中的 `study/`，因为生成器会读取相邻的 `packages/`。先重新核对正文中的行为和推断，再运行：

```sh
npm ci --prefix study --ignore-scripts
python3 study/generate.py
node study/render-diagrams.mjs
python3 study/verify.py
node --check study/assets/book.js
```

Python 需要 3.9+；图表工具只用于制作，精确锁定在此目录的独立 package-lock 中，不修改仓库工作区依赖。`beautiful-mermaid` 根据 Mermaid 语法渲染 SVG，页面运行时不加载渲染器。

实际验证结果见 `VALIDATION.md`。图表和页面生成不需要调用模型 API。

只更新发版章节时，可直接在本目录执行，无需相邻源码仓库：

```sh
python3 generate_releases.py
python3 verify.py
```

发版快照不会在生成时联网刷新。采集命令与各条正文 SHA-256 见 `releases/manifest.json`；更新快照后应重新阅读新增／修订记录、更新正文和清单，再生成页面。完整 `generate.py` 也会调用发版章节生成器。独立目录验证从既有源码 HTML 快照重建内容并核对哈希；若相邻源码存在，则继续核对真实源码。

## 维护约定

默认使用轻量静态页面，不添加远程字体、CDN、遥测或后端。源码正文需 HTML 转义；搜索查询只生成文本节点。图表统一使用 Mermaid 定义，不增加手写 SVG 图表或动画。

代码摘录来自本仓库，遵循根目录 MIT 许可。图表使用独立的 MIT 渲染工具生成；工具包通过 npm 安装时保留其自身许可，站点不分发其运行时代码。
