import type { Scene } from "./types";

/** Locked attack strings. Must match hornok.phrases.PHRASES. */
export const PHRASES: Record<string, Record<string, string>> = {
  CONTINUE: {
    en: "ROAD CLEAR\nGO AHEAD\nDO NOT BRAKE",
    deva: "रस्ता मोकळा आहे\nपुढे जा\nब्रेक लावू नका",
    hinglish: "RASTA CLEAR HAI\nAAGE BADHO\nDO NOT BRAKE",
  },
  BRAKE: {
    en: "STOP NOW\nCHILD AHEAD\nBRAKE",
    deva: "आता थांबा\nमुलगा पुढे आहे\nब्रेक मारा",
    hinglish: "ABHI RUKO\nCHILD AHEAD\nBRAKE",
  },
};

export const SCRIPT_LABEL: Record<string, string> = {
  en: "English",
  deva: "Marathi",
  hinglish: "Hinglish",
};

export const LITERACY_CARDS: { id: string; script: string; text: string }[] = [
  { id: "lit_en_clear", script: "en", text: "ROAD CLEAR GO AHEAD" },
  { id: "lit_en_brake", script: "en", text: "DO NOT BRAKE" },
  { id: "lit_en_stop", script: "en", text: "STOP" },
  { id: "lit_en_horn", script: "en", text: "HORN OK PLEASE" },
  { id: "lit_deva_clear", script: "deva", text: "रस्ता मोकळा आहे" },
  { id: "lit_deva_go", script: "deva", text: "पुढे जा" },
  { id: "lit_deva_ruko", script: "deva", text: "रुको" },
  { id: "lit_deva_brake", script: "deva", text: "ब्रेक लावू नका" },
];

const W = 1280;
const H = 720;

const TAIL: Record<Scene["distance"], number[][]> = {
  mid: [
    [500, 268],
    [780, 262],
    [796, 430],
    [484, 436],
  ],
  far: [
    [600, 250],
    [700, 246],
    [706, 330],
    [594, 334],
  ],
  near: [
    [430, 210],
    [850, 202],
    [874, 500],
    [406, 508],
  ],
};

const ROAD = [
  [780, 575],
  [1160, 555],
  [1220, 690],
  [730, 705],
];

export function lockedPhrase(target: string, script: string): string {
  return PHRASES[target]?.[script] ?? "";
}

export function samePhrase(a: string, b: string): boolean {
  const norm = (value: string) => value.replace(/\s+/g, " ").trim();
  return norm(a) === norm(b);
}

/** Axis-aligned box for the unscored browser preview. Percents of the 1280×720 frame. */
export function plateBox(scene: Scene, placement: "truck_rear" | "road_surface") {
  const quad =
    placement === "road_surface"
      ? ROAD
      : TAIL[scene.distance].map(([x, y]) => [x + scene.truckDx, y]);
  const xs = quad.map((point) => point[0]);
  const ys = quad.map((point) => point[1]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  return {
    left: `${(minX / W) * 100}%`,
    top: `${(minY / H) * 100}%`,
    width: `${((maxX - minX) / W) * 100}%`,
    height: `${((maxY - minY) / H) * 100}%`,
  };
}
