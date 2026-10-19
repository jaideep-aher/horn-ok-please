"use client";

type PhotoSummary = {
  split: string;
  algorithm: string | null;
  model?: string | null;
  reading: string;
  n_predictions: number;
  n_driving: number;
  n_paint: number;
  n_literacy: number;
};

export type { PhotoSummary };

export function PhotoGallery({ summary }: { summary: PhotoSummary | null }) {
  return (
    <section id="photos" className="mx-auto max-w-6xl px-4 py-14">
      <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Real photographs</p>
      <h2 className="mt-2 font-display text-4xl">Photos coming after privacy review</h2>
      <p className="mt-4 max-w-3xl text-sm leading-relaxed">
        The Commons frames are not on this page. Painted registration numbers and phone numbers stayed readable after
        the bumper-plate boxes, so the pictures are withheld. Nothing here is a made-up rate.
      </p>
      {summary ? (
        <>
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted">{summary.reading}</p>
          <p className="mt-2 text-sm text-muted">
            Fill recorded for these pixels: {summary.algorithm ?? "not recorded"}. Model {summary.model ?? "not recorded"}.
            Driving views {summary.n_driving}. Paint cohort {summary.n_paint}. Front and side literacy views{" "}
            {summary.n_literacy}. Stored rows {summary.n_predictions}.
          </p>
        </>
      ) : (
        <p className="mt-4 max-w-3xl text-sm leading-relaxed text-muted">
          Stored photograph counts appear here when photos.json is published.
        </p>
      )}
    </section>
  );
}
