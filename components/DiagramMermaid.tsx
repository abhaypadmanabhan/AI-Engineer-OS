"use client";
import { useEffect, useRef, useState } from "react";

let idCounter = 0;

export function DiagramMermaid({ children }: { children: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const mermaid = (await import("mermaid")).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        fontFamily: "var(--font-plex)",
        themeVariables: {
          primaryColor: "#27272a",
          primaryTextColor: "#f4f4f5",
          primaryBorderColor: "#fb923c",
          lineColor: "#a1a1aa",
        },
      });
      const id = `mmd-${++idCounter}`;
      try {
        const { svg } = await mermaid.render(id, children.trim());
        if (!cancelled) setSvg(svg);
      } catch (e) {
        if (!cancelled) setSvg(`<pre class="text-red-400">${String(e)}</pre>`);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [children]);

  return (
    <div
      ref={ref}
      className="my-6 overflow-x-auto rounded-lg border border-border bg-card p-4"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
