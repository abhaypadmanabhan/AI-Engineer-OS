"use client";
import { useState } from "react";
import { Check, Copy, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { colabUrl } from "@/lib/colab";

type Props = {
  html: string;
  raw: string;
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
            <Button asChild variant="ghost" size="sm" className="h-7 px-2 text-xs">
              <a
                href={colabUrl(colabPath)}
                target="_blank"
                rel="noreferrer"
                title="Open in Google Colab"
              >
                <ExternalLink className="h-3 w-3" />
                <span>Colab</span>
              </a>
            </Button>
          )}
          <Button
            onClick={copy}
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            aria-label="Copy code"
          >
            {copied ? <Check className="h-3 w-3 text-accent" /> : <Copy className="h-3 w-3" />}
            <span>{copied ? "copied" : "copy"}</span>
          </Button>
        </div>
      </div>
      <ScrollArea className="max-w-full">
        <div
          className="px-4 py-3 text-sm"
          dangerouslySetInnerHTML={{ __html: html }}
        />
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
}
