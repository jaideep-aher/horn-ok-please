"use client";

import { LiveDialog } from "@/components/live-dialog";

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
        <nav className="flex flex-1 gap-1 overflow-x-auto text-sm" aria-label="Page">
          {LINKS.map(([id, label]) => (
            <a key={id} href={`#${id}`} className="shrink-0 rounded px-2 py-1 text-paper/80 hover:text-yellow">
              {label}
            </a>
          ))}
        </nav>
        <LiveDialog />
      </div>
    </header>
  );
}
