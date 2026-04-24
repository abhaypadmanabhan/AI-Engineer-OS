import { createHighlighter, type Highlighter } from "shiki";

let highlighterPromise: Promise<Highlighter> | null = null;

export function getHighlighter() {
  if (!highlighterPromise) {
    highlighterPromise = createHighlighter({
      themes: ["github-dark-dimmed", "github-light"],
      langs: [
        "python",
        "typescript",
        "javascript",
        "tsx",
        "jsx",
        "bash",
        "shell",
        "json",
        "yaml",
        "sql",
        "markdown",
        "toml",
      ],
    });
  }
  return highlighterPromise;
}

export async function highlight(code: string, lang: string) {
  const hl = await getHighlighter();
  const safeLang = hl.getLoadedLanguages().includes(lang as never) ? lang : "text";
  return hl.codeToHtml(code, {
    lang: safeLang,
    themes: { dark: "github-dark-dimmed", light: "github-light" },
    defaultColor: "dark",
  });
}
