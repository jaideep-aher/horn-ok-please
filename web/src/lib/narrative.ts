import { ci, frac, pValue, pct } from "./format";
import { modelShort } from "./types";
import type { AsrRow, Summary, TestRow } from "./types";

export function asrRow(
  summary: Summary | null | undefined,
  model: string,
  script: string,
  defense = "none",
): AsrRow | undefined {
  return summary?.asr?.find(
    (row) =>
      row.model === model &&
      row.script === script &&
      row.defense === defense &&
      row.subset === "primary",
  );
}

export function rateLine(row: AsrRow | undefined): string {
  if (!row || row.n === 0 || row.rate == null) return "No paired scenes in the file.";
  const interval = ci(row);
  return `${frac(row)} targeted flips (${pct(row.rate)}${interval ? `, Wilson 95% CI ${interval}` : ""}).`;
}

export function testSentence(test: TestRow): string {
  const arms: Record<string, string> = {
    T1_en_vs_deva:
      "The first arm is English and the second is Devanagari. “First only” is a targeted flip on English and not on Devanagari.",
    T2_en_vs_hinglish:
      "The first arm is English and the second is Hinglish. “First only” is a targeted flip on English and not on Hinglish.",
    T3_deva_vs_hinglish:
      "The first arm is Devanagari and the second is Hinglish.",
    T4_f16_vs_q4_asr:
      "The first arm is f16 and the second is Q4_0. Pairs are scene × script.",
    T5_prompt_defense:
      "The first arm is no defense and the second is prompt hardening.",
    T6_ocr_defense: "The first arm is no defense and the second is OCR isolation.",
    T7_f16_vs_q4_benign:
      "The first arm is f16 and the second is Q4_0. The outcome is agreement with the constructed label on a clean image.",
  };
  const note = arms[test.id] ?? test.description;
  const holm = test.p_holm < 0.05 ? "below 0.05 after Holm" : "not below 0.05 after Holm";
  return `${note} ${test.b_only} pairs favor the first arm only, ${test.c_only} favor the second only, ${test.n} pairs, ${test.n_discordant} discordant. Exact McNemar p ${pValue(test.p)}, Holm p ${pValue(test.p_holm)} (${holm}).`;
}

export function primaryAsrSentences(summary: Summary): string[] {
  const model = summary.primary_model;
  if (!model) return [];
  return ["en", "deva", "hinglish"].map((script) => {
    const row = asrRow(summary, model, script, "none");
    const name = script === "en" ? "English" : script === "deva" ? "Marathi in Devanagari" : "Hinglish";
    return `${name} on ${modelShort(model)}, tailgate, no defense: ${rateLine(row)}`;
  });
}
