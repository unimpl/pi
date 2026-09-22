import { renderMermaidSVG } from "beautiful-mermaid";
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Optional build-time dependency; generated pages never load this package.
const base = dirname(fileURLToPath(import.meta.url));
for (const file of readdirSync(join(base, "diagrams")).filter((name) => name.endsWith(".mmd"))) {
  const source = readFileSync(join(base, "diagrams", file), "utf8");
  const svg = renderMermaidSVG(source, {
    bg: "#f0f1e9", fg: "#24392e", accent: "#285e4c", muted: "#59645e",
    line: "#758570", surface: "#e6eadd", border: "#9ead97",
    font: "PingFang SC", padding: 24,
  // The renderer adds a Google Fonts import even for installed system fonts.
  // Remove it so standalone SVG views are offline too, not only <img> embeds.
  }).replace(/^\s*@import[^\n]*\n/gm, "");
  writeFileSync(join(base, "diagrams", file.replace(/\.mmd$/, ".svg")), svg);
  console.log(`Rendered ${file}`);
}
