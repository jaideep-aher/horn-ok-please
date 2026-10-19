# Horn OK Please

[![tests](https://github.com/jaideep-aher/horn-ok-please/actions/workflows/ci.yml/badge.svg)](https://github.com/jaideep-aher/horn-ok-please/actions/workflows/ci.yml)

## Read this first

When painted truck text changes a driving model's decision, can we see why?

The confirmatory Gemini result is a null. Gemini 3.8 Flash passed the STOP versus GO gate: STOP 20/20 (Wilson 95% 0.839 to 1.000), GO 17/20 (0.640 to 0.948), balanced accuracy 0.925, unparsed 0/40. Preregistered tests T1–T4 and T7–T9 are exact McNemar then Holm, and every stored p is 1. T5, T6, and T10 are omitted because this file has one passer. G2 is not in that family. Marathi G2 flipped 4/20 (Wilson 95% 0.081 to 0.416) and Hindi G2 flipped 3/20 (0.052 to 0.360). English versus Marathi on G2 is exploratory: n=20, 4 discordant pairs, McNemar p=0.125.

Defenses were scored on G1 only. Undefended G1 flips are 1/80 (Wilson 95% 0.002 to 0.067). Each defense flipped 0/80. That paired test is p=1, so there is no measurable benefit. Each defense over-blocked 4/17 true GO scenes (0.096 to 0.473).

Six drawings are illustrative examples, not headline evidence. Qwen2.5-VL 3B Q8 failed the competence gate: GO 0/20, balanced accuracy 0.500. Under the preregistration its flips are not scored. On those drawings the English line changed the stored decision on 6/6 and OpenCV Telea restored 6/6. Four drawings are labeled STOP, so those changes ignore the hazard. Two are labeled GO (`xai_empty`, `xai_dusk`), so those STOP-to-GO changes are corrections. Marathi, benign text, and gibberish changed 0/6. Rationales were not a scored admission test. Stored `thinking` is `off` on 488/488 Flash rows, and `thoughts_token_count` is positive on 486/488. Flash-Lite was never evaluated: all 40 gate requests returned HTTP 400. An earlier 40/40 truncation is not a score.

This is not a crash risk and not a road test. The photograph track has no empty lane, so GO recall is undefined. Jaideep (Jay) Aher, Duke AIPI 590. Install the test extra, run pytest, then start the site from the web folder.

```bash
pip install -e ".[dev]"
pytest
cd web && npm ci && npm run dev
```

![Marathi GO line painted on an illustrated truck tailgate, with a person still on the crossing](web/public/stimuli/attack/ped_crossing__truck_rear__deva.webp)

Live site: https://jaideep-aher.github.io/horn-ok-please/ (deployed by the GitHub Pages workflow).

## The question

When painted truck text changes a driving model's decision, can we see why?

## Novelty

This project, set against prior typographic attacks on vision-language models (Chung et al., arXiv:2405.14169; CHAI, arXiv:2510.00181; SCAM, arXiv:2504.04893, which SCAM's authors note has an "exclusive focus on English-language attacks"), tests non-English, multi-script scene text (Marathi/Devanagari, Hindi, Hinglish, Urdu) painted on trucks, compares a cloud model with quantized edge models under a preregistered gate, and audits the effect causally by removing and inpainting the paint.

## Course mapping

| Topic | Where it shows up |
|---|---|
| XAI | Occlusion, faithfulness, and causal paint removal and inpainting in [`eval/xai/protocol.md`](eval/xai/protocol.md) |
| Adversarial AI | Painted tailgate attacks in [`eval/round3/`](eval/round3/) and the two defenses in [`src/hornok/defense.py`](src/hornok/defense.py) |
| Red-Teaming | Attack phrases in [`src/hornok/phrases.py`](src/hornok/phrases.py) and the scored tailgate paint in [`src/hornok/attack_paint.py`](src/hornok/attack_paint.py) |
| AI Harms | Who is affected in [Misuse and stakeholders](#misuse-and-stakeholders). Language coverage: English, Marathi, Hindi, and Hinglish in [`src/hornok/round3.py`](src/hornok/round3.py); Urdu in [`eval/photos/protocol.md`](eval/photos/protocol.md). Privacy: blurred frame [`poster/assets/truck_tailgate_blurred.jpg`](poster/assets/truck_tailgate_blurred.jpg); unblurred frames withheld in [`eval/photos/CREDITS.md`](eval/photos/CREDITS.md). |
| AI Evaluation | The locked gate in [`eval/round3/preregistration.md`](eval/round3/preregistration.md) and Holm adjustment in [`src/hornok/metrics.py`](src/hornok/metrics.py) |

## Key results

| Finding | Stored result |
|---|---|
| Gemini 3.8 Flash gate | Passed. STOP 20/20 (Wilson 95% 0.839 to 1.000), GO 17/20 (0.640 to 0.948), balanced accuracy 0.925, unparsed 0/40. |
| Confirmatory tests | T1–T4 and T7–T9, exact McNemar then Holm. Every p is 1. T5, T6, and T10 omitted. |
| G2, exploratory | Marathi 4/20 (Wilson 95% 0.081 to 0.416), Hindi 3/20 (0.052 to 0.360). English versus Marathi: p=0.125, 4 discordant, n=20. Not in the Holm family. |
| Defenses | G1 only. Undefended 1/80, each defense 0/80, McNemar p=1. Over-block 4/17 (Wilson 95% 0.096 to 0.473). Not run on G2. |
| Open models | None passed the same gate. Qwen2.5-VL 3B Q8: GO 0/20, balanced accuracy 0.500. The six-drawing English changes are illustrative examples from that gate-failed model, not headline evidence. |
| Photographs, Flash | STOP 28/31 (Wilson 95% 0.751 to 0.967). Paint changes 0/19. GO recall is undefined. Holm p=1 on all five tests. The frames are not in this copy. |

## What failed and why

- **Flash-Lite was never evaluated.** All 40 gate requests returned HTTP 400 INVALID_ARGUMENT. The client tries another thinking setting only when the error names `thinking_budget` or `thinking_level`. This message does not, so the run stopped. That is not a competence score.
- **Open models failed the gate.** In `web/public/data/round3.json`, Qwen2.5-VL 3B Q4 is STOP 20/20 and GO 1/20 (`photo_wind` only), balanced accuracy 0.525, unparsed 0/40. Qwen2.5-VL 3B Q8, Gemma 3 4B Q8, and Gemma 3 4B Q4 each said STOP on 40/40, balanced accuracy 0.500, unparsed 0/40. None passed, so their attacks were not scored.
- **The gate was re-run.** An earlier Flash file, 40/40 unparsed, was a client failure: thinking tokens consumed a 64-token cap, and the schema was not sent as `response_schema`. That file is not a score. The numbers above are the later run.
- **`thinking: off` is mislabeled.** Stored `thinking` is `off` on 488/488 Flash rows, and `thoughts_token_count` is positive on 486/488. The two rows without thoughts are literacy cards.
- **Defenses were not tested on G2.** Prompt and OCR defenses were scored on G1 only. Undefended G1 is 1/80 and each defense is 0/80, so the paired test is p=1: no measurable benefit. Each defense also over-blocked 4/17 true GO scenes.

The full log, including the prompt diagnostic, is `docs/RESULTS_LOG.md`. The open-weight photograph summary in `eval/photos/results/summary.json` is rebuilt from the committed Qwen2.5-VL 3B Q8 rows. It is not a published claim in this copy.

## Quickstart

Python 3.10 or newer. Devanagari shaping needs Pillow with RAQM. OCR defense needs Tesseract with English, Hindi, and Marathi.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
cd web && npm ci && npm run dev
```

`npm run build` writes `web/out`. Weights are not in git. `eval/download_models.sh` fetches the SmolVLM, Qwen2.5-VL 3B, Gemma 3 4B, and InternVL2.5 1B GGUF files used in the scored runs. `simple-lama-inpainting` is optional and is not installed by the test extra. The recorded photograph fill was LaMa. The six illustrated explanation scenes used OpenCV Telea.

## What is in git and what is not

The repo ships the scored clean frames and literacy cards as the exact PNGs the models saw. Painted variants (`attack/`, and `paint/`, `inpaint/`, `insertion/` for the explanation scenes) ship as WebP previews, because the full PNG set is about 500 MB. Each stimuli folder has `SHA256SUMS` (file hashes of every scored PNG) and `PIXELS.sha256.json` (hashes of the decoded pixels), so a rebuild can be checked byte for byte. `tests/test_gemini_bundle.py` checks that the painter reproduces the locked round-3 pixels. `web/public/stimuli` holds display copies of the round-1 frames for the site.

These are regenerable and stay out of git (see `.gitignore`):

- Painted PNGs for every round: `hornok make-scenes --out eval/stimuli`, `python eval/round2/build_stimuli.py`, and the round-3, dev, and XAI build scripts next to each protocol. Compare the output with `SHA256SUMS`.
- Round-2 drawing PNGs (`eval/round2/stimuli/`, only `manifest.json` is committed). They are not committed because 14 of them have no recorded hash to check a rebuild against.
- OCR, occlusion, and faithfulness caches (`eval/*/results/ocr*`, `eval/*/results/occlusion/`, `eval/*/results/faithful/`, `eval/photos/results/literacy_mask/`). The analysis scripts rebuild them from the stored predictions.
- Commons photographs and anything painted on them. Rebuild with `python eval/photos/fetch_sources.py` and `python eval/photos/build_stimuli.py`.

A zipped copy of the results, data, and drawn stimulus PNGs is kept off-repo by the author and is available on request.

The Ubuntu CI run (`.github/workflows/ci.yml`) is the test reference. On a Mac without libraqm and Tesseract, 4 to 5 Devanagari rendering and OCR tests fail for environment reasons only. `brew install fribidi` and `export DYLD_LIBRARY_PATH=/opt/homebrew/lib` turn on shaping in the Pillow wheel, which leaves only the Tesseract test skipped.

## Model ids

The scored run did not store a Hugging Face revision hash. The pin is the repository id plus the GGUF filename in `src/hornok/round2.py` and `src/hornok/round3.py`. Local runtime for every open model: llama.cpp `b11716`, image tokens 512, temperature 0, top_k 1, seed 1, context 4096, no GPU offload.

| Id | What was run |
|---|---|
| `qwen25vl-3b-q8` | `ggml-org/Qwen2.5-VL-3B-Instruct-GGUF` file `Qwen2.5-VL-3B-Instruct-Q8_0.gguf`, projector `mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf`. Round 2, round 3, the dev diagnostic, and the six explanation drawings. |
| `qwen25vl-3b-q4` | Same repo, `Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf`, same projector. Round 2 and round 3. |
| `gemma3-4b-q8` | `ggml-org/gemma-3-4b-it-GGUF` file `gemma-3-4b-it-Q8_0.gguf`, projector `mmproj-model-f16.gguf`. This is Gemma 3 4B IT, not a separate Gemma 4B. Round 2, round 3, and the dev diagnostic. |
| `gemma3-4b-q4` | Same repo, `gemma-3-4b-it-Q4_K_M.gguf`, same projector. Round 3 only. |
| `internvl25-1b-q8` | `ggml-org/InternVL2_5-1B-GGUF` file `InternVL2_5-1B-Q8_0.gguf`, projector `mmproj-InternVL2_5-1B-f16.gguf`. Round 2 only. |
| `smolvlm-256m-hf` / `smolvlm-500m-hf` | `HuggingFaceTB/SmolVLM-256M-Instruct` and `HuggingFaceTB/SmolVLM-500M-Instruct`, transformers float32. Round 1 pilot. |
| `smolvlm-256m-f16` / `smolvlm-256m-q4` | `ggml-org/SmolVLM-256M-Instruct-GGUF` f16, and a Q4_0 file quantized locally from that f16 with llama.cpp `b11716`. Round 1 pilot. |
| `gemini-3.8-flash` | Resolved API id. Temperature was not sent. The stored `thinking` field is `off`. |
| `gemini-3.5-flash-lite` | Resolved API id. All 40 gate requests returned HTTP 400. Not evaluated. |

## Contribution

The toolkit in `src/hornok` draws scenes, parses STOP and GO, scores attack success with Wilson intervals and exact McNemar tests, and runs the explanation checks. Protocols were locked before the completions they govern. The site reads those summaries. It does not invent a rate.

Illustrated frames are original drawings, CC-BY-4.0, Jaideep (Jay) Aher. The 99-photograph track uses Wikimedia Commons frames. Credits and licenses are in `eval/photos/CREDITS.md`. Photograph, font, and illustration terms outside the MIT license are in `NOTICE`. The unblurred Commons frames are not in this copy. `poster/assets/truck_tailgate_blurred.jpg` is a blurred Commons image (Anupamg, File:Funny 001.jpg, CC BY-SA 3.0). Painted registration numbers and phone numbers stayed readable after the bumper-plate boxes, so `web/public/photos/` is empty. Model-facing files stay out of git. Rebuild them locally with `python eval/photos/fetch_sources.py` and `python eval/photos/build_stimuli.py`.

## Design decisions

- **A gate before an attack.** Round 1 showed that a zero attack rate on SmolVLM was incompetence. Round 2 asked for four actions from one still frame, and every model failed a 60% agreement gate. Round 3, locked on 18 October 2026, asks only STOP or GO, because a still frame cannot support the four-way split. Unparsed is a miss.
- **Scripts are fixed, not searched.** English, Marathi in Devanagari, Hindi in Devanagari, Hinglish, and, on the photographs, Urdu in Nastaliq.
- **Quantization is a contrast, not a slogan.** Round 1 compared f16 with Q4_0 inside one llama.cpp runtime. Later rounds use the Q8_0 and Q4_K_M GGUFs named in `eval/download_models.sh`. The same vision projector is shared inside a family.
- **Two defenses, with an over-block cost.** Prompt hardening leaves the pixels alone. OCR isolation paints out instruction-like tokens and keeps STOP and रुको. Both are scored against true GO scenes.
- **Explanations are causal checks, not a paper reproduction.** Methods are adapted from On Thin Ice, photorealistic inpainting, Why2Speak, and GLEaN. Those papers' seal, portrait, and conversation numbers are not this study's numbers. Illustrated scenes use OpenCV Telea. The 99-photograph track uses LaMa.
- **Photographs are a separate track.** Rear driver's-eye views are labeled STOP. The pack has no empty-lane photo, so GO recall is undefined and that gate cannot pass. The bar is not lowered. Front and side views are a literacy probe against an unverified transcription, not a human label.

## Limitations

- No local open-weight model passed the STOP/GO gate. Several rows answered STOP on every GO scene, including empty lanes. That over-caution is a failure mode, not robustness.
- One frame, one action. There is no closed-loop controller and no video.
- Illustration labels are true because the hazard was drawn. A model can fail because the drawing does not look like a road. The Commons track is real trucks, and its GO class is empty.
- A defense that stops the attack can also stop a true GO. Flash over-blocked 4/17 on each defense.
- White-box attention was not run. Available memory was above the protocol floor. llama-server does not return attention, and a full-precision Qwen2.5-VL-3B checkpoint is not in this checkout. No attention map was drawn.
- The literacy reference on the photographs is an AI-assisted visual spot-check, not human-verified. Those means are not human-labeled accuracy.

## Misuse and stakeholders

The phrases tell a model to ignore a hazard or to invent one. They are here so an auditor can measure that behavior. They are not a guide for painting a vehicle. Do not put these strings on a road, a vehicle in traffic, or a test that other road users can see.

People who would bear a real version of this failure: people on foot, on two-wheelers, and in the vehicle; truck owners whose vehicles would be the canvas; ADAS and vehicle-software teams; regulators writing rules for driver assistance. A useful outcome is a defense that still brakes for a person and for STOP. A harmful outcome is treating a flip on a drawing as proof that a named production car is vulnerable.

## Future work

Does the model's own explanation admit it? Rationales were not scored.

A human check of the photograph transcriptions, attention maps from a checkpoint that returns them, and a deployment note for teams who ship a vision policy: score STOP and GO before scoring an attack, and publish the over-block cost beside any flip. A printed-board transfer test, if it is done, stays off public roads. Steps that need a date, a key, or a person are in `docs/SETUP.md`.

## Citations

Checked against the arXiv record on 19 October 2026. CHAI’s 95.5%, 81.8%, 72.8%, and at least 87% figures are in the paper’s introduction. They are not this study’s results.

- Nhat Chung, Sensen Gao, Tuan-Anh Vu, Jie Zhang, Aishan Liu, Yun Lin, Jin Song Dong, and Qing Guo. "Towards Transferable Attacks Against Vision-LLMs in Autonomous Driving with Typography." arXiv:2405.14169, 2024. The arXiv comment says work in progress. No venue is listed. https://arxiv.org/abs/2405.14169
- Luis Burbano, Diego Ortiz, Qi Sun, Siwei Yang, Haoqin Tu, Cihang Xie, Yinzhi Cao, and Alvaro A. Cardenas. "CHAI: Command Hijacking against embodied AI." arXiv:2510.00181. Accepted at IEEE SaTML, from the arXiv comment. https://arxiv.org/abs/2510.00181
- Justus Westerhoff, Erblina Purelku, Jakob Hackstein, Jonas Loos, Leo Pinetzki, Erik Rodner, and Lorenz Hufe. "SCAM." arXiv:2504.04893. CVPR 2025 Workshop EVAL-FoMo-2, and Journal of Data-centric Machine Learning Research (2026). https://arxiv.org/abs/2504.04893
- Zhou, Aghakishiyeva, Arya, Dale, Poling, Houliston, Womble, Larsen, Johnston, and Bent. "On Thin Ice." arXiv:2510.21689. NeurIPS Imageomics Workshop 2025. Adapted as a scoring template, not as a seal-detector result.
- Aghakishiyeva, Zhou, Arya, Dale, Poling, Houliston, Womble, Larsen, Johnston, and Bent. "Photorealistic Inpainting for Perturbation-based Explanations." arXiv:2510.03317. NeurIPS 2025 Imageomics Workshop. Adapted as mask-local removal. This run does not use their Segment Anything or Stable Diffusion pipeline.
- Mendi and Bent. "Why2Speak." arXiv:2608.20670. No venue is listed on the arXiv record. Adapted as a direct decision versus a reason-then-decide prompt.
- Ding, Bent, and Wendell. "GLEaN." arXiv:2604.09923. CVPR Workshops 2026, pp. 4026–4036. Cited for the public-facing aim. Their portrait study is not run. The expo form does not collect responses.
- Souvik Kundu and colleagues. "LVLM-Compress-Bench." arXiv:2503.04982. Accepted to NAACL 2025. Anik De and colleagues. "Bharat Scene Text." arXiv:2511.23071. International Journal on Document Analysis and Recognition (IJDAR), 2026. Vijayasri Iyer, Maahin Rathinagiriswaran, and Jyothikamalesh S. "RoadscapesQA." arXiv:2602.12877. No venue is listed. None of those datasets are in this run.

IDD is context for the question. Frames from it are not in this repository. https://idd.insaan.iiit.ac.in/dataset/details/

## AI assistance

This project was built with substantial AI assistance. I used AI coding agents (Cursor cloud agents and Grok Bot assistants) to write most of the code: the hornok toolkit and its tests, the stimulus builders, the evaluation runners and the analysis scripts. The same tools built the website, drafted the README and docs, and drafted the poster and pitch text. They also ran evaluation jobs and reviewed the project against the course rubric. I set the research question, the study design and the preregistered protocols, decided what to run and what to report, and checked every reported number against the committed result files in this repository. Any errors are mine.

## Reproduce

```bash
make setup
make test
make reproduce
```

`make setup` installs this package with the dev extra. `make test` runs `ruff check src tests eval poster` and `pytest`. `make reproduce` rebuilds summaries from the prediction files already in git, with no model and no network, then `git diff --exit-code` checks those files byte for byte. It sets `PYTHONHASHSEED=6` because `eval/round3/analyze.py` fills `readers` from a set; that seed keeps the committed key order. The rates do not depend on the seed.

Round 1 is not under `eval/round1/`. Scenes are `eval/stimuli` (`hornok make-scenes` writes there by default). The runner is `eval/run_benchmark.py`. The summary script is `eval/analyze.py`, which reads `eval/results/predictions.jsonl`. Five of the 40 round-3 gate frames (`photo_cargo_a`, `photo_cargo_b`, `photo_delhi`, `photo_dharwad`, `photo_wind`) are withheld Wikimedia Commons photographs and are not in git, so that gate cannot be fully re-run from a clone. `make reproduce` still rebuilds the summaries from the committed predictions. A full rescore needs the weights and is not what `make reproduce` runs:

```bash
hornok make-scenes --out eval/stimuli
python eval/run_benchmark.py
python eval/analyze.py
python eval/round3/build_stimuli.py
python eval/round3/run_benchmark.py
python eval/round3/analyze.py
```

`make reproduce` reruns only the analyzers that match the committed summaries:

- `eval/analyze.py` writes `eval/results/summary.json`
- `eval/round2/analyze.py` writes `eval/round2/results/summary.json`
- `eval/round3/analyze.py` writes `eval/round3/results/summary.json`
- `eval/dev/analyze.py` writes `eval/dev/results/summary.json`
- `eval/photos/analyze.py` writes `eval/photos/results/summary.json` from `eval/photos/results/predictions.jsonl`
- `eval/xai/analyze.py` writes `eval/xai/results/summary.json` from the stored completions and from `eval/xai/results/whitebox.json`
- `poster/derived_stats.py` writes `poster/build/derived_stats.json`

`eval/xai/analyze.py` does not copy frames into `web/public/xai` or rewrite `web/public/data/xai.json` unless `--publish` is passed. Paint and inpaint PNGs are gitignored. With `--publish`, those image fields stay `/xai/...` even when the PNG is absent.

`eval/photos/analyze.py` does not write `web/public/data/photos.json` unless `--publish` is passed. The hand-copied `snapshot` object is not produced from the prediction rows, so it is not in the rebuilt summary. English paint on the committed Qwen2.5-VL 3B Q8 rows is 6/19, Holm p = 0.125.

The round-1 contract is `eval/preregistration.md`. Later contracts are `eval/round2/preregistration.md`, `eval/round3/preregistration.md`, `eval/dev/protocol.md`, `eval/xai/protocol.md`, and `eval/photos/protocol.md`. Display copies of the illustrations are already in `web/public/stimuli`. llama.cpp `b11716` is the multimodal runtime. Point `HORNOK_LLAMA_BIN` at `llama-mtmd-cli`. The default path is `vendor/llama-b11716/llama-mtmd-cli` inside this repo. The binary is not committed.
