"use client";

import { useState } from "react";

type Actions = Record<string, string | null | undefined>;
type MapCell = { r: number; c: number; saliency: number | null; action?: string | null };
type OcclusionMap = {
  label?: string;
  mass_text?: number | null;
  n_flip_cells?: number;
  n_scored_cells?: number;
  centers_in_text?: number | null;
  mask_action?: string | null;
  mask_flipped?: boolean;
  cells?: MapCell[];
};
type Scene = {
  id: string;
  country: string;
  author: string;
  license: string;
  source_url: string;
  hazard_kind?: string;
  original: string;
  removed: string;
  paint: string;
  hazard: string;
  hazard_paint: string;
  actions: Actions;
  map?: OcclusionMap | null;
};
export type PhotoSummary = {
  split: string;
  algorithm: string | null;
  reading: string;
  n_predictions: number;
  n_driving: number;
  n_paint: number;
  n_literacy: number;
  scenes: Scene[];
};

const VIEWS = [
  ["original", "Original"],
  ["removed", "Text removed"],
  ["paint", "English GO line"],
  ["hazard", "Pasted hazard"],
  ["hazard_paint", "Hazard plus English"],
] as const;

export function PhotoGallery({ summary }: { summary: PhotoSummary | null }) {
  const [index, setIndex] = useState(0);
  const [view, setView] = useState<(typeof VIEWS)[number][0]>("original");
  const [showMap, setShowMap] = useState(true);

  if (!summary) {
    return (
      <section id="photos" className="mx-auto max-w-6xl px-4 py-14">
        <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Real photographs</p>
        <h2 className="mt-2 font-display text-4xl">The real-photo file is not on this page yet</h2>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed">
          Commons frames appear here only after eval/photos/results/summary.json is published. Plates and faces
          on this page are blurred. Nothing here is a made-up rate.
        </p>
      </section>
    );
  }

  const scene = summary.scenes[index];
  const src = scene ? scene[view] : null;
  const actionKey =
    view === "paint" ? "g1_en" : view === "hazard_paint" ? "hazard_g1_en" : view === "hazard" ? "hazard" : view;

  return (
    <section id="photos" className="mx-auto max-w-6xl px-4 py-14">
      <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Real photographs</p>
      <h2 className="mt-2 font-display text-4xl">Commons trucks, before and after</h2>
      <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted">{summary.reading}</p>
      <p className="mt-2 text-sm text-muted">
        Fill recorded for these pixels: {summary.algorithm ?? "not recorded"}. Driving views {summary.n_driving}. Paint
        cohort {summary.n_paint}. Front and side literacy views {summary.n_literacy}. Stored rows {summary.n_predictions}.
        Plates and faces are blurred on this page. Credits are in eval/photos/CREDITS.md.
      </p>
      {scene ? (
        <div className="mt-8 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <figure className="relative overflow-hidden rounded-lg border border-line bg-white">
            <img src={src ?? ""} alt={`${scene.id}, ${view}, plates and faces blurred.`} className="w-full" />
            {view === "paint" && showMap && scene.map?.cells?.length ? (
              <div className="pointer-events-none absolute inset-0 grid grid-cols-6 grid-rows-6">
                {scene.map.cells.map((cell) => (
                  <div
                    key={`${cell.r}-${cell.c}`}
                    className={
                      cell.saliency === 1
                        ? "bg-red-600/45"
                        : cell.saliency === 0
                          ? "bg-white/10"
                          : "bg-transparent"
                    }
                  />
                ))}
              </div>
            ) : null}
            <figcaption className="space-y-3 px-4 py-3 text-sm">
              <span className="block text-ink">
                {scene.id} · {scene.country} · {scene.license}
              </span>
              <span className="block text-muted">
                {scene.author}.{" "}
                <a className="underline" href={scene.source_url}>
                  Wikimedia Commons
                </a>
                . The pasted hazard is an illustration ({scene.hazard_kind ?? "none"}).
              </span>
              <label className="flex items-center gap-2 text-muted">
                <input
                  type="checkbox"
                  checked={showMap}
                  onChange={(event) => setShowMap(event.target.checked)}
                />
                6×6 occlusion on the English line
              </label>
              <div className="flex flex-wrap gap-2">
                {VIEWS.map(([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    className={`rounded border px-3 py-1 ${view === id ? "border-ink bg-ink text-paper" : "border-line"}`}
                    onClick={() => setView(id)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </figcaption>
          </figure>
          <div className="space-y-3 text-sm leading-relaxed">
            <label className="block">
              Photograph
              <select
                className="mt-1 w-full rounded border border-line bg-white px-2 py-2"
                value={scene.id}
                onChange={(event) => {
                  const next = summary.scenes.findIndex((row) => row.id === event.target.value);
                  setIndex(next < 0 ? 0 : next);
                  setView("original");
                }}
              >
                {summary.scenes.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.id} · {row.country}
                  </option>
                ))}
              </select>
            </label>
            <p>
              Qwen2.5-VL 3B Q8 on this view: {scene.actions[actionKey] ?? "not stored"}. The 6×6 map is on the
              English replacement. Label {scene.map?.label ?? "not stored"}. Text mass{" "}
              {scene.map?.mass_text ?? "not stored"}. Cell centers inside the text{" "}
              {scene.map?.centers_in_text ?? "not stored"}. Mask cell {scene.map?.mask_action ?? "not stored"}.
              Original{" "}
              {scene.actions.original ?? "not stored"}. Text removed {scene.actions.removed ?? "not stored"}. English{" "}
              {scene.actions.g1_en ?? "not stored"}. Devanagari {scene.actions.g1_deva ?? "not stored"}. Urdu{" "}
              {scene.actions.g1_ur ?? "not stored"}. Benign {scene.actions.benign ?? "not stored"}.
            </p>
          </div>
        </div>
      ) : (
        <p className="mt-6 text-sm">No paint-cohort photograph was published.</p>
      )}
    </section>
  );
}
