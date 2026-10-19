import { Picture } from "@/components/picture";
import { LITERACY_CARDS, SCRIPT_LABEL } from "@/lib/phrases";
import { modelShort, type Summary } from "@/lib/types";

export function LiteracySection({
  summary,
  status,
}: {
  summary: Summary | null;
  status: "loading" | "pending" | "ready" | "error";
}) {
  return (
    <section id="literacy" className="mx-auto max-w-6xl px-4 py-14">
      <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Reading</p>
      <h2 className="mt-2 font-display text-4xl">Script literacy, measured on cards</h2>
      <p className="mt-3 max-w-3xl text-muted">
        Eight cards, not driving scenes. The score is character similarity after Unicode normalization,
        collapsed spaces, and case folding: one minus the character error rate. Exact copies are counted
        too. With fewer than five models, the pre-registration does not run a correlation between reading
        and attack success. The idea that partial literacy is the dangerous case stays open.
      </p>
      <ul className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {LITERACY_CARDS.map((card) => (
          <li key={card.id} className="rounded-lg border border-line bg-white p-4">
            <Picture
              src={`/stimuli/literacy/${card.id}.png`}
              alt={`Card reading ${card.text}`}
              className="h-auto w-full rounded bg-paper"
            />
            <p className={`mt-2 text-sm ${card.script === "deva" ? "font-deva" : ""}`}>{card.text}</p>
            <p className="text-xs text-muted">{SCRIPT_LABEL[card.script]}</p>
          </li>
        ))}
      </ul>
      {status !== "ready" || !summary?.literacy?.length ? (
        <p className="mt-6 text-sm text-muted" role="status">
          Transcription scores are pending. Horn OK Please itself is one of the English cards. It is not
          the driving-attack phrase.
        </p>
      ) : (
        <div className="mt-8 overflow-x-auto rounded-lg border border-line bg-white">
          <table className="w-full min-w-[32rem] text-left text-sm">
            <caption className="px-4 py-3 text-left font-display text-2xl">Mean similarity</caption>
            <thead className="text-xs tracking-wide text-muted uppercase">
              <tr>
                <th className="px-4 py-2 font-medium">Model</th>
                <th className="px-4 py-2 font-medium">Script</th>
                <th className="px-4 py-2 font-medium">Cards</th>
                <th className="px-4 py-2 font-medium">Mean similarity</th>
                <th className="px-4 py-2 font-medium">Exact</th>
              </tr>
            </thead>
            <tbody>
              {summary.literacy.map((row) => (
                <tr key={`${row.model}-${row.script}`} className="border-t border-line">
                  <td className="px-4 py-2">{modelShort(row.model)}</td>
                  <td className="px-4 py-2">{SCRIPT_LABEL[row.script] ?? row.script}</td>
                  <td className="num px-4 py-2">{row.n}</td>
                  <td className="num px-4 py-2">{row.mean_similarity.toFixed(3)}</td>
                  <td className="num px-4 py-2">
                    {row.exact_k}/{row.n}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
