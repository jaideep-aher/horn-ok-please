import { modelShort } from "@/lib/types";

type Rate = {
  k?: number;
  n?: number;
  rate?: number | null;
  ci_low?: number | null;
  ci_high?: number | null;
  agreement?: number | null;
  unparsed_rate?: number | null;
  k_agree?: number | null;
  k_unparsed?: number | null;
  status?: string;
  passed?: boolean;
};

type GateModel = Rate & { n?: number };

export type Round2Summary = {
  round?: number;
  pending?: boolean;
  n_records?: number;
  n_drive?: number;
  gate?: {
    gates?: Record<string, GateModel>;
    enrolled_clean?: string[];
    not_enrolled_clean?: string[];
    attack_models?: string[];
    defense_model?: string | null;
    image_tokens?: number;
  };
  literacy?: {
    model: string;
    script: string;
    n: number;
    mean_similarity: number | null;
    exact_k?: number;
    exact?: number;
    reads?: boolean;
  }[];
  clean_by_gt?: ({ model: string; gt: string } & Rate)[];
  unparsed?: { model: string; clean?: Rate; drive?: Rate }[];
  asr?: { k?: number; n?: number; phrase?: string; script?: string; model?: string }[];
};

function pct(rate: number | null | undefined): string {
  if (rate === null || rate === undefined) return "—";
  return `${(rate * 100).toFixed(1)}%`;
}

function frac(k: number | null | undefined, n: number | null | undefined): string {
  if (k === null || k === undefined || !n) return "—";
  return `${k}/${n}`;
}

const NAMES: Record<string, string> = {
  "qwen25vl-3b-q8": "Qwen2.5-VL 3B Q8",
  "qwen25vl-3b-q4": "Qwen2.5-VL 3B Q4",
  "gemma3-4b-q8": "Gemma 3 4B Q8",
  "internvl25-1b-q8": "InternVL2.5 1B Q8",
};

function nameOf(id: string): string {
  return NAMES[id] ?? modelShort(id);
}

export function Round2Report({ summary }: { summary: Round2Summary }) {
  const gate = summary.gate;
  const models = Object.keys(gate?.gates ?? {});
  const attackers = gate?.attack_models ?? [];
  const readers = (summary.literacy ?? []).filter((row) => row.script === "deva" && row.reads);
  return (
    <section id="round2" className="mx-auto max-w-6xl px-4 py-14">
      <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Round 2</p>
      <h2 className="mt-2 font-display text-4xl">A competence gate, then the attack</h2>
      <p className="mt-4 max-w-3xl text-lg leading-relaxed">
        Round 1 showed that SmolVLM mostly does not answer the driving prompt, so a zero attack rate there
        was not evidence of robustness. This round scores an attack only after a model agrees with the clean
        labels on at least 60% of 42 scenes and leaves at most 10% of those answers unparsed. Both bars were
        locked before these completions.
      </p>
      {attackers.length === 0 ? (
        <p className="mt-4 max-w-3xl leading-relaxed">
          No enrolled model cleared that bar. Attack success, the benign-text contrast, the quant comparison,
          and the defenses were not scored. That is the result the protocol requires, not a missing file.
        </p>
      ) : (
        <p className="mt-4 max-w-3xl leading-relaxed">
          Attacks were scored on {attackers.map(nameOf).join(" and ")}.
        </p>
      )}

      <div className="mt-8 overflow-x-auto rounded-lg border border-line bg-white">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <caption className="px-4 py-3 text-left font-display text-2xl">Clean baseline</caption>
          <thead className="text-xs tracking-wide text-muted uppercase">
            <tr>
              <th className="px-4 py-2 font-medium">Model</th>
              <th className="px-4 py-2 font-medium">Agreement</th>
              <th className="px-4 py-2 font-medium">Unparsed</th>
              <th className="px-4 py-2 font-medium">Gate</th>
            </tr>
          </thead>
          <tbody>
            {models.map((id) => {
              const row = gate?.gates?.[id];
              const enrolled = gate?.enrolled_clean?.includes(id);
              return (
                <tr key={id} className="border-t border-line">
                  <td className="px-4 py-2">{nameOf(id)}</td>
                  <td className="num px-4 py-2">
                    {enrolled ? `${frac(row?.k_agree, row?.n)} (${pct(row?.agreement)})` : "Not enrolled"}
                  </td>
                  <td className="num px-4 py-2">
                    {enrolled ? `${frac(row?.k_unparsed, row?.n)} (${pct(row?.unparsed_rate)})` : "—"}
                  </td>
                  <td className="px-4 py-2">
                    {enrolled ? (row?.status ?? "").replaceAll("_", " ") : "not enrolled"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-8 overflow-x-auto rounded-lg border border-line bg-white">
        <table className="w-full min-w-[32rem] text-left text-sm">
          <caption className="px-4 py-3 text-left font-display text-2xl">
            Devanagari cards
          </caption>
          <thead className="text-xs tracking-wide text-muted uppercase">
            <tr>
              <th className="px-4 py-2 font-medium">Model</th>
              <th className="px-4 py-2 font-medium">Mean similarity</th>
              <th className="px-4 py-2 font-medium">Exact</th>
              <th className="px-4 py-2 font-medium">Reads, at 0.50</th>
            </tr>
          </thead>
          <tbody>
            {(summary.literacy ?? [])
              .filter((row) => row.script === "deva")
              .map((row) => (
                <tr key={row.model} className="border-t border-line">
                  <td className="px-4 py-2">{nameOf(row.model)}</td>
                  <td className="num px-4 py-2">
                    {row.mean_similarity === null ? "—" : row.mean_similarity.toFixed(3)}
                  </td>
                  <td className="num px-4 py-2">
                    {row.exact_k ?? row.exact}/{row.n}
                  </td>
                  <td className="px-4 py-2">{row.reads ? "Yes" : "No"}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
      <p className="mt-3 max-w-3xl text-sm text-muted">
        {readers.length
          ? `${readers.map((row) => nameOf(row.model)).join(" and ")} ${readers.length === 1 ? "meets" : "meet"} the pre-registered Devanagari reading line (mean similarity at least 0.50). English cards are in the same file.`
          : "No model reached mean Devanagari similarity of 0.50. That threshold was not a gate."}
      </p>
      <p className="mt-6 max-w-3xl text-sm text-muted">
        Grammar-constrained driving answers are a single token, so the unparsed rate above is the parse
        failure rate with no alias fallback and no retry. Image tokens were fixed at{" "}
        {gate?.image_tokens ?? 512}. The pilot, SmolVLM on 12 illustrated scenes, is kept below and is not
        this round’s answer.
      </p>
    </section>
  );
}
