#!/usr/bin/env python3
"""Check offline integrity, source fidelity, links, anchors and teaching traces."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from content import CHAPTERS, CHAPTER_GUIDES, DIAGRAMS

ROOT = Path(__file__).resolve().parent


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.h1 = 0
        self.path = path
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            assert attrs["id"] not in self.ids, f"Duplicate id: {self.path}: {attrs['id']}"
            self.ids.add(attrs["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "img":
            assert attrs.get("alt"), f"Missing image description: {self.path}"
        for attr in ("href", "src"):
            if attrs.get(attr):
                self.links.append(attrs[attr])


pages = {path.resolve(): Page(path) for path in list(ROOT.glob("*.html")) + list((ROOT / "sources").glob("*.html"))}
link_count = 0
for path, page in pages.items():
    assert page.h1 == 1, f"Expected one h1: {path}"
    for link in page.links:
        parsed = urlsplit(link)
        assert not parsed.scheme and not parsed.netloc, f"External dependency/link: {path}: {link}"
        target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
        assert target.is_relative_to(ROOT), f"Link escapes standalone book: {link}"
        assert target.exists(), f"Broken link: {path}: {link}"
        if parsed.fragment and target in pages:
            assert unquote(parsed.fragment) in pages[target].ids, f"Broken anchor: {path}: {link}"
        link_count += 1

manifest = json.loads((ROOT / "manifest.json").read_text())
for source, metadata in manifest["sources"].items():
    raw = (ROOT.parent / source).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == metadata["sha256"], f"Source changed; review chapter: {source}"

for path in list((ROOT / "diagrams").glob("*.svg")) + list((ROOT / "assets").glob("*.svg")):
    svg = path.read_text()
    element = ET.fromstring(svg)
    assert element.tag.endswith("svg")
    assert "<text" in svg, f"Diagram is empty: {path}"
    assert "<script" not in svg and "<foreignObject" not in svg
    assert "@import" not in svg, f"Remote font import: {path}"
    assert not re.search(r"url\(\s*['\"]?(?:https?:)?//", svg), f"External SVG resource: {path}"

assert {path.stem for path in (ROOT / "diagrams").glob("*.mmd")} == set(DIAGRAMS)
assert {path.stem for path in (ROOT / "diagrams").glob("*.svg")} == set(DIAGRAMS)
assert {path.name for path in (ROOT / "assets").glob("*.svg")} == {"favicon.svg"}

for chapter in CHAPTERS:
    assert len(chapter["sections"]) >= 4
    assert len(chapter["evidence"]) >= 3
    assert chapter["slug"] in CHAPTER_GUIDES
    page = (ROOT / f'{chapter["slug"]}.html').read_text()
    assert "<noscript>" in page and "查看本地源码快照与行号" in page and "本章先抓什么" in page
    assert "data-progress" not in page and "data-demo" not in page

print(f"PASS: {len(pages)} HTML pages, {link_count} local links/anchors, {len(DIAGRAMS)} Mermaid diagrams, {len(manifest['sources'])} source hashes; no progress tracker or custom SVG charts.")
