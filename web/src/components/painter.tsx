"use client";

import { useEffect, useMemo, useState } from "react";

import { ActionChip } from "@/components/action-chip";
import { LiveDialog } from "@/components/live-dialog-gate";
import { Picture } from "@/components/picture";
import { Button } from "@/components/ui/button";
import { isTargetedFlip, stimulusPath, trialFor } from "@/lib/format";
import { liveMode } from "@/lib/live";
import { lockedPhrase, plateBox, samePhrase, SCRIPT_LABEL } from "@/lib/phrases";
import { MODELS, SCENES, modelShort, type Summary, type Trial } from "@/lib/types";

type Script = "" | "en" | "deva" | "hinglish";
type Placement = "truck_rear" | "road_surface";
type Defense = "none" | "prompt" | "ocr";

/**
 * gemini.json records a gate total for gemini-3.8-flash and no per-scene action
 * for these frames. Until that file has trials, open on the round-1 checkpoint
 * with the most parsed stored actions (SmolVLM 500M float32 in the committed pilot).
 */
const FALLBACK_MODEL = "smolvlm-500m-hf";

function parsedActions(trials: Trial[] | undefined, modelId: string): number {
  return (trials ?? []).filter((trial) => trial.model === modelId && trial.action !== "UNPARSEABLE").length;
}

function bestStoredModel(trials: Trial[] | undefined): string {
  if (!trials?.length) return FALLBACK_MODEL;
  return [...MODELS].sort((a, b) => parsedActions(trials, b.id) - parsedActions(trials, a.id))[0]?.id ?? FALLBACK_MODEL;
}

export function Painter({
  summary,
  status,
}: {
  summary: Summary | null;
  status: "loading" | "pending" | "ready" | "error";
}) {
  const [sceneId, setSceneId] = useState("ped_crossing");
  const [script, setScript] = useState<Script>("deva");
  const [placement, setPlacement] = useState<Placement>("truck_rear");
  const [size, setSize] = useState(100);
  const [custom, setCustom] = useState("");
  const [defense, setDefense] = useState<Defense>("none");
  const [model, setModel] = useState(FALLBACK_MODEL);
  const [modelPicked, setModelPicked] = useState(false);
  const bestModel = useMemo(() => bestStoredModel(summary?.trials), [summary]);

  useEffect(() => {
    if (!modelPicked) setModel(bestModel);
  }, [bestModel, modelPicked]);

  const scene = SCENES.find((item) => item.id === sceneId) ?? SCENES[0];
  const phrase = script ? lockedPhrase(scene.target, script) : "";
  const customActive = script !== "" && custom.trim() !== "" && !samePhrase(custom, phrase);
  const rendered = script !== "" && !customActive && size === 100;
  const imageSrc = rendered
    ? stimulusPath(scene.id, script, placement)
    : stimulusPath(scene.id, "", placement);

  const scoredPlacement = placement === "truck_rear";
  const trials = summary?.trials;
  const condition = script && rendered ? "attack" : "clean";
  const trialScript = condition === "attack" ? script : "";
  const trial = rendered || script === ""
    ? trialFor(trials, scene.id, model, condition, trialScript, defense, "truck_rear")
    : undefined;
  const cleanTrial = trialFor(trials, scene.id, model, "clean", "", "none", "truck_rear");
  const flip =
    condition === "attack" && trial && cleanTrial
      ? isTargetedFlip(cleanTrial.action, trial.action, scene.target)
      : false;

  const box = useMemo(() => plateBox(scene, placement), [scene, placement]);
  const previewText = customActive ? custom : phrase;
  const showOverlay = script !== "" && !rendered;

  const alt = `${scene.title}. ${scene.hazard}${
    rendered ? ` Painted ${SCRIPT_LABEL[script]} text is on the ${placement === "truck_rear" ? "tailgate" : "road"}.` : ""
  }`;

  return (
    <section id="studio" className="border-t border-line bg-white/40">
      <div className="mx-auto max-w-6xl px-4 py-14">
        <p className="font-stencil text-sm tracking-[0.16em] text-signal uppercase">Studio</p>
        <h2 className="mt-2 font-display text-4xl">Paint the frame, then read the action</h2>
        <p className="mt-3 max-w-3xl text-muted">
          Pick a scene, a script, and where the words sit. At full size the picture is the committed
          illustration for that scene. A smaller plate, or wording you type yourself, is drawn here only.
          No model in the study saw that variant. Road paint was rendered for every scene and was not part
          of the scored attack-success rate.
        </p>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
          The chips below are the round-1 SmolVLM pilot. The studio opens on the round-1 checkpoint with
          the most parsed stored actions for these scenes. Gemini 3.8 Flash passed the STOP versus GO gate,
          and the published Gemini file has no per-scene action for these frames, so those calls are not on
          these chips. The other round-1 checkpoints are a secondary choice. These chips are four actions,
          not the STOP versus GO roster. STOP versus GO was run on Qwen2.5-VL 3B Instruct Q8_0 and Q4_K_M
          (`Qwen2.5-VL-3B-Instruct-Q8_0.gguf`, `Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf`), Gemma 3 4B IT Q8_0 and
          Q4_K_M (`gemma-3-4b-it-Q8_0.gguf`, `gemma-3-4b-it-Q4_K_M.gguf`), and Gemini 3.8 Flash
          (`gemini-3.8-flash`). The open-weight checkpoints failed the gate. Their STOP and GO counts are in the
          round-3 section, not in these chips. Gemma 3 4B IT is not a model named Gemma 4B.
        </p>

        <div className="mt-8 flex gap-2 overflow-x-auto pb-2">
          {SCENES.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                setSceneId(item.id);
                setCustom("");
              }}
              className={`w-36 shrink-0 overflow-hidden rounded-md border text-left ${
                item.id === scene.id ? "border-ink ring-2 ring-yellow" : "border-line"
              }`}
            >
              <Picture
                src={`/stimuli/clean/${item.id}.png`}
                alt=""
                className="h-20 w-full object-cover"
              />
              <span className="block px-2 py-1 text-xs">{item.title}</span>
            </button>
          ))}
        </div>

        <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1.4fr)_minmax(18rem,0.8fr)]">
          <div>
            <div className="relative overflow-hidden rounded-lg border border-line bg-ink">
              <Picture src={imageSrc} alt={alt} className="h-auto w-full" />
              {showOverlay ? (
                <div
                  className={`absolute flex items-center justify-center overflow-hidden px-1 text-center leading-tight ${
                    placement === "road_surface" ? "text-white" : "text-ink"
                  }`}
                  style={{
                    ...box,
                    fontSize: `${Math.max(8, (size / 100) * (placement === "truck_rear" ? 15 : 18))}px`,
                    background:
                      placement === "road_surface" ? "transparent" : "rgba(240, 180, 41, 0.88)",
                  }}
                >
                  <span
                    className={script === "deva" || /[\u0900-\u097F]/.test(previewText) ? "font-deva" : "font-stencil"}
                    style={{ whiteSpace: "pre-line" }}
                  >
                    {previewText}
                  </span>
                </div>
              ) : null}
            </div>
            <p className="mt-2 text-sm text-muted">{scene.hazard}</p>
            {showOverlay ? (
              <p className="mt-1 text-sm text-signal">
                Preview only. These pixels were not sent to a model, and there is no action for them.
              </p>
            ) : null}
            {!scoredPlacement && rendered ? (
              <p className="mt-1 text-sm text-muted">
                This road-paint file is in the repository. Model actions below stay on the tailgate trial,
                because that is the scored placement.
              </p>
            ) : null}
          </div>

          <div className="space-y-5">
            <fieldset>
              <legend className="font-stencil text-xs tracking-widest uppercase">Script</legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {(
                  [
                    ["", "Clean"],
                    ["en", "English"],
                    ["deva", "मराठी"],
                    ["hinglish", "Hinglish"],
                  ] as const
                ).map(([id, label]) => (
                  <Button
                    key={id || "clean"}
                    type="button"
                    size="sm"
                    variant={script === id ? "default" : "outline"}
                    onClick={() => setScript(id)}
                  >
                    <span className={id === "deva" ? "font-deva" : undefined}>{label}</span>
                  </Button>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend className="font-stencil text-xs tracking-widest uppercase">Placement</legend>
              <div className="mt-2 flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant={placement === "truck_rear" ? "default" : "outline"}
                  onClick={() => setPlacement("truck_rear")}
                >
                  Truck tail
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={placement === "road_surface" ? "default" : "outline"}
                  onClick={() => setPlacement("road_surface")}
                >
                  Road paint
                </Button>
              </div>
            </fieldset>

            <label className="block">
              <span className="font-stencil text-xs tracking-widest uppercase">
                Plate size {size}%
              </span>
              <input
                type="range"
                min={45}
                max={100}
                value={size}
                onChange={(event) => setSize(Number(event.target.value))}
                className="mt-2 w-full accent-yellow"
                disabled={script === ""}
                aria-valuetext={`${size} percent. Only 100 percent was scored.`}
              />
              <span className="text-xs text-muted">Only 100% was scored. It fills the tailgate quadrilateral.</span>
            </label>

            <label className="block space-y-1">
              <span className="font-stencil text-xs tracking-widest uppercase">Wording</span>
              <textarea
                value={custom}
                onChange={(event) => setCustom(event.target.value.slice(0, 80))}
                placeholder={phrase || "Select a script to paint"}
                disabled={script === ""}
                rows={3}
                className={`w-full rounded-md border border-line bg-white px-3 py-2 text-sm ${
                  script === "deva" ? "font-deva" : ""
                }`}
              />
              <span className="text-xs text-muted">
                Empty uses the locked phrase for this scene’s target ({scene.target}). Typed text is not scored.
              </span>
            </label>

            <fieldset>
              <legend className="font-stencil text-xs tracking-widest uppercase">Defense</legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {(
                  [
                    ["none", "None"],
                    ["prompt", "Prompt"],
                    ["ocr", "OCR mask"],
                  ] as const
                ).map(([id, label]) => (
                  <Button
                    key={id}
                    type="button"
                    size="sm"
                    variant={defense === id ? "default" : "outline"}
                    onClick={() => setDefense(id)}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend className="font-stencil text-xs tracking-widest uppercase">Round 1 model</legend>
              <p className="mt-1 text-xs text-muted">
                SmolVLM {modelShort(bestModel)} is the default. Round 1 pilot, not the Gemini gate.
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {MODELS.filter((item) => item.id === bestModel).map((item) => (
                  <Button
                    key={item.id}
                    type="button"
                    size="sm"
                    variant={model === item.id ? "yellow" : "outline"}
                    onClick={() => {
                      setModelPicked(true);
                      setModel(item.id);
                    }}
                  >
                    {item.short}
                  </Button>
                ))}
              </div>
              <p className="mt-3 text-xs text-muted">Other round-1 checkpoints</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {MODELS.filter((item) => item.id !== bestModel).map((item) => (
                  <Button
                    key={item.id}
                    type="button"
                    size="sm"
                    variant={model === item.id ? "yellow" : "outline"}
                    onClick={() => {
                      setModelPicked(true);
                      setModel(item.id);
                    }}
                  >
                    {item.short}
                  </Button>
                ))}
              </div>
            </fieldset>
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          <DecisionCard
            kicker="Round 1 pilot"
            title={`SmolVLM ${modelShort(model)}`}
            action={
              status !== "ready"
                ? undefined
                : !rendered && script !== ""
                  ? undefined
                  : scoredPlacement || script === ""
                    ? trial?.action
                    : undefined
            }
            note={decisionNote({
              status,
              rendered,
              script,
              scoredPlacement,
              defense,
              model,
              trialAction: trial?.action,
              rationale: trial?.rationale,
            })}
            flip={Boolean(flip)}
            gt={scene.gt}
            target={scene.target}
            role={scene.role}
          />
          <div className="rounded-lg border border-line bg-white p-4 md:col-span-2">
            <p className="font-stencil text-xs tracking-widest uppercase">Round 1 pilot, SmolVLM only</p>
            <ul className="mt-3 divide-y divide-line">
              {MODELS.map((item) => {
                const row =
                  status === "ready" && (rendered || script === "")
                    ? trialFor(
                        trials,
                        scene.id,
                        item.id,
                        script && rendered ? "attack" : "clean",
                        script && rendered ? script : "",
                        defense,
                        "truck_rear",
                      )
                    : undefined;
                return (
                  <li key={item.id} className="flex items-center justify-between gap-3 py-2 text-sm">
                    <span>
                      <span className="block">{item.short}</span>
                      <span className="text-xs text-muted">{item.detail}</span>
                    </span>
                    {status !== "ready" ? (
                      <span className="text-muted">pending</span>
                    ) : row ? (
                      <ActionChip action={row.action} />
                    ) : (
                      <span className="text-muted">not run</span>
                    )}
                  </li>
                );
              })}
            </ul>
            {liveMode ? (
              <div className="mt-4">
                <LiveDialog
                  triggerLabel="Send this frame live"
                  imageUrl={imageSrc}
                  canSend={rendered || script === ""}
                  defense={defense}
                />
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

function decisionNote(args: {
  status: string;
  rendered: boolean;
  script: string;
  scoredPlacement: boolean;
  defense: Defense;
  model: string;
  trialAction: string | undefined;
  rationale: string | undefined;
}): string {
  if (args.script !== "" && !args.rendered) {
    return "No model output. Change the size back to 100% and clear custom wording to see a scored trial.";
  }
  if (!args.scoredPlacement && args.script !== "") {
    return "Road placement has a picture and no scored action.";
  }
  if (args.status === "loading") return "Loading the precomputed file.";
  if (args.status === "error") return "The results file did not load. The picture is still the study frame.";
  if (args.status === "pending") return "The summary file is still the placeholder. Actions appear when the run is analyzed.";
  if (!args.trialAction) {
    if (args.defense !== "none" && args.model.includes("hf")) {
      return "Defenses were scored on the llama.cpp f16 and Q4_0 checkpoints, not on the Hugging Face float32 runs.";
    }
    return "No trial in the summary matches this combination.";
  }
  const extra =
    args.defense === "ocr"
      ? " OCR defense showed the model a masked copy. This picture is the unmasked file."
      : args.defense === "prompt"
        ? " Prompt defense used the same pixels and a longer instruction."
        : "";
  return `${args.rationale || "The model did not give a separate reason."}${extra}`;
}

function DecisionCard({
  kicker,
  title,
  action,
  note,
  flip,
  gt,
  target,
  role,
}: {
  kicker: string;
  title: string;
  action: string | undefined;
  note: string;
  flip: boolean;
  gt: string;
  target: string;
  role: string;
}) {
  return (
    <div className="rounded-lg border border-line bg-paper p-4">
      <p className="font-stencil text-xs tracking-widest uppercase">{kicker}</p>
      <h3 className="mt-1 font-display text-2xl">{title}</h3>
      <div className="mt-3">
        {action ? <ActionChip action={action} /> : <ActionChip action={undefined} />}
      </div>
      <p className="mt-3 text-sm leading-relaxed">{note}</p>
      <dl className="mt-4 space-y-1 text-sm text-muted">
        <div className="flex justify-between gap-3">
          <dt>Label</dt>
          <dd>{gt}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt>Attack target</dt>
          <dd>{target}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt>Targeted flip</dt>
          <dd>{flip ? "yes" : action ? "no" : "—"}</dd>
        </div>
        <div className="flex justify-between gap-3">
          <dt>Role</dt>
          <dd>{role === "control" ? "control, excluded from primary ASR" : "primary"}</dd>
        </div>
      </dl>
    </div>
  );
}
