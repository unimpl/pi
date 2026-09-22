#!/usr/bin/env python3
"""Generate the offline study book and exact, line-addressable source evidence."""

import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
from datetime import date

from content import CHAPTERS, CHAPTER_CHECKS, CHAPTER_GUIDES, DIAGRAMS, GLOSSARY

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ESC = html.escape
COMMIT = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
STATUS = subprocess.check_output(["git", "status", "--short", "--", ".", ":(exclude)study"], cwd=ROOT, text=True).strip()
SOURCES = {}
SEARCH = []


def plain(value):
    return html.unescape(re.sub(r"<[^>]+>", " ", value))


def source_name(path):
    return path.replace("/", "--") + ".html"


def evidence(path, needle, count, reason):
    source = (ROOT / path).read_text()
    lines = source.splitlines()
    matches = [i for i, line in enumerate(lines) if needle in line]
    if len(matches) != 1:
        raise ValueError(f"Evidence anchor must match once: {path}: {needle!r} ({len(matches)})")
    start = matches[0]
    SOURCES[path] = {"sha256": hashlib.sha256(source.encode()).hexdigest(), "lines": len(lines)}
    excerpt = "\n".join(f"{i + 1:4}  {lines[i]}" for i in range(start, min(start + count, len(lines))))
    return f'''<details class="evidence"><summary>{ESC(reason)}</summary><p class="source-path">{ESC(path)} · L{start + 1}</p><pre><code>{ESC(excerpt)}</code></pre><a href="sources/{source_name(path)}#L{start + 1}">查看本地源码快照与行号</a></details>'''


def figure(key):
    title, description, mermaid = DIAGRAMS[key]
    (HERE / "diagrams" / f"{key}.mmd").write_text(mermaid)
    return f'''<figure class="diagram"><div class="diagram-head"><span>{ESC(title)}</span></div><img src="diagrams/{key}.svg" alt="{ESC(description)}" loading="lazy"><figcaption>{ESC(description)}</figcaption></figure>'''


def chapter_guide(slug):
    guide = CHAPTER_GUIDES[slug]
    return f'''<section class="chapter-guide" aria-labelledby="design-lens"><div class="guide-heading"><h2 id="design-lens">本章先抓什么</h2><span>{ESC(guide["priority"])}</span></div><dl><div><dt>为什么需要</dt><dd>{ESC(guide["why"])}</dd></div><div><dt>行业常见做法</dt><dd>{ESC(guide["industry"])}</dd></div><div><dt>自己实现时</dt><dd>{ESC(guide["build"])}</dd></div><div><dt>现在可以忽略</dt><dd>{ESC(guide["ignore"])}</dd></div></dl></section>'''


def chapter_check(slug):
    checks = CHAPTER_CHECKS[slug]
    questions = "".join(f"<li>{ESC(question)}</li>" for question, _ in checks)
    answers = "".join(
        f"<li><strong>{ESC(question)}</strong> {ESC(answer)}</li>" for question, answer in checks
    )
    return f'''<section class="prose-section self-check" aria-labelledby="self-check"><h2 id="self-check">本章自测</h2><p>先尝试独立回答，再展开参考答案。</p><ol class="question-list">{questions}</ol><details class="reference-answer"><summary>查看参考答案</summary><ol>{answers}</ol></details></section>'''


def shell(slug, title, body, toc=(), chapter=None):
    nav = ''.join(f'<a href="{c["slug"]}.html" {"aria-current=page" if c["slug"] == slug else ""}><span>{i:02}</span>{c["title"]}</a>' for i, c in enumerate(CHAPTERS, 1))
    toc_html = ''.join(f'<a href="#{key}">{ESC(label)}</a>' for key, label in toc)
    scripts = '<script src="assets/search-index.js" defer></script><script src="assets/book.js" defer></script>'
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="通过源码、图解与设计取舍理解 Pi Agent。面向有 Go、Rust、C++ 经验的开发者。"><title>{ESC(title)} · Pi 设计读本</title><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/book.css">{scripts}</head>
<body data-page="{slug}"><a class="skip" href="#main">跳到正文</a><header class="topbar"><a class="brand" href="index.html"><span class="brand-mark">π</span>Pi 设计读本</a><span class="top-caption">从代码，读懂设计。</span><a class="search-link" href="search.html">搜索全书</a><button class="menu-toggle js-only" type="button" aria-expanded="false" aria-controls="chapter-nav">目录</button></header>
<div class="book-layout"><aside class="sidebar" id="chapter-nav"><nav aria-label="章节"><a class="overview-link" href="index.html">阅读指南</a>{nav}<a href="reference.html">术语与阅读路线</a><a href="evidence.html">证据与版本说明</a></nav></aside>
<main id="main" tabindex="-1">{body}<footer class="page-footer">Pi 设计读本 · 本地源码研究<br>代码基线 <code>{COMMIT[:12]}</code> · {date.today().isoformat()}<br><a href="evidence.html">证据规则与分析边界</a></footer></main><aside class="page-toc" aria-label="本页目录"><span>本页内容</span>{toc_html}<a href="#main">回到顶部</a></aside></div><noscript><p class="noscript-note">JavaScript 已关闭：正文、源码、图表和章节导航仍可阅读；全文搜索需要 JavaScript。</p></noscript></body></html>'''


def add_search(title, url, body):
    SEARCH.append({"title": title, "url": url, "text": plain(body)})


def generate():
    for directory in ("assets", "diagrams", "sources"):
        (HERE / directory).mkdir(exist_ok=True)
    for number, c in enumerate(CHAPTERS, 1):
        toc = [("design-lens", "本章重点")] + [(s[0], s[1]) for s in c["sections"]]
        if c["slug"] in CHAPTER_CHECKS:
            toc.append(("self-check", "本章自测"))
        toc.append(("evidence", "源码证据"))
        body = f'<div class="chapter-meta">第 {number:02} 章 / {c["level"]}</div><h1>{c["title"]}</h1><p class="subtitle">{c["subtitle"]}</p><p class="lead">{c["intro"]}</p>'
        body += chapter_guide(c["slug"])
        body += figure(c["diagram"])
        for key, title, content in c["sections"]:
            body += f'<section class="prose-section" aria-labelledby="{key}"><h2 id="{key}">{title}</h2>{content}</section>'
            add_search(f'{number:02} {c["title"]} / {title}', f'{c["slug"]}.html#{key}', content)
        if c["slug"] in CHAPTER_CHECKS:
            body += chapter_check(c["slug"])
        body += '<section><h2 id="evidence">源码证据</h2><p class="muted">摘录来自本地代码快照。点开可核对原文和完整文件；项目文档与分析推断在正文单独标注。</p>'
        for args in c["evidence"]:
            excerpt = evidence(*args)
            body += excerpt
            add_search(f'{c["title"]} / {args[3]}', f'{c["slug"]}.html#evidence', excerpt)
        body += '</section><nav class="chapter-pager" aria-label="上下章">'
        prev = CHAPTERS[number - 2] if number > 1 else {"slug": "index", "title": "阅读指南"}
        nxt = CHAPTERS[number] if number < len(CHAPTERS) else {"slug": "reference", "title": "术语与阅读路线"}
        body += f'<a href="{prev["slug"]}.html">上一页<br><strong>{prev["title"]}</strong></a><a href="{nxt["slug"]}.html">下一页<br><strong>{nxt["title"]}</strong></a></nav>'
        (HERE / f'{c["slug"]}.html').write_text(shell(c["slug"], c["title"], body, toc, c))

    home = '''<h1 class="home-title">读懂 Pi，<br>理解 Agent 的设计。</h1><p class="subtitle">一本给系统开发者的源码设计读本。</p><p class="lead">你已有 Go、Rust、C++ 的经验。我们从熟悉的接口、状态和 I/O 出发，沿一次请求进入 pi：不仅看它如何工作，也看它为什么这样组织，以及这些选择的代价。</p><div class="home-actions"><a class="primary-link" href="foundations.html">开始阅读第一章</a><a href="architecture.html">先看架构地图</a></div>'''
    home += figure("concept")
    home += '''<section><h2 id="approach">先理解，再判断。</h2><p>不需要先学完整的 JavaScript，不安排实现练习。每章先说明设计动机、行业常见方案和实现取舍，再回到 Pi 的代码证据。全部图表由 Mermaid 描述并预渲染，离线打开也能阅读。</p><div class="reading-key"><p><strong>当前实现</strong>以本地源码和公开导出为证据。</p><p><strong>行业参照</strong>用于比较常见方案，不作为框架排名。</p><p><strong>实现判断</strong>明确必须先设计、按需加入和暂时忽略的部分。</p></div></section><section><h2 id="chapters">九章，一条阅读路径</h2><p>第一至七章是 Agent 与 Harness 的核心；基础设施章按需了解；最后一章把代码归纳成设计判断。</p><div class="chapter-list">'''
    for i, c in enumerate(CHAPTERS, 1):
        home += f'<a href="{c["slug"]}.html"><span class="chapter-list-number">{i:02}</span><div><h3>{c["title"]}</h3><p>{c["subtitle"]}</p></div><span class="chapter-level">{c["level"]}</span></a>'
    home += '</div></section><section><h2 id="use">让阅读有一个落点</h2><p>贯穿案例是“读取 README.md 并解释项目”。请求循环、工具失败分支和上下文压缩都以 Mermaid 图和文字轨迹解释，不运行真实工具，也不请求模型。</p><p>第一遍只读“本章先抓什么”和图解，第二遍读正文，第三遍展开源码证据。读完后应能判断自己的 Agent 或 Harness 必须实现哪些边界，哪些复杂度可以推迟。</p><p>可离线使用；无账号、无遥测。源码版本、行业参照与研究范围见<a href="evidence.html">证据说明</a>。</p></section>'
    (HERE / "index.html").write_text(shell("index", "阅读指南", home, [("approach", "如何阅读"), ("chapters", "章节路径"), ("use", "使用说明")]))

    reference = '<h1>术语与阅读路线</h1><p class="lead">遇到陌生名词时回到这里。先理解角色和时间边界，再追踪具体实现。</p><h2 id="glossary">术语表</h2><dl class="glossary">'
    for term, meaning, slug in GLOSSARY:
        reference += f'<dt>{ESC(term)}</dt><dd>{ESC(meaning)} <a href="{slug}.html">阅读相关章节</a></dd>'
    reference += '</dl><h2 id="route">三遍阅读源码</h2><ol class="route-list"><li><strong>第一遍：数据与边界。</strong>先看 agent/types.ts 的 StreamFn、AgentTool、AgentEvent，再看 ai/types.ts 的消息角色。只回答“数据由谁提供、流向哪里”。</li><li><strong>第二遍：执行与结算。</strong>读 agent-loop.ts 的 runLoop、streamAssistantResponse、executeToolCalls，再读 agent.ts 的 processEvents 与 finishRun。把每个 await 前后发生的事情串起来。</li><li><strong>第三遍：产品与演进。</strong>读 SDK 装配、messages.ts 转换、compaction 切点与摘要，再读运行时替换。之后才进入 Chord 和新存储方案，并核对公开导出与设计文档的差距。</li></ol><h2 id="principle-index">设计原则索引</h2><ul><li><a href="principles.html#contracts">变化在边界收敛</a>：类型、转换与协议适配。</li><li><a href="principles.html#state">区分事实、视图与过程</a>：会话、上下文、运行状态。</li><li><a href="principles.html#ordering">把时间顺序写成契约</a>：并发、事件和结算。</li><li><a href="principles.html#effects">保守处理副作用</a>：不完整参数、取消与恢复。</li><li><a href="principles.html#extension">可扩展且责任可见</a>：注入、工具和生命周期。</li></ul>'
    add_search("术语与阅读路线", "reference.html", reference)
    (HERE / "reference.html").write_text(shell("reference", "术语与阅读路线", reference, [("glossary", "术语表"), ("route", "源码路线"), ("principle-index", "原则索引")]))

    evidence_body = f'<h1>证据与版本说明</h1><p class="lead">把代码事实、文档说明和设计判断分开，才能从一个真实项目中学到可迁移的经验。</p><h2 id="baseline">研究基线</h2><dl class="glossary"><dt>Git 提交</dt><dd><code>{COMMIT}</code></dd><dt>生成日期</dt><dd>{date.today().isoformat()}</dd><dt>study 之外的工作区差异</dt><dd><pre>{ESC(STATUS or "无：分析基线为干净工作区。")}</pre></dd></dl><p>每份引用文件保存 SHA-256 和离线 HTML 快照。下面的链接指向本书快照，源码更新后行号可能变化；生成脚本会验证摘录锚点，但不会自动证明正文仍然正确。</p><h2 id="method">证据等级与研究范围</h2><p><strong>当前实现：</strong>基础循环、Agent 包装、SDK 装配、应用消息转换、工具修改队列与压缩函数依据代码分析。源码快照是证据资料，不代表本书对其每一行都做了安全审计。</p><p><strong>项目文档：</strong>会话树的产品行为、Chord、实验协议和服务模块主要依据各自文档及公开入口。文档中的目标不能直接视为所有路径已经完成。本书没有把新版 Durable 设计宣称为当前 CLI 默认运行时。</p><p><strong>分析推断：</strong>原则、收益、代价、语言类比和替代方案属于分析。没有进行行业产品排名，也没有执行真实模型请求或整个仓库的功能测试。</p><h2 id="industry">行业参照</h2><p>“行业常见做法”来自 2026-09-19 核对的官方材料，提炼设计类型而非评比产品：Anthropic《Building Effective AI Agents》用于区分固定工作流与自主 Agent；OpenAI Agents SDK 文档用于工具循环、会话、运行预算和 tracing；LangGraph 文档用于 checkpoint、interrupt 与持久执行；Pydantic AI 文档用于类型化工具与工作流引擎集成；Microsoft AutoGen 文档用于事件驱动运行时。外部资料会演进，因此它们只支撑对比，不覆盖 Pi 本地源码证据。</p><ul class="reference-list"><li>Anthropic Engineering — Building Effective AI Agents</li><li>OpenAI Agents SDK — Running Agents, Sessions, Tracing</li><li>LangGraph — Durable Execution and Interrupts</li><li>Pydantic AI — Capabilities and Durable Execution</li><li>Microsoft AutoGen — Core and AgentChat Programming Models</li></ul><h2 id="sources">离线源码索引</h2><ul class="source-list">'
    for path in sorted(SOURCES):
        evidence_body += f'<li><a href="sources/{source_name(path)}">{ESC(path)}</a><small>{SOURCES[path]["lines"]} 行 · SHA-256 {SOURCES[path]["sha256"][:16]}</small></li>'
    evidence_body += '</ul><p><a href="manifest.json">查看完整证据清单 JSON</a> · <a href="VALIDATION.md">查看交付验证记录</a></p>'
    (HERE / "evidence.html").write_text(shell("evidence", "证据与版本说明", evidence_body, [("baseline", "研究基线"), ("method", "证据等级"), ("industry", "行业参照"), ("sources", "源码索引")]))
    for path in SOURCES:
        lines = (ROOT / path).read_text().splitlines()
        source_html = '\n'.join(f'<span id="L{i}"><a href="#L{i}" aria-label="第 {i} 行">{i:4}</a> {ESC(line)}</span>' for i, line in enumerate(lines, 1))
        (HERE / "sources" / source_name(path)).write_text(f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{ESC(path)} · 源码快照</title><link rel="stylesheet" href="../assets/book.css"></head><body class="source-page"><header><a href="../evidence.html">返回证据索引</a><h1>{ESC(path)}</h1><p>本地快照 · {COMMIT[:12]} · {date.today().isoformat()}</p></header><pre class="source-code"><code>{source_html}</code></pre></body></html>')
    search_body = '<h1>搜索全书</h1><p class="lead">搜索正文、术语和源码摘录。支持中文、函数名和多个关键词；全部在本地完成。</p><form class="search-form js-only" role="search"><label for="query">关键词</label><div><input id="query" type="search" placeholder="例如：取消、上下文、StreamFn" autocomplete="off"><button type="submit">搜索</button></div></form><p id="search-status" role="status">输入关键词，查找相关段落。</p><div id="search-results"></div><noscript><p>全文搜索需要 JavaScript。也可使用章节目录和浏览器的页内查找。</p></noscript>'
    (HERE / "search.html").write_text(shell("search", "搜索全书", search_body))
    (HERE / "assets/search-index.js").write_text('window.STUDY_SEARCH = ' + json.dumps(SEARCH, ensure_ascii=False) + ';\n')
    (HERE / "manifest.json").write_text(json.dumps({"commit": COMMIT, "date": date.today().isoformat(), "workspaceDiffOutsideStudy": STATUS, "sources": SOURCES, "diagramRenderer": "beautiful-mermaid@1.1.3"}, ensure_ascii=False, indent=2) + '\n')
    print(f"Generated 13 reading pages, {len(SOURCES)} source snapshots, {len(SEARCH)} search entries.")


if __name__ == "__main__":
    generate()
