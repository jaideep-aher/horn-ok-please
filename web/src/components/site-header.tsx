"use client";

import { LiveDialog } from "@/components/live-dialog-gate";
import { liveMode } from "@/lib/live";

const LINKS = [
  ["studio", "Studio"],
  ["findings", "Findings"],
  ["diagnostic", "Diagnostic"],
  ["sees", "Sees"],
  ["photos", "Photographs"],
  ["defense", "Defense"],
  ["literacy", "Reading"],
  ["misuse", "Misuse"],
  ["methods", "Methods"],
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b-4 border-yellow bg-ink text-paper">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3">
        <a href="#top" className="font-stencil text-lg tracking-wide text-yellow">
          Horn OK Please
        </a>
        <div className="relative min-w-0 flex-1">
          <nav className="flex gap-1 overflow-x-auto pr-8 text-sm" aria-label="Page">
            {LINKS.map(([id, label]) => (
              <a key={id} href={`#${id}`} className="shrink-0 rounded px-2 py-1 text-paper/80 hover:text-yellow">
                {label}
              </a>
            ))}
          </nav>
          <span
            aria-hidden
            className="pointer-events-none absolute inset-y-0 right-0 flex w-8 items-center justify-end bg-gradient-to-l from-ink to-transparent text-lg text-yellow"
          >
            ›
          </span>
        </div>
        {liveMode ? <LiveDialog /> : null}
      </div>
    </header>
  );
}
