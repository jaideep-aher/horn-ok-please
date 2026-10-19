"use client";

import { useEffect, useRef, useState } from "react";

import { LiveDialog } from "@/components/live-dialog-gate";
import { liveMode } from "@/lib/live";

const LINKS = [
  ["findings", "Findings"],
  ["diagnostic", "Diagnostic"],
  ["sees", "Sees"],
  ["photos", "Photographs"],
  ["studio", "Studio"],
  ["defense", "Defense"],
  ["literacy", "Reading"],
  ["misuse", "Misuse"],
  ["methods", "Methods"],
] as const;

export function SiteHeader() {
  const [active, setActive] = useState("");
  const [overflows, setOverflows] = useState(false);
  const listRef = useRef<HTMLUListElement>(null);

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    const measure = () => {
      const padLeft = Number.parseFloat(getComputedStyle(list).paddingLeft) || 0;
      const gap = Number.parseFloat(getComputedStyle(list).columnGap) || 0;
      const items = [...list.children] as HTMLElement[];
      let needed = 0;
      items.forEach((item, index) => {
        needed += item.offsetWidth;
        if (index > 0) needed += gap;
      });
      const available = list.clientWidth - padLeft;
      const next = needed > available + 1;
      setOverflows((prev) => (prev === next ? prev : next));
    };
    const observer = new ResizeObserver(measure);
    observer.observe(list);
    for (const child of list.children) observer.observe(child);
    measure();
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const ratios = new Map<string, IntersectionObserverEntry>();
    let observer: IntersectionObserver | null = null;
    let watching = new Map<string, Element>();

    const pick = () => {
      const visible = [...ratios.values()].filter((entry) => entry.isIntersecting);
      if (!visible.length) return;
      visible.sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      const id = visible[0].target.id;
      setActive((prev) => (prev === id ? prev : id));
    };

    const connect = () => {
      const sections = new Map<string, Element>();
      for (const [id] of LINKS) {
        const el = document.getElementById(id);
        if (el) sections.set(id, el);
      }
      let same = sections.size === watching.size;
      if (same) {
        for (const [id, el] of sections) {
          if (watching.get(id) !== el) {
            same = false;
            break;
          }
        }
      }
      if (same && observer) return;
      watching = sections;
      observer?.disconnect();
      ratios.clear();
      observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.target.id) ratios.set(entry.target.id, entry);
          }
          pick();
        },
        { rootMargin: "-80px 0px -55% 0px", threshold: [0, 0.2, 0.5] },
      );
      for (const el of sections.values()) observer.observe(el);
    };

    connect();
    const mutations = new MutationObserver(connect);
    mutations.observe(document.body, { childList: true, subtree: true });
    return () => {
      observer?.disconnect();
      mutations.disconnect();
    };
  }, []);

  useEffect(() => {
    const list = listRef.current;
    if (!list || !active) return;
    const link = list.querySelector<HTMLAnchorElement>(`a[href="#${active}"]`);
    if (!link) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const left = link.offsetLeft;
    const right = left + link.offsetWidth;
    const viewLeft = list.scrollLeft;
    const viewRight = viewLeft + list.clientWidth;
    if (left < viewLeft) {
      list.scrollTo({ left: Math.max(0, left - 8), behavior: reduce ? "auto" : "smooth" });
    } else if (right > viewRight - 32) {
      list.scrollTo({
        left: right - list.clientWidth + 40,
        behavior: reduce ? "auto" : "smooth",
      });
    }
  }, [active]);

  return (
    <header className="sticky top-0 z-40 border-b-4 border-yellow bg-ink text-paper">
      <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-2">
        <a href="#top" className="inline-flex min-h-11 items-center font-stencil text-lg tracking-wide text-yellow">
          Horn OK Please
        </a>
        <nav aria-label="On this page" className="relative min-w-0 flex-1">
          <ul
            ref={listRef}
            tabIndex={0}
            className={`flex gap-1 overflow-x-auto text-sm focus-visible:ring-2 focus-visible:ring-yellow focus-visible:ring-inset focus-visible:outline-none ${
              overflows ? "pr-8" : ""
            }`}
          >
            {LINKS.map(([id, label]) => (
              <li key={id} className="shrink-0">
                <a
                  href={`#${id}`}
                  aria-current={active === id ? "true" : undefined}
                  className={`inline-flex min-h-11 items-center px-3 focus-visible:ring-2 focus-visible:ring-yellow focus-visible:ring-inset focus-visible:outline-none ${
                    active === id ? "text-yellow underline decoration-2 underline-offset-8" : "text-paper/80 hover:text-yellow"
                  }`}
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
          {overflows ? (
            <span
              aria-hidden="true"
              className="pointer-events-none absolute inset-y-0 right-0 flex w-8 items-center justify-end bg-gradient-to-l from-ink to-transparent text-lg text-yellow"
            >
              ›
            </span>
          ) : null}
        </nav>
        {liveMode ? <LiveDialog /> : null}
      </div>
    </header>
  );
}
