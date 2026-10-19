# What Jay still has to do

The scored run, the site, and the poster can be finished without accounts. Everything below needs Jay.

## 1. Confirm the expo date

One planning assumption is an expo in the week of 7 December 2026, with a print deadline around 2 December. A separate planning note pointed at late November. Neither date is confirmed in this repo. Confirm the date with the instructor before sending the PDF to print. Print shops need a few days.

## 2. API models

The Gemini client is in the repo and was used for the locked STOP/GO gate, the explanation stage, and the photograph track. Scores are in `eval/gemini_remote/results/`. GPT-4o and Claude are not scored backends.

To run Gemini again:

1. Create a key in the provider's console. Do not commit it.
2. `GEMINI_API_KEY=... python eval/gemini_remote/run_gemini.py`. Without the key, the client stores nothing and does not send a request.
3. Append rows to a new jsonl. Do not delete the stored rows.
4. Do not add Gemini to the round-1 confirmatory family after looking at attack success. Report a new run as its own file.

Budget in the idea report was about $20–60 for a small API slice. That figure was the report's planning number, not a quote from a vendor invoice.

## 3. Publish the site

The site is a static Next.js export once `web/` is built.

- GitHub Pages: push the `out/` directory, or use an action that runs `npm ci && npm run build` with `output: 'export'`.
- Vercel: import the repo, set the root directory to `web`, the build command to `npm run build`, and the output directory to `out`. No environment variables are required for the offline demo.
- The poster QR is `poster/qr-site.png` and points at https://jaideep-aher.github.io/horn-ok-please/.

No token is required for the offline demo. Live mode stays hidden unless the build sets `NEXT_PUBLIC_LIVE_MODE=1`. That dialog expects an OpenAI-compatible endpoint and a key typed into the browser and kept in `localStorage`. The key is not written to the repo.

## 4. Print the poster

`poster/horn-ok-please.pdf` is 24 by 24 inches. Print it at 100% scale, no "fit to page." A campus plotter or a print shop that accepts a PDF with a custom page size is enough. The foam-board truck panel from the idea report (a physical "Horn OK Please" board and a webcam) is optional and is not required for the file deliverable.

## 5. The gate that is in force

Round 3 is the gate: STOP versus GO, balanced accuracy at least 0.75, recall at least 0.60 on both classes, unparsed at most 10%. The four open models on CPU failed it. Gemini 3.8 Flash passed it. Do not lower the bar after looking at the file.

Round 2, four actions on 42 scenes, is a closed failed gate. It is not the target to chase. Qwen2.5-VL 3B (Q8_0 and Q4_K_M), Gemma 3 4B Q8_0, and InternVL2.5 1B Q8_0 all missed the 60% agreement bar, with unparsed at 0.

- A larger checkpoint, on a GPU, can be scored on the locked STOP/GO items. Do not retune the prompt after seeing accuracy except by a new dated protocol.
- IDD or RoadscapesQA only after you have read the current license and, if redistribution is not allowed, keep the frames out of the public repo and report counts without shipping images.
- Bharat Scene Text crops for the literacy probe: https://github.com/Bhashini-IITJ/BharatSceneTextDataset (linked from the paper). Do not substitute those numbers into the card table.
- Expert notes and a classroom exercise are yours to collect. Do not invent them. The expo form on the site stays disabled. File any permitted notes in `docs/expert_notes.md`.

## 6. Physical transfer, if you do it

Photograph a printed page on a parked vehicle or a model truck, in a place with no other road users. Do not test in traffic. Three distances and two lights, as in the idea report, is enough to see whether the digital flips survive. Keep the prints out of the repo if they are photos of someone else's vehicle.

## 7. Expert read

The rubric rewards a limitation that a domain reader has seen. Ask one person who works on ADAS or fleet safety to read the poster and write three sentences. File their notes in `docs/expert_notes.md` with their permission. Do not invent the notes.
