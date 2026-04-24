"use client";
import { useEffect, useRef, useState } from "react";
import { Key, Loader2, Play, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PRICING, computeCost, type ModelId } from "@/lib/pricing";

const KEY_STORAGE = "playground:anthropic_key";
const MODELS: { id: ModelId; label: string }[] = [
  { id: "claude-sonnet-4-6", label: "Sonnet 4.6 (default)" },
  { id: "claude-haiku-4-5", label: "Haiku 4.5 (fast)" },
];

export default function PlaygroundPage() {
  const [apiKey, setApiKey] = useState<string>("");
  const [keyDraft, setKeyDraft] = useState<string>("");
  const [keyOpen, setKeyOpen] = useState(false);
  const [prompt, setPrompt] = useState<string>("Explain prompt caching in one paragraph.");
  const [system, setSystem] = useState<string>("");
  const [model, setModel] = useState<ModelId>("claude-sonnet-4-6");
  const [temperature, setTemperature] = useState<number>(0);
  const [maxTokens, setMaxTokens] = useState<number>(1024);
  const [output, setOutput] = useState<string>("");
  const [running, setRunning] = useState<boolean>(false);
  const [inputTok, setInputTok] = useState<number>(0);
  const [outputTok, setOutputTok] = useState<number>(0);
  const [err, setErr] = useState<string>("");
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const k = localStorage.getItem(KEY_STORAGE) ?? "";
    setApiKey(k);
    if (!k) setKeyOpen(true);
  }, []);

  function saveKey() {
    setApiKey(keyDraft);
    localStorage.setItem(KEY_STORAGE, keyDraft);
    setKeyDraft("");
    setKeyOpen(false);
  }
  function clearKey() {
    setApiKey("");
    localStorage.removeItem(KEY_STORAGE);
  }

  async function run() {
    if (!apiKey) {
      setKeyOpen(true);
      return;
    }
    setErr("");
    setOutput("");
    setInputTok(0);
    setOutputTok(0);
    setRunning(true);
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const body: any = {
        model,
        max_tokens: maxTokens,
        temperature,
        stream: true,
        messages: [{ role: "user", content: prompt }],
      };
      if (system.trim()) body.system = system;

      const resp = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": apiKey,
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });

      if (!resp.ok || !resp.body) {
        const text = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${text.slice(0, 400)}`);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf("\n\n")) !== -1) {
          const event = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          const dataLine = event.split("\n").find((l) => l.startsWith("data: "));
          if (!dataLine) continue;
          const payload = dataLine.slice(6).trim();
          if (!payload || payload === "[DONE]") continue;
          try {
            const evt = JSON.parse(payload);
            if (evt.type === "content_block_delta" && evt.delta?.type === "text_delta") {
              setOutput((prev) => prev + evt.delta.text);
            } else if (evt.type === "message_start" && evt.message?.usage) {
              setInputTok(evt.message.usage.input_tokens ?? 0);
            } else if (evt.type === "message_delta" && evt.usage) {
              setOutputTok(evt.usage.output_tokens ?? 0);
            }
          } catch {
            // ignore malformed SSE
          }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") setErr(e.message ?? String(e));
    } finally {
      setRunning(false);
      abortRef.current = null;
    }
  }

  function stop() {
    abortRef.current?.abort();
  }

  const cost = computeCost(model, inputTok, outputTok);
  const p = PRICING[model];

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-semibold">Playground</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Bring-your-own-key Anthropic streaming. Key stays in your browser — never touches our server.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setKeyOpen(true)}>
            <Key className="h-4 w-4" />
            {apiKey ? "Change key" : "Set key"}
          </Button>
          {apiKey && (
            <Button variant="ghost" size="sm" onClick={clearKey} aria-label="Clear API key">
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-[1fr_280px]">
        <Card>
          <CardHeader>
            <CardTitle>Prompt</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-muted-foreground">
                System (optional)
              </label>
              <Textarea
                value={system}
                onChange={(e) => setSystem(e.target.value)}
                rows={2}
                placeholder="You are a helpful assistant..."
              />
            </div>
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-muted-foreground">
                User
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                rows={6}
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={running ? stop : run} disabled={!prompt.trim()}>
                {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                {running ? "Stop" : "Run"}
              </Button>
              <Button variant="outline" onClick={() => { setOutput(""); setErr(""); setInputTok(0); setOutputTok(0); }}>
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1 block text-xs uppercase tracking-wide text-muted-foreground">Model</label>
              <Select value={model} onValueChange={(v) => setModel(v as ModelId)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MODELS.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="mt-1 font-mono text-[10px] text-muted-foreground">
                ${p.input_per_mtok}/M in · ${p.output_per_mtok}/M out
              </div>
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="text-xs uppercase tracking-wide text-muted-foreground">Temperature</label>
                <span className="font-mono text-xs">{temperature.toFixed(2)}</span>
              </div>
              <Slider
                value={[temperature]}
                onValueChange={(v) => setTemperature(v[0])}
                min={0}
                max={1}
                step={0.05}
              />
            </div>
            <div>
              <div className="mb-2 flex items-center justify-between">
                <label className="text-xs uppercase tracking-wide text-muted-foreground">Max tokens</label>
                <span className="font-mono text-xs">{maxTokens}</span>
              </div>
              <Input
                type="number"
                min={1}
                max={8192}
                value={maxTokens}
                onChange={(e) => setMaxTokens(Math.max(1, parseInt(e.target.value || "1")))}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-base">Output</CardTitle>
          <div className="font-mono text-xs text-muted-foreground">
            {inputTok} in · {outputTok} out · ${cost.toFixed(5)}
          </div>
        </CardHeader>
        <CardContent>
          {err && (
            <div className="mb-3 rounded border border-destructive/50 bg-destructive/10 p-3 font-mono text-xs text-destructive">
              {err}
            </div>
          )}
          <pre className="min-h-[200px] whitespace-pre-wrap rounded-md border border-border bg-input/40 p-4 font-mono text-sm">
            {output || (running ? "streaming..." : "output will stream here")}
          </pre>
        </CardContent>
      </Card>

      <Dialog open={keyOpen} onOpenChange={setKeyOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Anthropic API key</DialogTitle>
            <DialogDescription>
              Pasted in and stored in your browser&apos;s localStorage. Never sent to our server. Get one at{" "}
              <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noreferrer" className="underline">
                console.anthropic.com
              </a>
              .
            </DialogDescription>
          </DialogHeader>
          <Input
            type="password"
            placeholder="sk-ant-..."
            value={keyDraft}
            onChange={(e) => setKeyDraft(e.target.value)}
            className="font-mono"
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setKeyOpen(false)}>Cancel</Button>
            <Button onClick={saveKey} disabled={!keyDraft.startsWith("sk-")}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
