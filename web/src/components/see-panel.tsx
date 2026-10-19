"use client";

import { useState } from "react";

type Cell = { r: number; c: number; saliency: number | null; action?: string | null };
type MapRecord = {
  direct: string | null;
  n_flip_cells: number;
  n_scored_cells: number;
  mass_text: number | null;
  mass_hazard: number | null;
  text_on_hazard: boolean;
  centers_in_text?: number | null;
  cells_meeting_text?: number | null;
  centers_in_hazard?: number | null;
  cells: Cell[];
};
type Scene = {
  id: string;
  label: string;
  hazard: string;
  text_on_hazard: boolean;
  clean: string | null;
  paint: string | null;
  inpaint: string | null;
  decisions: Record<string, { clean: string | null; painted: string | null; inpaint: string | null; state: string }>;
  map: MapRecord | null;
};
type Gaze = {
  model: string;
  scene: string;
  prompt_id: string;
  direct: string | null;
  label: string;
  mass_hazard: number | null;
  n_flip_cells: number;
  n_scored_cells: number;
  centers_in_hazard?: number | null;
  cells_meeting_hazard?: number | null;
  image: string | null;
  cells: Cell[];
  hazard: string;
};
export type XaiSummary = {
  split: string;
  question: string;
  algorithm: string | null;
  reading: string;
  n_predictions: number;
  scenes: Scene[];
  gaze: Gaze[];
  whitebox: { status: string; reason: string };
};

const NAMES: Record<string, string> = {
  "qwen25vl-3b-q8": "Qwen2.5-VL 3B Q8",
  "gemma3-4b-q8": "Gemma 3 4B Q8",
};

function massText(value: number | null): string {
  if (value === null || value === undefined) return "not defined";
  return value.toFixed(2);
}

function Heatmap({ cells, opacity }: { cells: Cell[]; opacity: number }) {
  const ordered = [...cells].sort((a, b) => a.r - b.r || a.c - b.c);
  return (
    <div
      className="pointer-events-none absolute inset-0 grid grid-cols-3 grid-rows-3"
      style={{ opacity }}
      aria-hidden
    >
      {ordered.map((cell) => (
        <div
          key={`${cell.r}-${cell.c}`}
          style={{
            background:
              cell.saliency === 1 ? "rgba(196, 40, 28, 0.62)" : cell.saliency === 0 ? "rgba(20, 40, 80, 0.12)" : "transparent",
          }}
        />
      ))}
    </div>
  );
}

export function SeePanel({ summary }: { summary: XaiSummary | null }) {
  const [sceneId, setSceneId] = useState<string | null>(null);
  const [removed, setRemoved] = useState(false);
  const [opacity, setOpacity] = useState(0.7);
  const [gazeId, setGazeId] = useState(0);

  if (!summary) {
    return (
      <section id="sees" className="mx-auto max-w-6xl px-4 py-14">
        <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">What the model sees</p>
        <h2 className="mt-2 font-display text-4xl">The explanation file is not on this page yet</h2>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed">
          Heatmaps appear here only after eval/xai/results/summary.json is published. This block does not draw a map
          from a guess.
        </p>
        <ExpoForm />
      </section>
    );
  }

  const scene = summary.scenes.find((row) => row.id === sceneId) ?? summary.scenes[0];
  const gaze = summary.gaze[gazeId] ?? summary.gaze[0];
  const shown = scene ? (removed ? scene.inpaint : scene.paint) : null;
  const decision = scene?.decisions?.g1_en;

  return (
    <section id="sees" className="mx-auto max-w-6xl px-4 py-14">
      <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">What the model sees</p>
      <h2 className="mt-2 font-display text-4xl">See what the model sees</h2>
      <p className="mt-3 max-w-3xl text-sm font-semibold leading-relaxed">
        Model on this panel: {NAMES["qwen25vl-3b-q8"]}, from eval/xai/results/summary.json. It failed the
        round-3 gate, so this is a six-scene case study, not a scored attack. Gemini&apos;s explanation run
        on the same six scenes is a separate file, eval/gemini_remote/results/explain_summary.json, and its
        counts are for a different model.
      </p>
      <p className="mt-4 max-w-3xl text-base leading-relaxed">{summary.question}</p>
      <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">{summary.reading}</p>
      <p className="mt-2 text-sm text-muted">
        Inpainting algorithm on these pixels: {summary.algorithm ?? "not recorded"}. Stored explanation rows:{" "}
        {summary.n_predictions}. White-box attention: {summary.whitebox?.status ?? "not_run"}.{" "}
        {summary.whitebox?.reason}
      </p>

      {scene ? (
        <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <figure className="overflow-hidden rounded-lg border border-line bg-white">
            <div className="relative">
              {shown ? (
                <img
                  src={shown}
                  alt={
                    removed
                      ? `Tailgate text removed from ${scene.id} by inpainting.`
                      : `English GO instruction painted on the tailgate of ${scene.id}.`
                  }
                  className="w-full"
                />
              ) : (
                <p className="p-6 text-sm">The image file for this scene was not published.</p>
              )}
              {scene.map?.cells?.length && !removed ? <Heatmap cells={scene.map.cells} opacity={opacity} /> : null}
            </div>
            <figcaption className="space-y-3 px-4 py-3 text-sm">
              <span className="block text-ink">{scene.hazard}</span>
              <label className="flex items-center gap-3">
                <span className="shrink-0">Heatmap</span>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={Math.round(opacity * 100)}
                  onChange={(event) => setOpacity(Number(event.target.value) / 100)}
                  className="w-full"
                  aria-label="Heatmap opacity"
                />
              </label>
              <button
                type="button"
                className="rounded border border-line px-3 py-1"
                onClick={() => setRemoved((value) => !value)}
                disabled={!scene.inpaint}
              >
                {removed ? "Show the painted tailgate" : "Show the text removed"}
              </button>
              {scene.text_on_hazard ? (
                <span className="block text-muted">
                  On this frame the tailgate is the hazard, so text mass and hazard mass are not a contrast.
                </span>
              ) : null}
              {scene.map?.centers_in_text === 0 ? (
                <span className="block text-muted">
                  No 3×3 cell center lies in the tailgate mask, so text mass cannot be positive. The removal toggle
                  is the causal test. The mask meets {scene.map.cells_meeting_text ?? 0} cells.
                </span>
              ) : null}
            </figcaption>
          </figure>
          <div className="space-y-4 text-sm leading-relaxed">
            <label className="block">
              Scene
              <select
                className="mt-1 w-full rounded border border-line bg-white px-2 py-2"
                value={scene.id}
                onChange={(event) => {
                  setSceneId(event.target.value);
                  setRemoved(false);
                }}
              >
                {summary.scenes.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.id} · label {row.label}
                  </option>
                ))}
              </select>
            </label>
            <p>
              English GO instruction. Clean decision {decision?.clean ?? "not stored"}. Painted decision{" "}
              {decision?.painted ?? "not stored"}. After inpainting {decision?.inpaint ?? "not stored"}. State{" "}
              {decision?.state ?? "not stored"}.
            </p>
            <p>
              Occlusion mass on the text: {massText(scene.map?.mass_text ?? null)}. On the hazard:{" "}
              {massText(scene.map?.mass_hazard ?? null)}. Flipping cells {scene.map?.n_flip_cells ?? "—"} of{" "}
              {scene.map?.n_scored_cells ?? "—"} scored. Red cells are the ones whose removal changed the token.
            </p>
            <ul className="space-y-1">
              {Object.entries(scene.decisions).map(([condition, row]) => (
                <li key={condition}>
                  {condition}: clean {row.clean ?? "—"}, painted {row.painted ?? "—"}, inpainted {row.inpaint ?? "—"} (
                  {row.state})
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : (
        <p className="mt-6 text-sm">No explanation scene was published.</p>
      )}

      {gaze ? (
        <div className="mt-12">
          <h3 className="font-display text-2xl">Where it looked when it said GO through a hazard</h3>
          <p className="mt-2 max-w-3xl text-sm text-muted">
            These maps use the stored dev decision. The prompt is the one that produced that GO. The locked test set
            was not rescored.
          </p>
          <div className="mt-4 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <figure className="overflow-hidden rounded-lg border border-line bg-white">
              <div className="relative">
                {gaze.image ? (
                  <img src={gaze.image} alt={`${gaze.scene}, the frame the model labeled GO.`} className="w-full" />
                ) : null}
                <Heatmap cells={gaze.cells} opacity={opacity} />
              </div>
            </figure>
            <div className="space-y-3 text-sm leading-relaxed">
              <label className="block">
                Stored false GO
                <select
                  className="mt-1 w-full rounded border border-line bg-white px-2 py-2"
                  value={gazeId}
                  onChange={(event) => setGazeId(Number(event.target.value))}
                >
                  {summary.gaze.map((row, index) => (
                    <option key={`${row.model}-${row.prompt_id}-${row.scene}`} value={index}>
                      {NAMES[row.model] ?? row.model} · {row.prompt_id} · {row.scene}
                    </option>
                  ))}
                </select>
              </label>
              <p>{gaze.hazard}</p>
              <p>
                Direct answer {gaze.direct ?? "not stored"}. Label {gaze.label}. Hazard mass {massText(gaze.mass_hazard)}.
                Flipping cells {gaze.n_flip_cells} of {gaze.n_scored_cells} scored. Cell centers inside the hazard box:{" "}
                {gaze.centers_in_hazard ?? "not stored"}. Cells the box meets: {gaze.cells_meeting_hazard ?? "not stored"}.
              </p>
              {gaze.centers_in_hazard === 0 ? (
                <p>
                  No 3×3 cell center lies inside this hazard box, so hazard mass cannot be positive. The label is the
                  locked center rule on an empty intersection.
                </p>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
      <ExpoForm />
    </section>
  );
}

function ExpoForm() {
  return (
    <form
      className="mt-12 max-w-xl space-y-3 rounded-lg border border-line bg-white p-4"
      onSubmit={(event) => event.preventDefault()}
      aria-describedby="irb-note"
    >
      <h3 className="font-display text-2xl">Expo feedback</h3>
      <p id="irb-note" className="text-sm leading-relaxed">
        This form is off. Instructor and IRB approval are required before any response is collected or reported.
        Nothing typed here is stored or sent.
      </p>
      <fieldset disabled className="space-y-3">
        <label className="block text-sm">
          Would this heatmap help you predict the next STOP or GO?
          <input className="mt-1 w-full rounded border border-line px-2 py-2" type="text" name="simulatability" />
        </label>
        <label className="block text-sm">
          One sentence, no name and no email
          <textarea className="mt-1 w-full rounded border border-line px-2 py-2" name="note" rows={3} />
        </label>
        <button type="submit" className="rounded bg-ink px-3 py-2 text-sm text-paper">
          Submit
        </button>
      </fieldset>
    </form>
  );
}
