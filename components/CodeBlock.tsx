"use client";
import { useState } from "react";
import { Check, Copy, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { colabUrl } from "@/lib/colab";

type Props = {
  html: string;        // pre-highlighted HTML from shiki
  raw: string;         // source text for copy
  lang: string;
  colabPath?: string;
  filename?: string;
};

export function CodeBlock({ html, raw, lang, colabPath, filename }: Props) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(raw);
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  return (
    <div className="group relative my-5 overflow-hidden rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border/60 px-3 py-1.5 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wide">
            {lang}
          </span>
          {filename && <span className="font-mono">{filename}</span>}
        </div>
        <div className="flex items-center gap-1">
          {colabPath && (
            <a
              href={colabUrl(colabPath)}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 rounded px-2 py-1 hover:bg-muted"
              title="Open in Google Colab"
            >
              <ExternalLink className="h-3 w-3" />
              <span>Colab</span>
            </a>
          )}
          <button
            onClick={copy}
            className={cn(
              "flex items-center gap-1 rounded px-2 py-1 hover:bg-muted",
              copied && "text-accent"
            )}
            aria-label="Copy code"
          >
            {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            <span>{copied ? "copied" : "copy"}</span>
          </button>
        </div>
      </div>
      <div
        className="overflow-x-auto px-4 py-3 text-sm"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}
