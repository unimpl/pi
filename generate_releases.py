#!/usr/bin/env python3
"""Generate the release chapter from a frozen archive without refreshing source evidence."""
import html
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
TITLE = "从发版记录理解功能演进"
NAV = f'<a href="releases.html"><span>10</span>{TITLE}</a>'


def generate():
    releases = json.loads((HERE / "releases/releases.json").read_text())
    manifest = json.loads((HERE / "releases/manifest.json").read_text())
    by_tag = {release["tag_name"]: release for release in releases}
    template = (HERE / "index.html").read_text()
    template = template.replace(NAV, "")
    template = template.replace('<a href="reference.html">术语与阅读路线</a>', NAV + '<a href="reference.html">术语与阅读路线</a>')
    footer = f'<footer class="page-footer">Pi 设计读本 · GitHub 发版记录研究<br>抓取日期 {manifest["fetched_at"][:10]} · {len(releases)} 条记录<br><a href="releases/manifest.json">发版证据清单</a></footer>'

    def shell(slug, title, body, toc):
        page = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)} · Pi 设计读本</title>", template)
        page = page.replace('data-page="index"', f'data-page="{slug}"')
        if slug == "releases":
            page = page.replace(NAV, NAV.replace('<a href=', '<a aria-current="page" href='))
        page = re.sub(r'<main id="main" tabindex="-1">.*?</main>', lambda _: f'<main id="main" tabindex="-1">{body}{footer}</main>', page, flags=re.S)
        toc_html = '<span>本页内容</span>' + ''.join(f'<a href="#{key}">{html.escape(label)}</a>' for key, label in toc) + '<a href="#main">回到顶部</a>'
        return re.sub(r'<aside class="page-toc" aria-label="本页目录">.*?</aside>', lambda _: f'<aside class="page-toc" aria-label="本页目录">{toc_html}</aside>', page, flags=re.S)

    def citation(match):
        tag = match[1]
        release = by_tag[tag]
        return f'<a href="release-archive.html#{tag}">{tag}（{release["published_at"][:10]}）</a>'

    content = (HERE / "releases-chapter.html.inc").read_text()
    content = re.sub(r"\{\{(v[0-9.]+)\}\}", citation, content)
    content = content.replace("{{coverage}}", f'截至 {manifest["fetched_at"][:10]}，分页获取 {manifest["page_count"]} 页，共 {len(releases)} 条已发布记录；按发布时间覆盖 {releases[0]["tag_name"]}（{releases[0]["published_at"][:10]}）至 {releases[-1]["tag_name"]}（{releases[-1]["published_at"][:10]}）。')
    assert "{{" not in content, "Unresolved release citation"
    toc = re.findall(r'<h2 id="([^"]+)">([^<]+)</h2>', content)
    pager = '<nav class="chapter-pager" aria-label="上下章"><a href="principles.html">上一页<br><strong>把实现读成设计判断</strong></a><a href="reference.html">下一页<br><strong>术语与阅读路线</strong></a></nav>'
    (HERE / "releases.html").write_text(shell("releases", TITLE, content + pager, toc))

    archive = '<h1>全部发版记录</h1><p class="lead">GitHub Releases 原文快照。按发布时间从早到晚排列，点击版本展开原始 Markdown；不执行原文中的 HTML、脚本或命令。</p><p><a href="releases.html">返回第十章</a> · <a href="releases/releases.json">下载 JSON</a> · <a href="releases/manifest.json">抓取与校验信息</a></p><p>原文中的相对 Markdown 链接保持原样；在线阅读可点击每条记录的 GitHub 原始发布页。原文里的旧仓库名和当时的配置建议不作改写。</p><h2 id="all">版本索引</h2><p>'
    archive += ' · '.join(f'<a href="#{r["tag_name"]}">{r["tag_name"]}</a>' for r in releases) + '</p>'
    for release in releases:
        tag = release["tag_name"]
        status = "预发布" if release["prerelease"] else "正式发布记录"
        archive += f'<section class="prose-section" id="{tag}"><h2>{tag}</h2><p>{release["published_at"]} · {status} · <a rel="external" href="{html.escape(release["html_url"], quote=True)}">GitHub 原始发布页</a></p><details class="evidence"><summary>展开 {tag} 原文</summary><pre style="white-space:pre-wrap;overflow-wrap:anywhere"><code>{html.escape(release["body"] or "（此记录没有正文）")}</code></pre></details></section>'
    (HERE / "release-archive.html").write_text(shell("release-archive", "全部发版记录", archive, [("all", "版本索引")]))

    for path in HERE.glob("*.html"):
        if path.name in {"releases.html", "release-archive.html"}:
            continue
        page = path.read_text().replace(NAV, "")
        page = page.replace('<a href="reference.html">术语与阅读路线</a>', NAV + '<a href="reference.html">术语与阅读路线</a>')
        if path.name == "principles.html":
            page = page.replace('<a href="reference.html">下一页<br><strong>术语与阅读路线</strong></a>', f'<a href="releases.html">下一页<br><strong>{TITLE}</strong></a>')
        if path.name == "index.html":
            page = page.replace("九章，一条阅读路径", "十章，一条阅读路径")
            page = page.replace("最后一章把代码归纳成设计判断。", "第九章把代码归纳成设计判断；第十章从发版记录回看功能演进。")
            if 'class="chapter-list-number">10</span>' not in page:
                card = f'<a href="releases.html"><span class="chapter-list-number">10</span><div><h3>{TITLE}</h3><p>从全部发版记录中识别能力边界、迁移成本与实验方向。</p></div><span class="chapter-level">演进</span></a>'
                page = page.replace('</div></section><section><h2 id="use">', card + '</div></section><section><h2 id="use">')
        if path.name == "evidence.html" and 'id="release-evidence"' not in page:
            page = page.replace('<h2 id="industry">', '<h2 id="release-evidence">发版记录证据</h2><p>第十章依据独立抓取的 GitHub Releases 快照，覆盖范围与日期不等同于以上代码基线。<a href="releases.html">阅读功能演进</a> · <a href="release-archive.html">核对全部原文</a> · <a href="releases/manifest.json">抓取清单</a>。历史说明不自动证明某能力在当前默认运行路径启用。</p><h2 id="industry">')
        path.write_text(page)

    search_path = HERE / "assets/search-index.js"
    search = json.loads(search_path.read_text().removeprefix("window.STUDY_SEARCH = ").rstrip(";\n"))
    search = [item for item in search if not item["url"].startswith(("releases.html", "release-archive.html"))]
    for key, label in toc:
        section = re.search(rf'<section[^>]*aria-labelledby="{re.escape(key)}"[^>]*>(.*?)</section>', content, re.S)
        if section:
            text = html.unescape(re.sub(r"<[^>]+>", " ", section[1]))
            search.append({"title": f"10 {TITLE} / {label}", "url": f"releases.html#{key}", "text": text})
    for release in releases:
        search.append({"title": f'发版原文 / {release["tag_name"]}', "url": f'release-archive.html#{release["tag_name"]}', "text": release["body"] or "（此记录没有正文）"})
    search_path.write_text("window.STUDY_SEARCH = " + json.dumps(search, ensure_ascii=False) + ";\n")
    print(f"Generated release chapter and {len(releases)} archived releases; integrated navigation and search.")


if __name__ == "__main__":
    generate()
