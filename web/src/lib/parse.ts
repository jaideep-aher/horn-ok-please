/** Port of hornok.parse for the optional live call. Scored actions come from summary.json. */

const ALIASES: { action: string; pattern: RegExp }[] = [
  { action: "CHANGE_LANE", pattern: /change[\s_]*lane|lane[\s_]*change/gi },
  { action: "BRAKE", pattern: /\b(?:brake|halt|stop)\b/gi },
  { action: "SLOW", pattern: /\bslow(?:\s+down)?\b|\bdecelerate\b/gi },
  { action: "CONTINUE", pattern: /\bcontinue\b|\bproceed\b|\bkeep going\b/gi },
];

const NEGATION = /(?:do\s+not|don't|dont|never|not)\s*$/i;

function negated(text: string, start: number): boolean {
  return NEGATION.test(text.slice(Math.max(0, start - 12), start));
}

function phraseToAction(phrase: string): string | null {
  const found: string[] = [];
  for (const { action, pattern } of ALIASES) {
    pattern.lastIndex = 0;
    let match = pattern.exec(phrase);
    while (match) {
      if (!negated(phrase, match.index) && !found.includes(action)) {
        found.push(action);
      }
      match = pattern.exec(phrase);
    }
  }
  return found.length === 1 ? found[0] : null;
}

export function parseDecision(text: string): { action: string; rationale: string } {
  const raw = (text || "").trim();
  if (!raw) return { action: "UNPARSEABLE", rationale: "" };

  const jsonMatch = raw.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    try {
      const payload = JSON.parse(jsonMatch[0]) as { action?: unknown; rationale?: unknown; because?: unknown };
      if (payload && typeof payload === "object" && "action" in payload) {
        const action = phraseToAction(String(payload.action ?? ""));
        if (action) {
          const rationale = String(payload.rationale || payload.because || "").trim();
          return { action, rationale };
        }
      }
    } catch {
      /* fall through */
    }
  }

  const actionLine = raw.match(/ACTION\s*:\s*(.+)/i);
  const because = raw.match(/BECAUSE\s*:\s*([\s\S]+)/i);
  const rationale = because ? because[1].trim() : "";
  if (actionLine) {
    const action = phraseToAction(actionLine[1].split(/\n/)[0]);
    if (action) return { action, rationale };
  }
  const fallback = phraseToAction(raw);
  if (fallback) return { action: fallback, rationale };
  return { action: "UNPARSEABLE", rationale };
}
