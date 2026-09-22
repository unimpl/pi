(() => {
  "use strict";
  document.documentElement.classList.add("js");
  const menu = document.querySelector(".menu-toggle");
  menu?.addEventListener("click", () => {
    const open = menu.getAttribute("aria-expanded") !== "true";
    menu.setAttribute("aria-expanded", String(open));
    document.querySelector(".sidebar").classList.toggle("open", open);
  });

  const form = document.querySelector(".search-form");
  if (form) {
    const input = document.querySelector("#query");
    const results = document.querySelector("#search-results");
    const status = document.querySelector("#search-status");
    const search = () => {
      const query = input.value.trim();
      results.replaceChildren();
      if (!query) { status.textContent = "输入关键词，查找相关段落。"; return; }
      const terms = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
      const matches = (window.STUDY_SEARCH || []).filter((item) => terms.every((term) => `${item.title} ${item.text}`.toLocaleLowerCase().includes(term)));
      status.textContent = matches.length ? `找到 ${matches.length} 个相关段落。` : "没有匹配内容。试试更短的关键词，如“工具”或“取消”。";
      for (const item of matches) {
        const article = document.createElement("article"); article.className = "search-result";
        const title = document.createElement("h2"); const link = document.createElement("a"); link.href = item.url; link.textContent = item.title; title.append(link);
        const p = document.createElement("p");
        const start = Math.max(0, item.text.toLocaleLowerCase().indexOf(terms[0]) - 55);
        const excerpt = (start ? "…" : "") + item.text.slice(start, start + 210) + (start + 210 < item.text.length ? "…" : "");
        // Build text nodes, never interpret the query or excerpts as HTML.
        const escaped = terms.map((term) => term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
        const pattern = new RegExp(`(${escaped.join("|")})`, "giu");
        let cursor = 0;
        for (const match of excerpt.matchAll(pattern)) {
          p.append(document.createTextNode(excerpt.slice(cursor, match.index)));
          const mark = document.createElement("mark"); mark.textContent = match[0]; p.append(mark); cursor = match.index + match[0].length;
        }
        p.append(document.createTextNode(excerpt.slice(cursor)));
        article.append(title, p); results.append(article);
      }
    };
    form.addEventListener("submit", (event) => { event.preventDefault(); search(); });
    input.addEventListener("input", search);
  }
})();
