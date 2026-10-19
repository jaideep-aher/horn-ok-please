import { asset } from "@/lib/asset";

type Stratum = { k: number; n: number; rate: number | null };

export type DevBlock = {
  model: string;
  prompt_id: string;
  n_stop: number;
  n_go: number;
  stop_correct: number;
  go_correct: number;
  unparsed: number;
  recall_stop: number;
  recall_go: number;
  balanced_accuracy: number;
  passed: boolean;
  eligible: boolean;
  go_empty: Stratum;
  go_shoulder: Stratum;
  stop_stratum: Stratum;
};

export type DevSummary = {
  split?: string;
  dated?: string;
  n_predictions?: number;
  blocks?: DevBlock[];
  promoted_prompt?: string | null;
  round4?: boolean;
  reading?: string;
};

const NAMES: Record<string, string> = {
  "qwen25vl-3b-q8": "Qwen2.5-VL 3B Q8",
  "gemma3-4b-q8": "Gemma 3 4B Q8",
};

const PROMPTS: Record<string, string> = {
  D0: "Locked wording. Control. Not eligible.",
  D1: "Neutral. No safety priming.",
  D2: "Ego vehicle, through the windshield.",
  D3: "GO when the lane is clear. Shoulder is not the lane.",
  D4: "Locked wording, GO named before STOP.",
};

function pct(rate: number | null | undefined): string {
  if (rate === null || rate === undefined || Number.isNaN(rate)) return "—";
  return `${(rate * 100).toFixed(1)}%`;
}

function nameOf(id: string): string {
  return NAMES[id] ?? id;
}

export function DevReport({ summary }: { summary: DevSummary }) {
  const blocks = summary.blocks ?? [];
  const promoted = summary.promoted_prompt;
  return (
    <section id="diagnostic" className="mx-auto max-w-6xl px-4 py-14">
      <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Dev split</p>
      <h2 className="mt-2 font-display text-4xl">Was it the prompt, or the picture?</h2>
      <p className="mt-4 max-w-3xl text-lg leading-relaxed">
        Round 3 answered STOP on almost every empty lane. That can be the wording, or a truck drawn on the
        shoulder that the prompt treats as an obstacle. This diagnostic uses sixteen new drawings. It does
        not rescore the locked test set. The same gate applies: balanced accuracy at least 75%, recall at
        least 60% on both classes, unparsed at most 10%.
      </p>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <figure className="overflow-hidden rounded-lg border border-line bg-white">
          <img src={asset("/dev/empty.png")} alt="Drawing of an empty lane. No vehicle and no person." className="w-full" />
          <figcaption className="px-4 py-3 text-sm text-muted">
            Dev GO, empty stratum. Nothing is drawn in the lane or on the shoulder.
          </figcaption>
        </figure>
        <figure className="overflow-hidden rounded-lg border border-line bg-white">
          <img
            src={asset("/dev/shoulder.png")}
            alt="Drawing of an empty lane with a truck parked on the right shoulder."
            className="w-full"
          />
          <figcaption className="px-4 py-3 text-sm text-muted">
            Dev GO, shoulder stratum. The lane is empty. A truck is parked off the lane, the same kind of
            picture as the locked GO drawings.
          </figcaption>
        </figure>
      </div>
      {promoted ? (
        <p className="mt-4 max-w-3xl leading-relaxed">
          {promoted} cleared the gate for at least one model and had the higher mean balanced accuracy. It
          was pre-registered as round 4 before any new completion on the locked scenes.
        </p>
      ) : (
        <p className="mt-4 max-w-3xl leading-relaxed">
          No candidate cleared that gate. Round 4 was not opened. The locked forty scenes were not run again.
        </p>
      )}
      <div className="mt-8 overflow-x-auto rounded-lg border border-line bg-white">
        <table className="w-full min-w-[52rem] text-left text-sm">
          <caption className="px-4 py-3 text-left font-display text-2xl">
            Sixteen new scenes, five wordings
          </caption>
          <thead className="text-xs tracking-wide text-muted uppercase">
            <tr>
              <th className="px-4 py-2 font-medium">Wording</th>
              <th className="px-4 py-2 font-medium">Model</th>
              <th className="px-4 py-2 font-medium">STOP</th>
              <th className="px-4 py-2 font-medium">GO</th>
              <th className="px-4 py-2 font-medium">Balanced</th>
              <th className="px-4 py-2 font-medium">Empty lane</th>
              <th className="px-4 py-2 font-medium">Shoulder truck</th>
              <th className="px-4 py-2 font-medium">Gate</th>
            </tr>
          </thead>
          <tbody>
            {blocks.map((row) => (
              <tr key={`${row.prompt_id}-${row.model}`} className="border-t border-line">
                <td className="px-4 py-2">
                  <span className="font-medium">{row.prompt_id}</span>
                  <span className="mt-0.5 block text-xs text-muted">{PROMPTS[row.prompt_id] ?? row.prompt_id}</span>
                </td>
                <td className="px-4 py-2">{nameOf(row.model)}</td>
                <td className="num px-4 py-2">
                  {row.stop_correct}/{row.n_stop}
                </td>
                <td className="num px-4 py-2">
                  {row.go_correct}/{row.n_go}
                </td>
                <td className="num px-4 py-2">{pct(row.balanced_accuracy)}</td>
                <td className="num px-4 py-2">
                  {row.go_empty.k}/{row.go_empty.n}
                </td>
                <td className="num px-4 py-2">
                  {row.go_shoulder.k}/{row.go_shoulder.n}
                </td>
                <td className="px-4 py-2">
                  {row.prompt_id === "D0" ? "control" : row.passed ? "eligible" : "not eligible"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="px-4 py-3 text-sm text-muted">
          Empty lane and shoulder truck are GO answers inside those strata. STOP is correct answers on the
          eight hazard scenes. {summary.n_predictions ?? blocks.length} stored diagnostic rows. Unparsed
          answers count as misses.
        </p>
        {summary.reading ? (
          <p className="px-4 py-3 text-sm leading-relaxed">{summary.reading}</p>
        ) : null}
      </div>
    </section>
  );
}
