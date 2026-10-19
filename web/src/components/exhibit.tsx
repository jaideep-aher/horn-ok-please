"use client";

import { useEffect, useState } from "react";

import { DefenseSection } from "@/components/defense-section";
import { Findings } from "@/components/findings";
import { Hero } from "@/components/hero";
import { LiteracySection } from "@/components/literacy-section";
import { Methods } from "@/components/methods";
import { Misuse } from "@/components/misuse";
import { Painter } from "@/components/painter";
import { Round2Report, type Round2Summary } from "@/components/round2-report";
import { DevReport, type DevSummary } from "@/components/dev-report";
import { Round3Report, type Round3Summary } from "@/components/round3-report";
import { GeminiReport, type GeminiSummary } from "@/components/gemini-report";
import { PhotoGallery, type PhotoSummary } from "@/components/photo-gallery";
import { SeePanel, type XaiSummary } from "@/components/see-panel";
import { SiteHeader } from "@/components/site-header";
import { asset } from "@/lib/asset";
import type { Summary } from "@/lib/types";

type Status = "loading" | "pending" | "ready" | "error";

async function loadJson<T>(url: string): Promise<T | null> {
  const response = await fetch(url);
  if (!response.ok) return null;
  return (await response.json()) as T;
}

export function Exhibit() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [pilot, setPilot] = useState<Summary | null>(null);
  const [round3, setRound3] = useState<Round3Summary | null>(null);
  const [round2, setRound2] = useState<Round2Summary | null>(null);
  const [dev, setDev] = useState<DevSummary | null>(null);
  const [xai, setXai] = useState<XaiSummary | null>(null);
  const [photos, setPhotos] = useState<PhotoSummary | null>(null);
  const [gemini, setGemini] = useState<GeminiSummary | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    let cancel = false;
    Promise.all([
      loadJson<Round3Summary>(asset("/data/round3.json")),
      loadJson<Round2Summary>(asset("/data/round2.json")),
      loadJson<Summary>(asset("/data/pilot.json")),
      loadJson<Summary & Round2Summary & Round3Summary>(asset("/data/summary.json")),
      loadJson<DevSummary>(asset("/data/dev.json")),
      loadJson<XaiSummary>(asset("/data/xai.json")),
      loadJson<PhotoSummary>(asset("/data/photos.json")),
      loadJson<GeminiSummary>(asset("/data/gemini.json")),
    ])
      .then(([r3, r2, pilotData, current, devData, xaiData, photoData, geminiData]) => {
        if (cancel) return;
        const round3Data = r3?.round === 3 ? r3 : current?.round === 3 ? current : null;
        const round2Data = r2?.round === 2 ? r2 : current?.round === 2 ? current : null;
        setRound3(round3Data);
        setRound2(round2Data);
        setDev(devData?.split === "dev" ? devData : null);
        setXai(xaiData?.split === "xai" ? xaiData : null);
        setPhotos(photoData?.split === "photos" ? photoData : null);
        setGemini(geminiData?.flash ? geminiData : null);
        setPilot(pilotData);
        setSummary(current);
        if (round3Data?.gate || round2Data?.gate) setStatus("ready");
        else if (current) setStatus(current.pending || !current.asr ? "pending" : "ready");
        else setStatus("error");
      })
      .catch(() => {
        if (!cancel) setStatus("error");
      });
    return () => {
      cancel = true;
    };
  }, []);

  const showingRound3 = round3?.round === 3;
  const showingRound2 = !showingRound3 && round2?.round === 2;
  const studioSummary = showingRound3 || showingRound2 ? pilot : summary;
  const studioStatus: Status = showingRound3 || showingRound2 ? (pilot?.asr ? "ready" : "pending") : status;

  return (
    <>
      <a href="#studio" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-yellow focus:p-2">
        Skip to the studio
      </a>
      <SiteHeader />
      <main>
        <Hero
          summary={round2 ? summary : studioSummary}
          status={round2 ? status : studioStatus}
          note={
            showingRound3
              ? "Round 3 figures come from eval/round3/results. The prompt diagnostic, when it is on this page, comes from eval/dev/results and does not rescore those scenes. Nothing on this page is a road test."
              : showingRound2
                ? "Round 2 figures come from eval/round2/results. The studio below still shows the round-1 pilot trials. Nothing on this page is a road test."
                : undefined
          }
        />
        {showingRound3 && round3 ? <Round3Report summary={round3} /> : null}
        {gemini ? <GeminiReport summary={gemini} /> : null}
        {dev?.blocks?.length ? <DevReport summary={dev} /> : null}
        <SeePanel summary={xai} />
        <PhotoGallery summary={photos} />
        {showingRound3 && round2 ? (
          <details className="mx-auto max-w-6xl px-4 py-6">
            <summary className="cursor-pointer font-display text-2xl">
              Round 2: the four-way gate failed
            </summary>
            <Round2Report summary={round2} />
          </details>
        ) : null}
        {showingRound2 && round2 ? <Round2Report summary={round2} /> : null}
        <Painter summary={studioSummary} status={studioStatus} />
        {showingRound3 || showingRound2 ? (
          <details className="mx-auto max-w-6xl px-4 py-6">
            <summary className="cursor-pointer font-display text-2xl">
              Pilot, round 1: SmolVLM did not answer the driving prompt
            </summary>
            <Findings summary={pilot} status={studioStatus} anchor="pilot" />
            <DefenseSection summary={pilot} status={studioStatus} />
            <LiteracySection summary={pilot} status={studioStatus} />
          </details>
        ) : (
          <>
            <Findings summary={summary} status={status} />
            <DefenseSection summary={summary} status={status} />
            <LiteracySection summary={summary} status={status} />
          </>
        )}
        <Misuse />
        <Methods summary={summary} />
      </main>
      <footer className="border-t border-line px-4 py-8 text-sm text-muted">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:justify-between">
          <p>Horn OK Please · Jaideep (Jay) Aher · Duke AIPI 590</p>
          <p>Scenes CC-BY-4.0. Code MIT. Noto fonts under the SIL Open Font License.</p>
        </div>
      </footer>
    </>
  );
}
