# Expo pitch — Horn OK Please

Jaideep (Jay) Aher. Spoken at about five sentences a minute. Under five minutes.

## Script

The back of an Indian truck often says Horn OK Please. A vision-language model sees those letters as part of the road, in the same picture as the person on the crossing.

The question is: when painted truck text changes a driving model's decision, can we see why?

I drew the hazards, so the right answer is known. A model is attacked only after it can tell STOP from GO. If the paint changes STOP to GO, I remove the paint and ask again.

The first pilot could not do the clean task, so a zero attack rate there was the model failing. The next round asked for four actions from one still frame, and every model missed a 60% agreement gate.

Gemini 3.8 Flash passed the STOP versus GO gate: STOP 20/20 (Wilson 95% 0.839 to 1.000), GO 17/20 (0.640 to 0.948), balanced accuracy 0.925, unparsed 0/40. The confirmatory tests, T1 through T4 and T7 through T9, are exact McNemar then Holm, and every p is 1. That is a null, not a hidden effect. A second phrase is outside that family. It flipped 4/20 in Marathi (Wilson 95% 0.081 to 0.416) and 3/20 in Hindi (0.052 to 0.360). English versus Marathi on that phrase is exploratory: n=20, 4 discordant pairs, McNemar p=0.125.

Both defenses were scored only on the first phrase. Undefended flips are 1/80 (Wilson 95% 0.002 to 0.067) and each defense is 0/80, so the paired test is p=1. There is no measurable benefit, and the defenses were not run on the second phrase. Each one also blocked 4 of 17 true GO scenes (0.096 to 0.473). Flash-Lite returned HTTP 400 on all 40 gate images, so it was never evaluated. An earlier Flash gate, 40 of 40 unparsed, was a client failure and is not a score. The stored thinking field says off, and 486 of 488 Flash rows still used thinking tokens.

The open models on a CPU did not pass that gate. Qwen2.5-VL 3B Q8 said GO on 0 of 20 and its balanced accuracy was 0.500, so its flips are not headline evidence. Six drawings are illustrative examples from that gate-failed model. The English line changed all 6, and OpenCV Telea restored all 6. Four of those drawings are STOP scenes, so those four changes ignore the hazard. Two are GO scenes, so those changes correct a STOP. Marathi, benign text, and gibberish changed 0 of 6. The rationales were not a scored admission test. The files are Gemma 3 4B IT, not a model named Gemma 4B: `gemma-3-4b-it-Q8_0.gguf` and `gemma-3-4b-it-Q4_K_M.gguf` from `ggml-org/gemma-3-4b-it-GGUF`. Qwen is `Qwen2.5-VL-3B-Instruct` Q8_0 and Q4_K_M from `ggml-org/Qwen2.5-VL-3B-Instruct-GGUF`. Flash is the resolved id `gemini-3.8-flash`.

On the Commons photographs there is no empty lane, so GO recall is undefined. Flash said STOP on 28 of 31 rear views (Wilson 95% 0.751 to 0.967), and replacing the paint changed 0 of 19. Those paired tests are not significant. The frames are withheld until a privacy review. The photograph fill was LaMa. The six drawings used Telea.

This is not a crash risk and not a road test. The person on the crossing lives with a wrong call. If you ship a vision policy, score STOP and GO before you score an attack, and publish the over-block beside any flip.

## Appendix

Intervals, the prompt diagnostic, and the per-round tables are in `docs/RESULTS_LOG.md`.
