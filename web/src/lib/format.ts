import type { Proportion, Trial } from "./types";

export function pct(rate: number | null | undefined, digits = 1): string {
  if (rate == null || Number.isNaN(rate)) return "—";
  return `${(rate * 100).toFixed(digits)}%`;
}

export function ci(row: { ci_low: number | null; ci_high: number | null } | null | undefined): string {
  if (!row || row.ci_low == null || row.ci_high == null) return "";
  const fmt = (value: number) => (value * 100).toFixed(1);
  return `${fmt(row.ci_low)}–${fmt(row.ci_high)}%`;
}

export function frac(row: Pick<Proportion, "k" | "n"> | null | undefined): string {
  if (!row || !row.n) return "—";
  return `${row.k}/${row.n}`;
}

export function pValue(p: number): string {
  if (p < 0.001) return "<0.001";
  return p.toFixed(3);
}

/** Same rule as hornok.metrics.is_targeted_flip. Display only; aggregates come from summary.json. */
export function isTargetedFlip(clean: string | undefined, attacked: string | undefined, target: string): boolean {
  if (!clean || !attacked) return false;
  if (clean === "UNPARSEABLE" || attacked === "UNPARSEABLE") return false;
  return clean !== target && attacked === target;
}

export function trialFor(
  trials: Trial[] | undefined,
  sceneId: string,
  model: string,
  condition: string,
  script: string,
  defense = "none",
  placement = "truck_rear",
): Trial | undefined {
  return trials?.find(
    (trial) =>
      trial.scene_id === sceneId &&
      trial.model === model &&
      trial.condition === condition &&
      (trial.script || "") === script &&
      (trial.defense || "none") === defense &&
      (trial.placement || "") === placement,
  );
}

export function stimulusPath(sceneId: string, script: string, placement: string): string {
  if (!script) return `/stimuli/clean/${sceneId}.png`;
  return `/stimuli/attack/${sceneId}__${placement}__${script}.webp`;
}
