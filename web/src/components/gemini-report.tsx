type Rate = {
  k: number;
  n: number;
  rate?: number | null;
  ci95?: [number, number] | null;
};

type Gate = {
  model: string;
  stop_correct: number;
  go_correct: number;
  n_stop: number;
  n_go: number;
  unparsed: number;
  balanced_accuracy: number | null;
  passed: boolean;
  note?: string;
};

export type GeminiSummary = {
  flash: string;
  flash_lite: string;
  lite_why: string;
  gate: Gate[];
  attacks: (Rate & { phrase: string; script: string })[];
  phrase_panel: (Rate & { phrase: string; script: string })[];
  benign: (Rate & { phrase: string; script: string })[];
  defenses: (Rate & { defense: string; script: string })[];
  overblock: (Rate & { defense: string })[];
  literacy_cards: { script: string; mean_similarity: number; exact_k: number; n: number }[];
  explain: string;
  photos: string;
};

const SCRIPT: Record<string, string> = {
  en: "English",
  mr: "Marathi",
  hi: "Hindi",
  hinglish: "Hinglish",
};

function rate(row: Rate): string {
  if (!row.n) return "not defined";
  return `${row.k}/${row.n}`;
}

export function GeminiReport({ summary }: { summary: GeminiSummary }) {
  const rows = [...summary.attacks, ...summary.phrase_panel, ...summary.benign];
  return (
    <section id="gemini" className="mx-auto max-w-6xl px-4 py-14">
      <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Gemini</p>
      <h2 className="mt-2 font-display text-4xl">Flash passed. Flash-Lite did not answer.</h2>
      <p className="mt-4 max-w-3xl leading-relaxed">
        Jay ran the locked STOP versus GO protocol. The client resolved Flash to {summary.flash} and Flash-Lite to{" "}
        {summary.flash_lite}. These rows are not in the open-model table above. The prompt, the 40 scenes, the parser,
        and the gate were not changed after these scores.
      </p>
      <div className="mt-8 overflow-x-auto rounded-lg border border-line bg-white">
        <table className="w-full min-w-[40rem] text-left text-sm">
          <caption className="px-4 py-3 text-left font-display text-2xl">Gate</caption>
          <thead className="text-xs tracking-wide text-muted uppercase">
            <tr>
              <th className="px-4 py-2 font-medium">Model</th>
              <th className="px-4 py-2 font-medium">STOP</th>
              <th className="px-4 py-2 font-medium">GO</th>
              <th className="px-4 py-2 font-medium">Balanced</th>
              <th className="px-4 py-2 font-medium">Unparsed</th>
              <th className="px-4 py-2 font-medium">Gate</th>
            </tr>
          </thead>
          <tbody>
            {summary.gate.map((row) => (
              <tr key={row.model} className="border-t border-line">
                <td className="px-4 py-2">{row.model}</td>
                <td className="num px-4 py-2">
                  {row.stop_correct}/{row.n_stop}
                </td>
                <td className="num px-4 py-2">
                  {row.go_correct}/{row.n_go}
                </td>
                <td className="num px-4 py-2">
                  {row.balanced_accuracy === null ? "—" : row.balanced_accuracy.toFixed(3)}
                </td>
                <td className="num px-4 py-2">
                  {row.unparsed}/{row.n_stop + row.n_go}
                </td>
                <td className="px-4 py-2">{row.passed ? "passed" : "gated out"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted">{summary.lite_why}</p>

      <div className="mt-8 overflow-x-auto rounded-lg border border-line bg-white">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <caption className="px-4 py-3 text-left font-display text-2xl">
            STOP to GO on {summary.flash}
          </caption>
          <thead className="text-xs tracking-wide text-muted uppercase">
            <tr>
              <th className="px-4 py-2 font-medium">Phrase</th>
              <th className="px-4 py-2 font-medium">Script</th>
              <th className="px-4 py-2 font-medium">Flips</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={`${row.phrase}-${row.script}`} className="border-t border-line">
                <td className="px-4 py-2">{row.phrase === "B1" ? "Benign" : row.phrase}</td>
                <td className="px-4 py-2">{SCRIPT[row.script] ?? row.script}</td>
                <td className="num px-4 py-2">{rate(row)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-8 overflow-x-auto rounded-lg border border-line bg-white">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <caption className="px-4 py-3 text-left font-display text-2xl">Defenses</caption>
          <thead className="text-xs tracking-wide text-muted uppercase">
            <tr>
              <th className="px-4 py-2 font-medium">Defense</th>
              <th className="px-4 py-2 font-medium">What</th>
              <th className="px-4 py-2 font-medium">Count</th>
            </tr>
          </thead>
          <tbody>
            {summary.defenses.map((row) => (
              <tr key={`${row.defense}-${row.script}`} className="border-t border-line">
                <td className="px-4 py-2">{row.defense}</td>
                <td className="px-4 py-2">G1 STOP to GO, {SCRIPT[row.script] ?? row.script}</td>
                <td className="num px-4 py-2">{rate(row)}</td>
              </tr>
            ))}
            {summary.overblock.map((row) => (
              <tr key={`${row.defense}-over`} className="border-t border-line">
                <td className="px-4 py-2">{row.defense}</td>
                <td className="px-4 py-2">Over-block on a true GO that was GO without the defense</td>
                <td className="num px-4 py-2">{rate(row)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 max-w-3xl text-sm leading-relaxed">
        Literacy cards, same model: English mean {summary.literacy_cards[0]?.mean_similarity.toFixed(3)}, exact{" "}
        {summary.literacy_cards[0]?.exact_k}/{summary.literacy_cards[0]?.n}. Devanagari mean{" "}
        {summary.literacy_cards[1]?.mean_similarity.toFixed(3)}, exact {summary.literacy_cards[1]?.exact_k}/
        {summary.literacy_cards[1]?.n}. The Devanagari stratum marks it a reader.
      </p>
      <h3 className="mt-10 font-display text-2xl">Explanation scenes</h3>
      <p className="mt-3 max-w-3xl text-sm leading-relaxed">{summary.explain}</p>
      <h3 className="mt-8 font-display text-2xl">Real photographs</h3>
      <p className="mt-3 max-w-3xl text-sm leading-relaxed">{summary.photos}</p>
    </section>
  );
}
