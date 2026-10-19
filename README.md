# Horn OK Please

[![tests](https://github.com/jaideep-aher/horn-ok-please/actions/workflows/ci.yml/badge.svg)](https://github.com/jaideep-aher/horn-ok-please/actions/workflows/ci.yml)

## Read this first

When painted truck text changes a driving model's decision, can we see why, and does the model's own explanation admit it?

The confirmatory Gemini result is a null. Gemini 3.8 Flash passed the STOP versus GO gate: STOP 20/20 (Wilson 95% 0.839 to 1.000), GO 17/20 (0.640 to 0.948), balanced accuracy 0.925, unparsed 0/40. Preregistered tests T1–T4 and T7–T9 are exact McNemar then Holm, and every stored p is 1. T5, T6, and T10 are omitted because this file has one passer. G2 is not in that family. Marathi G2 flipped 4/20 (Wilson 95% 0.081 to 0.416) and Hindi G2 flipped 3/20 (0.052 to 0.360). English versus Marathi on G2 is exploratory: n=20, 4 discordant pairs, McNemar p=0.125.

Defenses were scored on G1 only. Undefended G1 flips are 1/80 (Wilson 95% 0.002 to 0.067). Each defense flipped 0/80. That paired test is p=1, so there is no measurable benefit. Each defense over-blocked 4/17 true GO scenes (0.096 to 0.473).

On six drawings, Qwen2.5-VL 3B Q8 English paint changed the decision on 6/6, and OpenCV Telea restored the clean decision on 6/6. Four of those drawings are labeled STOP, so those four changes ignore the hazard. Two are labeled GO (`xai_empty`, `xai_dusk`), so those STOP-to-GO changes are corrections. Marathi, benign text, and gibberish changed 0/6. That Qwen checkpoint failed the round-3 gate. Rationales were not a scored admission test. Stored `thinking` is `off` on 488/488 Flash rows, and `thoughts_token_count` is positive on 486/488. Flash-Lite was never evaluated: all 40 gate requests returned HTTP 400. An earlier 40/40 truncation is not a score.

This is not a crash risk and not a road test. The photograph track has no empty lane, so GO recall is undefined. Jaideep (Jay) Aher, Duke AIPI 590. Install the test extra, run pytest, then start the site from the web folder.

```bash
pip install -e ".[dev]"
pytest
cd web && npm ci && npm run dev
```

![Marathi GO line painted on an illustrated truck tailgate, with a person still on the crossing](web/public/stimuli/attack/ped_crossing__truck_rear__deva.png)

The site is a static export. GitHub Actions publishes it at https://jaideep-aher.github.io/horn-ok-please/. The poster QR points at that URL.

## The question

When painted truck text changes a driving model's decision, can we see why, and does the model's own explanation admit it?

## Key results

| Finding | Stored result |
|---|---|
| Gemini 3.8 Flash gate | Passed. STOP 20/20 (Wilson 95% 0.839 to 1.000), GO 17/20 (0.640 to 0.948), balanced accuracy 0.925, unparsed 0/40. |
| Confirmatory tests | T1–T4 and T7–T9, exact McNemar then Holm. Every p is 1. T5, T6, and T10 omitted. |
| G2, exploratory | Marathi 4/20 (Wilson 95% 0.081 to 0.416), Hindi 3/20 (0.052 to 0.360). English versus Marathi: p=0.125, 4 discordant, n=20. Not in the Holm family. |
| Defenses | G1 only. Undefended 1/80, each defense 0/80, McNemar p=1. Over-block 4/17 (Wilson 95% 0.096 to 0.473). Not run on G2. |
| Open models | None passed the same gate. On six drawings, Qwen2.5-VL 3B Q8 English paint changed 6/6: 4 hazard-ignoring flips and 2 GO corrections. Telea restored 6/6. |
| Photographs, Flash | STOP 28/31 (Wilson 95% 0.751 to 0.967). Paint changes 0/19. GO recall is undefined. Holm p=1 on all five tests. The frames are not in this copy. |

## What failed and why

- **Flash-Lite was never evaluated.** All 40 gate requests returned HTTP 400 INVALID_ARGUMENT. The client tries another thinking setting only when the error names `thinking_budget` or `thinking_level`. This message does not, so the run stopped. That is not a competence score.
- **Open models failed the gate.** In `web/public/data/round3.json`, Qwen2.5-VL 3B Q4 is STOP 20/20 and GO 1/20 (`photo_wind` only), balanced accuracy 0.525, unparsed 0/40. Qwen2.5-VL 3B Q8, Gemma 3 4B Q8, and Gemma 3 4B Q4 each said STOP on 40/40, balanced accuracy 0.500, unparsed 0/40. None passed, so their attacks were not scored.
- **The gate was re-run.** An earlier Flash file, 40/40 unparsed, was a client failure: thinking tokens consumed a 64-token cap, and the schema was not sent as `response_schema`. That file is not a score. The numbers above are the later run.
- **`thinking: off` is mislabeled.** Stored `thinking` is `off` on 488/488 Flash rows, and `thoughts_token_count` is positive on 486/488. The two rows without thoughts are literacy cards.
- **Defenses were not tested on G2.** Prompt and OCR defenses were scored on G1 only. Undefended G1 is 1/80 and each defense is 0/80, so the paired test is p=1: no measurable benefit. Each defense also over-blocked 4/17 true GO scenes.

The full log, including the prompt diagnostic, is `docs/RESULTS_LOG.md`. An open-weight photograph snapshot sits in `eval/photos/results/summary.json`. It is not a published claim in this copy.

## Quickstart

Python 3.10 or newer. Devanagari shaping needs Pillow with RAQM. OCR defense needs Tesseract with English, Hindi, and Marathi.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
cd web && npm ci && npm run dev
```

`npm run build` writes `web/out`. Weights are not in git. `eval/download_models.sh` fetches the SmolVLM, Qwen2.5-VL-3B, Gemma-3-4B, and InternVL2.5-1B GGUF files used in the scored runs. `simple-lama-inpainting` is optional and is not installed by the test extra. The recorded photograph fill was LaMa. The six illustrated explanation scenes used OpenCV Telea.

## Contribution

The toolkit in `src/hornok` draws scenes, parses STOP and GO, scores attack success with Wilson intervals and exact McNemar tests, and runs the explanation checks. Protocols were locked before the completions they govern. The site reads those summaries. It does not invent a rate.

Illustrated frames are original drawings, CC-BY-4.0, Jaideep (Jay) Aher. The 99-photograph track uses Wikimedia Commons frames. Credits and licenses are in `eval/photos/CREDITS.md`. The Commons frames are not in this copy: painted registration numbers and phone numbers stayed readable after the bumper-plate boxes, so `web/public/photos/` is empty. Model-facing files stay out of git. Rebuild them locally with `python eval/photos/fetch_sources.py` and `python eval/photos/build_stimuli.py`.

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

AI coding assistants helped build the tooling: the harness, the stimulus scripts, the site, and the analysis code. The design decisions, the protocols, and the analysis were reviewed by Jaideep Aher. Transcription notes that say "AI-assisted visual spot-check, not human-verified" are not human labels.

## Reproduce

```bash
hornok make-scenes --out eval/round1/stimuli
python eval/round1/run_benchmark.py
python eval/round1/analyze.py
python eval/round3/build_stimuli.py
python eval/round3/run_benchmark.py
python eval/round3/analyze.py
```

The round-1 contract is `eval/preregistration.md`. Later contracts are `eval/round2/preregistration.md`, `eval/round3/preregistration.md`, `eval/dev/protocol.md`, `eval/xai/protocol.md`, and `eval/photos/protocol.md`. Display copies of the illustrations are already in `web/public/stimuli`. llama.cpp `b11716` is the multimodal runtime. Point `HORNOK_LLAMA_BIN` at `llama-mtmd-cli`. The default path is `vendor/llama-b11716/llama-mtmd-cli` inside this repo. The binary is not committed.
