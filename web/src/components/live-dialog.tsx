"use client";

import { useEffect, useState } from "react";

import { ActionChip } from "@/components/action-chip";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { parseDecision } from "@/lib/parse";
import { DEFENSE_PROMPT_V1, DRIVING_PROMPT_V1 } from "@/lib/prompts";

const STORAGE = "hornok-live-v1";

type Saved = { base: string; model: string; key: string };

export function LiveDialog({
  imageUrl,
  canSend = false,
  defense = "none",
  triggerLabel = "Live mode",
}: {
  imageUrl?: string;
  canSend?: boolean;
  defense?: "none" | "prompt" | "ocr";
  triggerLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const [base, setBase] = useState("https://api.openai.com/v1");
  const [model, setModel] = useState("gpt-4o");
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [raw, setRaw] = useState("");
  const [action, setAction] = useState("");

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE) || "") as Partial<Saved>;
      if (saved.base) setBase(saved.base);
      if (saved.model) setModel(saved.model);
      if (saved.key) setKey(saved.key);
    } catch {
      /* first visit */
    }
  }, []);

  function persist(next: Saved) {
    localStorage.setItem(STORAGE, JSON.stringify(next));
  }

  async function ask() {
    if (!imageUrl || !canSend) return;
    setBusy(true);
    setError("");
    setRaw("");
    setAction("");
    persist({ base, model, key });
    try {
      const imageRes = await fetch(imageUrl);
      if (!imageRes.ok) throw new Error(`Could not read the picture (${imageRes.status}).`);
      const blob = await imageRes.blob();
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result));
        reader.onerror = () => reject(new Error("Could not encode the picture."));
        reader.readAsDataURL(blob);
      });
      const prompt = defense === "prompt" ? DEFENSE_PROMPT_V1 : DRIVING_PROMPT_V1;
      const endpoint = `${base.replace(/\/$/, "")}/chat/completions`;
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${key}`,
        },
        body: JSON.stringify({
          model,
          temperature: 0,
          messages: [
            {
              role: "user",
              content: [
                { type: "text", text: prompt },
                { type: "image_url", image_url: { url: dataUrl } },
              ],
            },
          ],
        }),
      });
      const json = (await res.json()) as {
        error?: { message?: string };
        choices?: { message?: { content?: unknown } }[];
      };
      if (!res.ok) throw new Error(json.error?.message || `Request failed (${res.status}).`);
      const content = json.choices?.[0]?.message?.content;
      const text = typeof content === "string" ? content : JSON.stringify(content ?? "");
      setRaw(text);
      setAction(parseDecision(text).action);
    } catch (err) {
      setError(err instanceof Error ? err.message : "The request failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="yellow" size="sm" type="button">
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Optional live call</DialogTitle>
          <DialogDescription>
            The study numbers on this page come from the precomputed file. A live call is extra, stays in
            this browser, and is not added to the attack-success rate.
          </DialogDescription>
        </DialogHeader>
        <div className="mt-4 space-y-3 text-sm">
          <label className="block space-y-1">
            <span>OpenAI-compatible base URL</span>
            <Input value={base} onChange={(event) => setBase(event.target.value)} autoComplete="off" />
          </label>
          <label className="block space-y-1">
            <span>Model name</span>
            <Input value={model} onChange={(event) => setModel(event.target.value)} autoComplete="off" />
          </label>
          <label className="block space-y-1">
            <span>API key, stored only in localStorage</span>
            <Input
              type="password"
              value={key}
              onChange={(event) => setKey(event.target.value)}
              autoComplete="off"
            />
          </label>
          <p className="text-muted">
            The browser calls the endpoint itself. Many providers block that from a web page. Nothing is
            sent to a Horn OK Please server, because this site has no server. OCR defense is not available
            live: masking needs the local toolkit.
          </p>
          {!canSend ? (
            <p>
              Choose a locked phrase at full plate size to send a rendered file. Custom wording and smaller
              plates exist only as a preview in the browser.
            </p>
          ) : null}
          <Button type="button" onClick={ask} disabled={!canSend || !key || busy || defense === "ocr"}>
            {busy ? "Asking…" : "Send this frame"}
          </Button>
          {error ? (
            <p className="rounded-md border border-signal/40 bg-white px-3 py-2 text-signal" role="alert">
              {error}
            </p>
          ) : null}
          {action ? (
            <p className="flex items-center gap-2">
              Parsed action <ActionChip action={action} />
            </p>
          ) : null}
          {raw ? (
            <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-md bg-white p-3 text-xs">
              {raw}
            </pre>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
