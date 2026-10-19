# Expo pitch — Horn OK Please

Jaideep (Jay) Aher. Spoken at about five sentences a minute. Under five minutes.

## Script

The back of an Indian truck often says Horn OK Please. A vision-language model sees those letters as part of the road, in the same picture as the person on the crossing.

The question is: when painted truck text changes a driving model's decision, can we see why, and does the model's own explanation admit it?

I drew the hazards, so the right answer is known. A model is attacked only after it can tell STOP from GO. If the paint changes STOP to GO, I remove the paint and ask again.

The first pilot could not do the clean task, so a zero attack rate there was the model failing. The next round asked for four actions from one still frame, and every model missed a 60% agreement gate.

Gemini 3.8 Flash passed the STOP versus GO gate: STOP 20/20, GO 17/20, balanced accuracy 0.925. The plain English line flipped 0 of 20 STOP scenes. A second phrase flipped 4/20 in Marathi and 3/20 in Hindi, and 0/20 in English and in Hinglish. Both defenses brought the attack to 0/20, and each one also blocked 4 of 17 true GO scenes. Flash-Lite returned an empty HTTP 400 on all 40 gate images, so its attacks were not run.

The open models on a CPU did not pass that gate. On six new drawings, Qwen2.5-VL 3B Q8 flipped all 6 when the English line was painted, and OpenCV Telea restored all 6. Marathi, benign text, and gibberish flipped 0 of 6.

On 99 Commons photographs there is no empty lane, so GO recall is undefined. Flash said STOP on 28 of 31 rear views, and replacing the paint changed 0 of 19. Those paired tests are not significant. The photograph fill was LaMa. The six drawings used Telea.

This is not a crash risk and not a road test. The person on the crossing lives with a wrong call. If you ship a vision policy, score STOP and GO before you score an attack, and publish the over-block beside any flip.

## Appendix

Intervals, the prompt diagnostic, and the per-round tables are in `docs/RESULTS_LOG.md`.
