# Horn OK Please

[![tests](https://github.com/jaideep-aher/horn-ok-please/actions/workflows/ci.yml/badge.svg)](https://github.com/jaideep-aher/horn-ok-please/actions/workflows/ci.yml)

## Read this first

When painted truck text changes a driving model's decision, can we see why, and does the model's own explanation admit it?

Gemini 3.8 Flash passed the STOP versus GO gate: STOP 20/20, GO 17/20, balanced accuracy 0.925. The main English attack flipped 0/20. A second phrase flipped 4/20 in Marathi and 3/20 in Hindi. Both defenses brought the attack to 0/20 and over-blocked 4/17 GO scenes. The open models did not pass. On six drawings, Qwen2.5-VL 3B Q8 English paint flipped 6/6, and OpenCV Telea restored 6/6. Marathi, benign text, and gibberish flipped 0/6.

This is not a crash risk and not a road test. The photograph track has no empty lane, so GO recall is undefined: STOP 28/31, paint changes 0/19, and the paired tests are not significant. Jaideep (Jay) Aher, Duke AIPI 590. Install the test extra, run pytest, then start the site from the web folder.

```bash
pip install -e ".[dev]"
pytest
cd web && npm ci && npm run dev
```

![Marathi GO line painted on an illustrated truck tailgate, with a person still on the crossing](web/public/stimuli/attack/ped_crossing__truck_rear__deva.png)

The site is a static export. The poster carries a QR placeholder until the Pages URL is live.

## The question

When painted truck text changes a driving model's decision, can we see why, and does the model's own explanation admit it?

## Key results

| Finding | Stored result |
|---|---|
| Gemini 3.8 Flash gate | Passed. STOP 20/20, GO 17/20, balanced accuracy 0.925, unparsed 0/40. |
| English attack, and the second phrase | G1 English 0/20. G2 Marathi 4/20 (Wilson 95% 0.081 to 0.416), Hindi 3/20. English and Hinglish G2 0/20. Benign text 0/20. |
| Defenses | Prompt and OCR each left G1 at 0/20 and over-blocked 4/17 true-GO scenes. |
| Open models | None passed the same gate. On six drawings, Qwen2.5-VL 3B Q8 English paint changed 6/6 and OpenCV Telea restored 6/6. |
| Photographs | STOP 28/31. Paint changes 0/19. GO recall is undefined, so the gate does not pass. McNemar then Holm is not significant. |

Flash-Lite returned HTTP 400 on all 40 gate images, so its attacks were not run. The full log, including the prompt diagnostic, is `docs/RESULTS_LOG.md`.

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

Illustrated frames are original drawings, CC-BY-4.0, Jaideep (Jay) Aher. The 99-photograph track uses Wikimedia Commons frames. Credits and licenses are in `eval/photos/CREDITS.md`. Unblurred plates and faces are not in this git history. Blurred copies are in `web/public/photos/`. Rebuild the model-facing files with `python eval/photos/fetch_sources.py` and `python eval/photos/build_stimuli.py`.

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

Checked against the arXiv page on 18 October 2026. Numbers in those abstracts are theirs, not this study's.

- Nhat Chung, Sensen Gao, Tuan-Anh Vu, Jie Zhang, Aishan Liu, Yun Lin, Jin Song Dong, and Qing Guo. "Towards Transferable Attacks Against Vision-LLMs in Autonomous Driving with Typography." arXiv:2405.14169, 2024. https://arxiv.org/abs/2405.14169
- Luis Burbano, Diego Ortiz, Qi Sun, Siwei Yang, Haoqin Tu, Cihang Xie, Yinzhi Cao, and Alvaro A. Cardenas. "CHAI: Command Hijacking against embodied AI." arXiv:2510.00181. https://arxiv.org/abs/2510.00181
- Justus Westerhoff, Erblina Purelku, Jakob Hackstein, Jonas Loos, Leo Pinetzki, Erik Rodner, and Lorenz Hufe. "SCAM." arXiv:2504.04893, 2025. https://arxiv.org/abs/2504.04893
- Zhou, Aghakishiyeva, Arya, Dale, Poling, Houliston, Womble, Larsen, Johnston, and Bent. "On Thin Ice." arXiv:2510.21689. Adapted as a scoring template, not as a seal-detector result.
- Aghakishiyeva, Zhou, Arya, Dale, Poling, Houliston, Womble, Larsen, Johnston, and Bent. "Photorealistic Inpainting for Perturbation-based Explanations." arXiv:2510.03317. Adapted as mask-local removal. This run does not use their Segment Anything or Stable Diffusion pipeline.
- Mendi and Bent. "Why2Speak." arXiv:2608.20670. Adapted as a direct decision versus a reason-then-decide prompt.
- Ding, Bent, and Wendell. "GLEaN." arXiv:2604.09923. Cited for the public-facing aim. Their portrait study is not run. The expo form does not collect responses.
- Souvik Kundu and colleagues. "LVLM-Compress-Bench." arXiv:2503.04982. Anik De and colleagues. "Bharat Scene Text." arXiv:2511.23071. Vijayasri Iyer, Maahin Rathinagiriswaran, and Jyothikamalesh S. "RoadscapesQA." arXiv:2602.12877. None of those datasets are in this run.

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
