# Horn OK Please: expo site plan (phone-first, QR entry)

Based on main @ 5a072ae (2026-10-18). Numbers below come only from committed JSON. "pending data" means the numbers aren't on main.
Style references: Latent Gaze and Alba. The page leads with the story, in short plain-language sentences. One idea per screen, with detail in collapsible sections.

## Global
- Entry: the poster QR goes to `https://jaideep-aher.github.io/horn-ok-please/` (it returns 404 today). Add `?src=poster` so it can be counted later.
- Build: `web/next.config.ts` needs `basePath: '/horn-ok-please'`. All `fetch('/data/...')` and `<img src="/...">` calls must be basePath-aware: today they are absolute root paths and would 404 on Pages.
- Mobile: single column at 360px or wider. Tap targets at least 44px. Images use `loading="lazy"` with fixed aspect ratios. No hover-only info.
- Accessibility: meaningful alt text on every frame. Heatmaps need a text equivalent and a non-colour cue (pattern or outline). Action chips should show the text "STOP"/"GO", not colour alone. Respect `prefers-reduced-motion`. Set `lang="hi"`/`"mr"` on Devanagari spans.

## 1. Hook: a painted truck tail
- Purpose: show an outsider in 5 seconds that words painted on a truck can steer a driving AI.
- Content: one full-width truck tail (blurred Commons photo or rendered scene) with a one-line question: "Can paint on a truck tell a self-driving AI to GO?" Add a scroll cue.
- Feeds from: `hero.tsx`. Its copy ("small vision-language model can tell STOP from GO") is stale and needs a rewrite. Image: `/stimuli/clean/*.png` or `/xai/xai_*__g1_en.png` (pending data: images aren't committed).
- Mobile: the image should take at most 60vh, with the headline over or under it in large type.
- A11y: alt text describes the painted text and the scene. The headline is the page's only h1.

## 2. Try it: the painter
- Purpose: hands-on. The visitor paints a phrase and sees the stored model action.
- Content: phrase picker (EN / Devanagari / Hinglish), plate size, the resulting frame, and the precomputed action chip. Hide live mode for expo visitors.
- Feeds from: `painter.tsx` using the `pilot.json` / `summary.json` round-1 pilot trials. Images: `/stimuli/clean/{id}.png` and painted variants (pending data: the symlink target is empty). Note for the story: the round-1 pilot model (SmolVLM) mostly didn't answer, so this section should say "stored pilot outputs" honestly.
- Mobile: put controls below the image in a sticky bottom bar or stepper. Avoid long selects.
- A11y: controls are keyboard reachable and labelled. Announce the result through `aria-live="polite"`.
- Live mode (`live-dialog.tsx`): it asks for an OpenAI-compatible base URL and API key, stores the key in localStorage, and calls from the browser. It is NOT excluded from the build today. Gate it behind a build flag or remove it from the public/expo build.

## 3. See what the model sees
- Purpose: explain why the decision flipped, using an occlusion heatmap plus an inpainting restore.
- Content: three tabs per scene (clean, painted, painted text inpainted away) with the decision under each, plus a 3×3 occlusion overlay.
- Numbers (`web/public/data/xai.json`, Qwen2.5-VL 3B Q8, six scenes, fill = telea):
  - English GO line changed the decision on 6/6 parsed pairs.
  - Inpainting restored the clean decision on 6/6.
  - Insertion matched on 6/6.
  - Marathi (g1_mr) changed 0/6.
  - Faithfulness: deletion flip 10/15, insertion match 11/15 (3 inert skipped).
  - Gaze cohort: of 12, 0 localized the hazard, 9 missed it, 3 had inert occlusion.
  - Self-explanation "says" changed: dev 10/29, xai 2/18.
  - White-box attention: not run.
- Feeds from: `see-panel.tsx` + `xai.json`. Images `/xai/*.png` (pending data: not committed).
- Mobile: put the tabs in a segmented control and the overlay toggle in a large switch. Swipe between scenes.
- A11y: under each overlay, add text such as "Hot cells: the painted line (rows 2–3)". Overlay cells use patterns as well as red.

## 4. Findings
- Purpose: three takeaways, each a card with one number and a plain sentence.
- (a) Gemini gated result: pending data. No Gemini results JSON is committed on main yet. Current copy ("Gemini was not called") is false and must change once the results are published.
- (b) Open-model over-caution (`round3.json`, round-3 gate, 20 STOP / 20 GO scenes, 168 predictions): all four open models got STOP right on 20/20. GO recall was 1/20 for qwen25vl-3b-q4 and 0/20 for qwen25vl-3b-q8, gemma3-4b-q8 and gemma3-4b-q4. Balanced accuracy was 0.525 / 0.5 / 0.5 / 0.5 against a 0.75 threshold, so no model passed. Plain reading: they say STOP to almost everything, so attack-success rates on them are not meaningful.
- (c) 6/6 flip-and-restore: the xai.json numbers from section 3, framed as the headline result, with scope: 6 rendered scenes, one 3B model.
- Feeds from: `round3-report.tsx` (references `/round3/*.png`, which is missing), `findings.tsx`, `dev-report.tsx` (`dev.json`; `/dev/*.png` is missing). Round-2 is in `round2-report.tsx` (collapsed).
- Real photos: `photo-gallery.tsx` fetches `/data/photos.json`, which doesn't exist, so the empty state shows. Pending data.
- Mobile: stack the cards. Bar charts (`rate-bar.tsx`) should show the numbers as text too, and so should the CIs.
- A11y: charts need a text table fallback. Avoid jargon like "balanced accuracy" without a gloss.

## 5. Limits and misuse
- Purpose: responsible-AI framing. No physical how-to, scope limits, the defense ships beside the attack.
- Content:
  - Rendered scenes and blurred Commons photos only.
  - Small open models.
  - No road test.
  - Plates and faces blurred on the site; models saw unblurred frames.
  - The OCR-mask defense and over-blocking (`defenses`/`overblock` arrays in round3.json are empty: pending data).
- Feeds from: `misuse.tsx`, `defense-section.tsx`, `literacy-section.tsx` (round3 literacy: gemma3-4b-q4 EN 4/4 exact, Devanagari 2/4 exact, mean similarity 0.78).
- Mobile: short bullets, with expanders for detail.
- A11y: plain language at roughly grade 8.

## 6. About
- Purpose: who made it, the course, credits, and the AI-assistance disclosure.
- Content:
  - Jaideep (Jay) Aher, Duke AIPI 590.
  - Repo link (the repo is private now, so link it only once it's public).
  - Commons credits (`eval/photos/CREDITS.md`).
  - Licenses.
  - The README AI-assistance note verbatim.
- Feeds from: `methods.tsx` and the footer in `exhibit.tsx`.
- A11y: links have descriptive text.

---

## Ranked tasks

### P0 (site broken or misleading)
- Add a Pages deploy workflow (build web, upload `out/`, deploy) and enable Pages: `.github/workflows/` (new), repo settings. Note the repo is private, so Pages on the user's plan may require it to be public.
- Add `basePath: '/horn-ok-please'` and make every fetch/img path prefix-aware: `web/next.config.ts`, `exhibit.tsx`, `painter.tsx`, `see-panel.tsx`, `round3-report.tsx`, `dev-report.tsx`, `photo-gallery.tsx`, `live-dialog.tsx`.
- Commit real (blurred) images in place of the symlink to the empty `eval/stimuli`: `web/public/stimuli`, plus new `web/public/xai/`, `round3/`, `dev/`, `photos/`.
- Publish `web/public/data/photos.json` (blurred photo track): `poster/publish*.py`, `photo-gallery.tsx`.
- Remove or gate the API-key live mode from the public build: `live-dialog.tsx`, `painter.tsx`.
- Fix stale Gemini / scope copy: `hero.tsx`, README Results, `docs/EXPO_PITCH.md`, poster.

### P1 (story and design)
- Reorder `exhibit.tsx` to: hook → painter → see panel → findings → limits → about. Today the order is hero, round3, dev, see, photos, painter, and so on.
- Add a findings summary with 3 cards before the detailed reports: new component, `exhibit.tsx`.
- Add a Gemini findings card once its JSON is committed: `eval/gemini_remote/`, `web/public/data/`.
- Add text alternatives and patterns to heatmaps and charts: `see-panel.tsx`, `photo-gallery.tsx`, `rate-bar.tsx`.
- Do a mobile pass on painter controls and tap targets: `painter.tsx`, `ui/button.tsx`.
- Add page metadata, OG image and title for QR shares: `web/src/app/layout.tsx`.

### P2 (polish)
- Delete the create-next-app leftovers (`file/globe/next/vercel/window.svg`) and the default `favicon.ico`: `web/public/`, `web/src/app/`.
- Remove the duplicate `summary.json` (identical size to round2.json, 8444 bytes): `web/public/data/`.
- Change the `web/README.md` dev command to a plain `npm run dev`.
- Reword the whitebox reason: `eval/xai/results/whitebox.json`.
- Fix the red CI python job (5 failing tests per rubric_audit): `tests/`, `pyproject.toml`.
