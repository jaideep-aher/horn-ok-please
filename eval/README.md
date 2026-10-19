# Evaluation index

Each directory under `eval/` is one round or one track. The offline rebuild is one command, `make reproduce`. It reruns the analyzers below from the prediction files already in git. It does not load a weight file and it does not call an API. A runner that needs a model or `GEMINI_API_KEY` is a rescore, not what `make reproduce` does.

Weights are not in git. `eval/download_models.sh` fetches the GGUF files named in the README. There is no per-round Make target besides the analyzers inside `make reproduce`.

| Track | Protocol | Offline rebuild |
|---|---|---|
| Round 1 | [`preregistration.md`](preregistration.md) | `make reproduce` runs [`analyze.py`](analyze.py) |
| Round 2 | [`round2/preregistration.md`](round2/preregistration.md) | `make reproduce` runs [`round2/analyze.py`](round2/analyze.py) |
| Round 3 | [`round3/preregistration.md`](round3/preregistration.md) | `make reproduce` runs [`round3/analyze.py`](round3/analyze.py) |
| Dev diagnostic | [`dev/protocol.md`](dev/protocol.md) | `make reproduce` runs [`dev/analyze.py`](dev/analyze.py) |
| Photographs | [`photos/protocol.md`](photos/protocol.md) | `make reproduce` runs [`photos/analyze.py`](photos/analyze.py) |
| XAI | [`xai/protocol.md`](xai/protocol.md) | `make reproduce` runs [`xai/analyze.py`](xai/analyze.py) |
| Gemini, including phase 2 | [`gemini_remote/RUN.md`](gemini_remote/RUN.md), [`gemini_remote/phase2/preregistration.md`](gemini_remote/phase2/preregistration.md) | `make reproduce` runs [`gemini_remote/phase2/analyze_phase2.py`](gemini_remote/phase2/analyze_phase2.py) only |
| US-truck frames | same phase-2 file, block 2 | the same phase-2 analyzer |

## Round 1

There is no `eval/round1/` directory. The pilot lives at the top of `eval/`.

It tests whether painted text changes a four-way driving action (BRAKE, SLOW, CONTINUE, CHANGE_LANE) on twelve drawn scenes, for SmolVLM checkpoints, including an f16 versus Q4 contrast and two defenses. The contract is [`preregistration.md`](preregistration.md). The grid that was actually run is [`run_config.json`](run_config.json).

Scenes are [`stimuli/`](stimuli/). `hornok make-scenes --out eval/stimuli` redraws them. The runner is [`run_benchmark.py`](run_benchmark.py). It needs the local weights. The analyzer is [`analyze.py`](analyze.py). It reads [`results/predictions.jsonl`](results/predictions.jsonl) and writes [`results/summary.json`](results/summary.json). [`results/run_meta.json`](results/run_meta.json) is run metadata. `make reproduce` runs the analyzer. It does not need a model or an API key.

## Round 2

A competence gate on clean frames (agreement at least 0.60, unparsed at most 0.10), then attacks only for models that pass. Four actions, still one frame. Enrolled models are the Qwen2.5-VL 3B, Gemma 3 4B, and InternVL2.5 1B checkpoints named in the protocol. The contract is [`round2/preregistration.md`](round2/preregistration.md).

[`round2/build_stimuli.py`](round2/build_stimuli.py) draws frames and can download Commons photographs. Those downloads are not what `make reproduce` does. The runner is [`round2/run_benchmark.py`](round2/run_benchmark.py). It needs the local GGUF weights (llama.cpp). The analyzer is [`round2/analyze.py`](round2/analyze.py). It reads [`round2/results/predictions.jsonl`](round2/results/predictions.jsonl) and [`round2/results/gate.json`](round2/results/gate.json), and writes [`round2/results/summary.json`](round2/results/summary.json). `make reproduce` runs that analyzer with no model and no API key. The runner is not a Make target.

## Round 3

STOP versus GO on 20 hazard frames and 20 clear frames. Attacks and the two defenses are scored only for a model that passes the gate in [`round3/preregistration.md`](round3/preregistration.md). The four open checkpoints are Qwen2.5-VL 3B and Gemma 3 4B at Q8_0 and Q4_K_M.

[`round3/build_stimuli.py`](round3/build_stimuli.py) copies inherited frames and draws the new ones. It does not call a model. Five gate frames (`photo_cargo_a`, `photo_cargo_b`, `photo_delhi`, `photo_dharwad`, `photo_wind`) are withheld Commons photographs, so a full image rescore cannot be done from a clone. The runner is [`round3/run_benchmark.py`](round3/run_benchmark.py). The local backend needs the GGUF weights. `--backend gemini` needs `GEMINI_API_KEY` and sends no request without it. The stored open-model rows are the local run. The Gemini rows are the separate track under `gemini_remote/`.

The analyzer is [`round3/analyze.py`](round3/analyze.py). It reads [`round3/results/predictions.jsonl`](round3/results/predictions.jsonl) and [`round3/results/gate.json`](round3/results/gate.json), and writes [`round3/results/summary.json`](round3/results/summary.json). [`round3/results/smoke.jsonl`](round3/results/smoke.jsonl) is the enrollment smoke, not a score. `make reproduce` runs the analyzer with no model and no API key.

## Dev

A prompt diagnostic on scenes that are not the round-3 test set. It asks whether the constant-STOP pattern comes from the wording or from the picture. The contract is [`dev/protocol.md`](dev/protocol.md). It is not a round 4.

[`dev/build_stimuli.py`](dev/build_stimuli.py) draws the frames and does not call a model. The runner is [`dev/run_diagnostic.py`](dev/run_diagnostic.py). It needs the local weights. The analyzer is [`dev/analyze.py`](dev/analyze.py). It reads [`dev/results/predictions.jsonl`](dev/results/predictions.jsonl) and writes [`dev/results/summary.json`](dev/results/summary.json). `make reproduce` runs the analyzer with no model and no API key.

## Photographs

99 Wikimedia Commons frames (53 India, 46 Pakistan, as [`photos/protocol.md`](photos/protocol.md) states). Driving trials are rear driver's-eye views, all labeled STOP, so GO recall is undefined. Literacy is front and side views. The transcription is model-assisted except `IN_001` and `IN_013`, the two frames that protocol marks verified. Credits are [`photos/CREDITS.md`](photos/CREDITS.md).

[`photos/fetch_sources.py`](photos/fetch_sources.py) downloads the frames and needs the network. [`photos/build_stimuli.py`](photos/build_stimuli.py) builds derivatives and does not call a driving model. Unblurred originals are gitignored. The runner is [`photos/run_photos.py`](photos/run_photos.py). Driving and paint jobs use Qwen2.5-VL 3B Q8. Literacy also runs Gemma 3 4B Q8. Both weight files have to be local. The analyzer is [`photos/analyze.py`](photos/analyze.py). It reads [`photos/results/predictions.jsonl`](photos/results/predictions.jsonl) and writes [`photos/results/summary.json`](photos/results/summary.json). `make reproduce` runs it with no model and no API key. `--publish` also writes `web/public/data/photos.json`; `make reproduce` does not pass that flag.

The Gemini photograph rows are a different file: [`gemini_remote/results/photos_summary.json`](gemini_remote/results/photos_summary.json).

## XAI

Six drawn scenes. The question is whether removing and inpainting the tailgate paint restores the clean decision, plus a 3 by 3 occlusion grid. The contract is [`xai/protocol.md`](xai/protocol.md). The painted model in the stored file is `qwen25vl-3b-q8`.

[`xai/build_stimuli.py`](xai/build_stimuli.py) draws the scenes and the tailgate edits. It does not call a model. The runner is [`xai/run_xai.py`](xai/run_xai.py). It needs the local weights. [`xai/whitebox.py`](xai/whitebox.py) writes [`xai/results/whitebox.json`](xai/results/whitebox.json) with `status` `not_run` and does not draw an attention map. The analyzer is [`xai/analyze.py`](xai/analyze.py). It reads [`xai/results/predictions.jsonl`](xai/results/predictions.jsonl) and `whitebox.json`, and writes [`xai/results/summary.json`](xai/results/summary.json). [`xai/results/gaze_cohort.json`](xai/results/gaze_cohort.json) is the occlusion cohort list. `make reproduce` runs the analyzer with no model and no API key. `--publish` also writes site files; `make reproduce` does not pass that flag.

## Gemini remote, including phase 2

This is the cloud reference. It is not an edge-model round.

The first bundle follows the round-3 gate, then attacks, defenses, the six-scene explanation, and the photograph track, on the resolved id `gemini-3.8-flash`. Flash-Lite is a separate gate attempt. How to run it is [`gemini_remote/RUN.md`](gemini_remote/RUN.md). The protocol is the Gemini section of [`round3/preregistration.md`](round3/preregistration.md), plus [`xai/protocol.md`](xai/protocol.md) for the explanation stage and [`photos/protocol.md`](photos/protocol.md) for the photograph stage.

The runner is [`gemini_remote/run_gemini.py`](gemini_remote/run_gemini.py). It needs `GEMINI_API_KEY`. Without the key it writes a status of `not_called` and sends nothing. Its default output directory is `gemini-out/`, not the committed folder. The committed copies are:

| File | What it is |
|---|---|
| [`gemini_remote/results/predictions.jsonl`](gemini_remote/results/predictions.jsonl) | Gate, attacks, defenses |
| [`gemini_remote/results/summary.json`](gemini_remote/results/summary.json) | Gate, tests, `lite_audit`, `thinking_audit` |
| [`gemini_remote/results/explain.jsonl`](gemini_remote/results/explain.jsonl) | Six-scene explanation rows |
| [`gemini_remote/results/explain_summary.json`](gemini_remote/results/explain_summary.json) | Explanation summary |
| [`gemini_remote/results/photos.jsonl`](gemini_remote/results/photos.jsonl) | Photograph rows |
| [`gemini_remote/results/photos_summary.json`](gemini_remote/results/photos_summary.json) | Photograph summary |
| [`gemini_remote/results/models.json`](gemini_remote/results/models.json) | Model list from the run |
| `gemini_remote/results/status*.json` | Stage status |

`make reproduce` does not rewrite these files. Rebuilding them means running the API again.

Phase 2 was locked in [`gemini_remote/phase2/preregistration.md`](gemini_remote/phase2/preregistration.md) and then run as locked. Block 1 is a G2 replication at seed 2. Block 3 is defenses on G2. Block 4 is G1 repeats at seeds 3, 4, and 5. The runner for those three is [`gemini_remote/phase2/run_phase2.py`](gemini_remote/phase2/run_phase2.py). It needs `GEMINI_API_KEY`. Its default output directory is [`gemini_remote/phase2/results/`](gemini_remote/phase2/results/), which already holds the stored JSONL. The preregistration says not to call the API again from this checkout.

The analyzer is [`gemini_remote/phase2/analyze_phase2.py`](gemini_remote/phase2/analyze_phase2.py). It reads the phase-2 JSONL and the stored round-3 predictions, and writes [`gemini_remote/phase2/results/summary.json`](gemini_remote/phase2/results/summary.json). `make reproduce` runs it. It does not need a model or an API key. Other files in that results directory: `b1_g2_replication_seed2.jsonl`, `b2_us_truck_control.jsonl`, `b3_defenses_on_g2.jsonl`, `b4_g1_repeat_seed3.jsonl`, `b4_g1_repeat_seed4.jsonl`, `b4_g1_repeat_seed5.jsonl`, `call_counts.json`, `us_call_counts.json`, `status.json`, `us_status.json`.

## US trucks

Block 2 of phase 2. Drawn US dry-van rears, English G1 against each frame's own clean answer. B1 is drawn and is not in the 40 scored calls. The frames are [`gemini_remote/phase2/us_trucks/`](gemini_remote/phase2/us_trucks/), pinned by [`SHA256SUMS`](gemini_remote/phase2/us_trucks/SHA256SUMS). The builder is [`gemini_remote/phase2/build_us_trucks.py`](gemini_remote/phase2/build_us_trucks.py). It draws. It does not call a model or an API.

The runner is [`gemini_remote/phase2/run_us.py`](gemini_remote/phase2/run_us.py). It needs `GEMINI_API_KEY` and `--us-stim` (or `PHASE2_US_STIM`) pointing at the drawing directory. The stored rows are [`gemini_remote/phase2/results/b2_us_truck_control.jsonl`](gemini_remote/phase2/results/b2_us_truck_control.jsonl). The summary block is inside [`gemini_remote/phase2/results/summary.json`](gemini_remote/phase2/results/summary.json), rebuilt by the phase-2 analyzer under `make reproduce`. That rebuild does not need a model or an API key.

## Also under eval/

[`smoke.py`](smoke.py) times one forward pass on an image that is not in the scored twelve. It needs a local model. It writes [`smoke/timing.json`](smoke/timing.json). [`smoke/recheck.json`](smoke/recheck.json) is a stored recheck. `make reproduce` does not run this script.
