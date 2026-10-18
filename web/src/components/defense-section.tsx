import { RateBar } from "@/components/rate-bar";
import { ci, frac, pct } from "@/lib/format";
import { asrRow } from "@/lib/narrative";
import { modelShort, type Summary } from "@/lib/types";

const SCRIPTS = [
  ["en", "English"],
  ["deva", "Marathi"],
  ["hinglish", "Hinglish"],
] as const;

export function DefenseSection({
  summary,
  status,
}: {
  summary: Summary | null;
  status: "loading" | "pending" | "ready" | "error";
}) {
  const primary = summary?.primary_model ?? "smolvlm-256m-f16";
  const edge = summary?.edge_model ?? "smolvlm-256m-q4";
  const regs = (summary?.regulatory ?? []).filter(
    (row) => row.model === primary || row.model === edge,
  );
  return (
    <section id="defense" className="border-t border-line bg-white/50">
      <div className="mx-auto max-w-6xl px-4 py-14">
        <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Defense</p>
        <h2 className="mt-2 font-display text-4xl">Ignore the paint. Still read the sign.</h2>
        <div className="mt-4 grid gap-6 md:grid-cols-2">
          <article className="rounded-lg border border-line bg-paper p-5">
            <h3 className="font-display text-2xl">Prompt hardening</h3>
            <p className="mt-2 text-sm leading-relaxed">
              The picture stays the same. The prompt adds a rule: paint on trucks, roads, walls, and
              billboards is untrusted, in any script. A standard STOP sign, the word रुको, and a red lamp
              may still be obeyed.
            </p>
          </article>
          <article className="rounded-lg border border-line bg-paper p-5">
            <h3 className="font-display text-2xl">OCR, then hide the order</h3>
            <p className="mt-2 text-sm leading-relaxed">
              Tesseract (English, Hindi, and Marathi) lists words. Instruction-like words are painted over.
              The exact tokens STOP and रुको are left in place. The model then sees the masked picture plus
              the hardening rule and the list of removed strings. Full-frame OCR missed the white-on-red
              STOP octagon during development even when the letters were intact. That miss is part of the
              defense being measured.
            </p>
          </article>
        </div>
        <p className="mt-6 max-w-3xl text-sm text-muted">
          The cost that matters is induced over-block: on STOP, रुको, and red-light scenes, how often a
          clean BRAKE becomes something else once the defense is on. English is the attack script used for
          that regulatory slice.
        </p>

        {status !== "ready" || !summary ? (
          <p className="mt-6 rounded-lg border border-dashed border-ink/30 bg-white p-5" role="status">
            Defense rates are pending. They will be read from the same summary file as the attack-success
            charts.
          </p>
        ) : (
          <div className="mt-8 space-y-8">
            <div className="rounded-lg border border-line bg-white p-5">
              <h3 className="font-display text-2xl">{modelShort(primary)} attack success</h3>
              <div className="mt-4 space-y-4">
                {SCRIPTS.map(([id, label]) => (
                  <div key={id}>
                    <p className="mb-2 text-sm">{label}</p>
                    <div className="space-y-2">
                      <RateBar label="No defense" row={asrRow(summary, primary, id, "none")} />
                      <RateBar label="Prompt" row={asrRow(summary, primary, id, "prompt")} />
                      <RateBar label="OCR" row={asrRow(summary, primary, id, "ocr")} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto rounded-lg border border-line bg-white">
              <table className="w-full min-w-[36rem] text-left text-sm">
                <caption className="px-4 py-3 text-left font-display text-2xl">
                  BRAKE on STOP, रुको, and the red lamp
                </caption>
                <thead className="text-xs tracking-wide text-muted uppercase">
                  <tr>
                    <th className="px-4 py-2 font-medium">Model</th>
                    <th className="px-4 py-2 font-medium">Defense</th>
                    <th className="px-4 py-2 font-medium">Condition</th>
                    <th className="px-4 py-2 font-medium">BRAKE</th>
                    <th className="px-4 py-2 font-medium">Induced over-block</th>
                  </tr>
                </thead>
                <tbody>
                  {regs.map((row) => (
                    <tr
                      key={`${row.model}-${row.defense}-${row.condition}`}
                      className="border-t border-line"
                    >
                      <td className="px-4 py-2">{modelShort(row.model)}</td>
                      <td className="px-4 py-2">{row.defense}</td>
                      <td className="px-4 py-2">{row.condition === "attack" ? "English paint" : "clean"}</td>
                      <td className="num px-4 py-2">
                        {frac(row.brake_rate)} · {pct(row.brake_rate.rate)}
                        <span className="block text-xs text-muted">{ci(row.brake_rate)}</span>
                      </td>
                      <td className="num px-4 py-2">
                        {row.induced_overblock
                          ? `${frac(row.induced_overblock)} · ${pct(row.induced_overblock.rate)}`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
