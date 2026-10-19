# Horn OK Please: design and implementation spec (web/)

Target: Next 15.5 static export (`output: "export"`), React 19, Tailwind 4, GitHub Pages at `https://jaideep-aher.github.io/horn-ok-please/` (basePath `/horn-ok-please`).
Companion to `web/docs/site_plan.md`, which sets the section order (hook → try it → see → findings → limits → about) and lists the numbers that can be cited.
Rules:
- No number without a committed JSON source.
- Images come from blurred derivatives only.
- Every link must resolve.
- Do not start until the prerequisite changes (basePath, Pages workflow, stimuli, blurred photos + `photos.json`, Gemini JSON, gated live mode, copy fixes) have landed on main and been verified.

---

## 1. Style references

**The Latent Gaze**: https://bd1ng.github.io/latent-gaze/ (Bochu Ding, Duke Culture I/O Lab & Explainable AI; code at github.com/bd1ng/model-gaze). Fetched 2026-10-18. Why it works:
- **Opens with a direct question to the reader** ("What does it look like to be a ___?") and one striking image before any method. The method follows in one-sentence beats ("This isn't a real person." / "For each label, I generated thousands of portraits.").
- **Pacing:** each scroll step carries about one sentence and one visual change. The method is explained in plain language at the moment it's needed ("each pixel represents the median value…").
- **Restraint:** a near-monochrome page, so the images carry the colour. Large serif/sans headlines with short body lines.
- **Numbers** are words, not dashboards ("thousands of portraits"). The interactive gallery comes *after* the story has earned it.
- **Closing:** "In Closing" widens to the stakes, followed by a references list and thanks.
- **What to borrow:** a question hook, one idea per screen, explaining the method inline, and ending with references.
- I couldn't verify the exact fonts or scroll library from the fetched text. Don't copy them; borrow the structure.

**Alba** (confirmed by Jay): the Duke AIPI 2025 hackathon Chrome extension by Lindsay Gross, Andrew Jin, Shreya Mendi and Sam Otto. Repo: https://github.com/lindsaygross/Alba (read 2026-10-18).

What's actually there:
- **README:** a one-line value proposition ("live view of the energy, carbon, and water cost of every prompt"), then a Chrome Web Store link, a demo video (YouTube, not watched), and a Zenodo DOI citation.
- **Bolded feature bullets:** "Real-time footprint labels", "Inline prompt optimizer", "Floating dashboard + popup", "Spotify-style 'Wrapped'" recap cards, "Configurable methodology", "No API keys in the extension".
- **Long References section:** every coefficient is tied to a named source (Ember, OWID, IEA, NREL, EIA, arXiv benchmarks, Epoch AI).
- **Visual material is thin.** There are no screenshots in the repo. The only image is `icons/alba_logo.png`: a flat two-tone green dove/bird in a geometric, low-poly style, with dark-to-light green gradient wings on a light grey background.
- **From `styles.css`:**
  - Font stack `"Inter", "Segoe UI", -apple-system…`.
  - A sage/green accent (`--alba-sage`, #6aa484, #8bd8b5) on near-white tints (#f3faf4, #fdfbef) and dark slate (#0e1f2c, #1f2b27).
  - Pink-magenta accents (#f15f79, #b24592) in a gradient for the Wrapped overlay.
  - Heavy use of pill shapes (`border-radius: 999px`) and rounded cards (12–28px radii).
  - A conic-gradient progress ring.
  - Class names show the UI pattern: inline `.alba-impact-label`, `.alba-suggestion-badge`, and a `.alba-wrapped-overlay` with a grid of recap cards.

Borrowing notes for Horn OK Please:
1. **Tone:** a one-sentence "make the invisible visible" promise at the top, then plain, verb-first feature bullets. Our equivalent: "See how paint on a truck can change what a driving AI decides."
2. **Inline labels:** Alba attaches a small label right where the action happens. Mirror this with the STOP/GO action chip placed directly on or under the frame in the painter and slider, not in a separate results table. Use pill-shaped chips (`rounded-full`) with the word plus an icon.
3. **"Wrapped"-style recap cards:** the findings section becomes 3–4 swipeable recap cards, each with one big number, one sentence, a scope line and a `<Source>` (snap-scroll on mobile, grid on desktop). Use our truck-art palette, not Alba's pink gradient.
4. **Sources as a first-class section:** like Alba's References, end with an auto-generated Sources list. It matches our claim-sourcing rule.
5. **Trust copy:** Alba states "No API keys in the extension" up front. We state "No server, no tracking, no API keys. Every number links to its data file" in the About/footer.
6. **Restraint in the mark:** a flat, two-tone geometric logo. Our icon should likewise be a simple two-tone mark (marigold on night), not a detailed truck illustration.
- **Don't borrow:** the Inter font (we need Devanagari coverage) or the green/pink palette.
- Since Alba has little visual and story material, **story pacing follows Latent Gaze** (question hook, one idea per scroll step, method explained inline, references at the end). Alba supplies the UI patterns and tone.

---

## 2. Visual system

**Theme decision:** light "paper" theme by default (readable in bright expo halls and on phone glare). A dark section is used for the hook only (night highway, truck tail lit). Respect `prefers-color-scheme: dark` with a full dark token set. Ship it in PR 2 behind CSS variables; it's not a separate design.

**Fonts** (self-hosted with `next/font/google`, `display: "swap"`, subsets limited):
- Display: **Noto Serif Devanagari** (variable wght 100–900; it includes Latin glyphs). Use it for h1/h2 and painted-phrase previews.
- Text/UI: **Noto Sans** (variable wght, Latin) plus **Noto Sans Devanagari** (variable) in the stack, so mixed EN/Devanagari runs share metrics.
- Urdu: **Noto Nastaliq Urdu**, loaded only if any rendered string contains Arabic-script characters. The photo track has a `g1_ur` condition, so the photo gallery needs it. Lazy-load it with `preload: false`, and apply it only to elements with `lang="ur" dir="rtl"`.
- Stencil accent (existing `font-stencil`) is used only for small uppercase kickers, never body text.
- Preload only the display weight used above the fold.

**Type scale:** fluid, base 17px at 360px rising to 19px at 1280px, ratio 1.25.

| token | size (clamp) | use |
|---|---|---|
| `--step--1` | 0.85rem | captions, Source chips |
| `--step-0` | 1rem–1.1rem | body (line-height 1.6, max 65ch) |
| `--step-1` | 1.25rem | lead |
| `--step-2` | 1.56rem | h3 |
| `--step-3` | 1.95rem–2.4rem | h2 |
| `--step-4` | 2.6rem–4.2rem | h1 / hero |
| `--step-num` | 3rem–5rem | finding numerals (tabular-nums) |

**Palette (truck-art inspired). Contrast is measured against paper `#FFF8EC` and ink `#1B1A2E`:**

| token | hex | on paper | on ink | rule |
|---|---|---|---|---|
| paper | #FFF8EC | — | 16.1:1 | page bg |
| ink | #1B1A2E | 16.1:1 | — | text |
| muted | #5B5566 | 6.8:1 | — | secondary text (AA) |
| signal (truck red) | #B3122E | 6.5:1 | 2.5 ✗ | text/links on paper; STOP chip bg with paper text |
| peacock (blue) | #1F4FA0 | 7.4:1 | 2.2 ✗ | links, focus ring on paper |
| teal | #00695C | 6.3:1 | 2.6 ✗ | GO chip bg with paper text |
| marigold | #F4B400 | 1.75 ✗ | 9.2:1 | **never text on paper**: fills, underline strokes, highlight on ink, focus ring on dark |
| night | #14132A | 17.2:1 | — | hook section bg |

- Decorative truck-art motifs (border chevrons, a lotus or eye "nazar" ornament, "HORN OK PLEASE" stripe) are inline SVG with `aria-hidden`. Keep them to 2 or 3 motifs.
- The STOP/GO chips always include the word, and an icon (octagon or arrow), not colour alone.

**Spacing:** 4px base. Tokens 1/2/3/4/6/8/12/16/24 (×4px). Sections use `py-16` mobile and `py-24` desktop. Content width is 65ch for text and 72rem for media. Radii 6px/12px. One shadow token.

---

## 3. Interactions per section

The rules below apply to every section:
- Each interaction works with mouse, touch and keyboard.
- Motion runs under 400ms and is disabled under `prefers-reduced-motion: reduce`.
- Use IntersectionObserver, never scroll listeners. No scroll-jacking.
- No new runtime dependencies beyond what's in `package.json`, unless the PR justifies one under 5 KB gz.

**1. Hook** (`hero.tsx`, night section)
- Full-bleed truck-tail image (blurred), using AVIF with WebP fallback.
- Over it, an SVG text path reads "HORN OK PLEASE" and reveals as a paint stroke. Animate `stroke-dashoffset` (about 1.2s) via CSS, then fill marigold.
- Below it: "Can paint on a truck tell a driving AI to GO?" and a "Try it ↓" button that jumps to `#studio`.
- **Reduced motion:** the text appears fully painted, with no animation.
- The text is real HTML (an `h1` overlaying the SVG, with the SVG `aria-hidden`), so it's readable and selectable.
- LCP element = hero image (preloaded).

**2. Painter** (`painter.tsx`)
- A three-step stepper: 1) pick a phrase (chips for EN / मराठी / Hinglish, each chip with a `lang` attribute), 2) pick a plate size (segmented control), 3) see the frame plus the stored action chip with a `<Source>`.
- The frame swaps with a 150ms crossfade. Preload the neighbouring variants when an option is hovered or focused.
- Controls are radio groups (`role="radiogroup"`, arrow keys). The result is announced in an `aria-live="polite"` region ("Stored model answer: STOP").
- Copy must say "stored output from the pilot model", not "the model thinks".
- Live mode is not in the public build (gated by a prerequisite change). Don't render a disabled button for it either.
- **Mobile:** image on top, sticky bottom control sheet (max 40vh), tap targets of at least 44px.

**3. See what the model sees** (`see-panel.tsx`, new `compare-slider.tsx`)
- **Compare slider:** two stacked images (clean ↔ painted, then painted ↔ inpainted via a 3-way segmented toggle) clipped by a draggable divider.
  - Implement it as a native `<input type="range">` overlay (so keyboard, touch and screen readers work for free), with `aria-label="Reveal painted version"` and `aria-valuetext="40 percent painted"`.
  - Arrow keys move it by 5% and Home/End jump to the ends.
- **Decision strip** under the images: clean → STOP/GO, painted → …, inpainted → …, each with a `<Source>`.
- **Heatmap reveal:** a "Show where it looked" toggle button (`aria-pressed`) overlays the occlusion grid (3×3 in xai.json, 6×6 in photos.json).
  - Cells fade in staggered at 30ms each; with reduced motion they appear instantly.
  - Hot cells get red at 45% opacity **plus** diagonal hatching (an SVG pattern), so they read without colour.
  - A text equivalent under the image: "Changing the decision: cells r2c1, r2c2 (the painted line). Inert: 7 cells."
- **Scene picker:** horizontal snap-scroll thumbnails with buttons, and arrow keys within the group.

**4. Findings** (`findings.tsx` replaced by a new `finding-card.tsx` set)
- Three to four cards, each with: a big numeral (`k/n` shown as "6 of 6"), a one-sentence plain reading, a scope line ("6 rendered scenes, Qwen2.5-VL 3B Q8"), and a `<Source>`.
- **Count-up** runs only when 50% visible, once, over 600ms, rendered with `tabular-nums`.
  - The screen-reader text is the final value from the start (`aria-label` set to the final value; the animated span is `aria-hidden`).
  - With reduced motion, show the final value immediately.
- The Gemini card renders only if the Gemini JSON exists at build time. Otherwise there's no card, rather than a "pending" placeholder at the expo.
- The round-3 over-caution card adds a small dot plot (20 STOP / 20 GO per model) as SVG, with an adjacent `<table>` behind "Show as table" (a native `<details>`).

**5. Limits and misuse** (`misuse.tsx`, `defense-section.tsx`): a static, accordion-style list built with native `<details>`. One line each, with "why it matters" inside.

**6. About** (`methods.tsx` + footer)
- Author, course, credits link, licenses, and the README AI-assistance note verbatim.
- Add a "Sources" list that is auto-generated from every `<Source>` used on the page.

---

## 4. Claim sourcing

**Component**: `web/src/components/source.tsx`
```tsx
type SourceProps = { file: DataFile; path: string; children?: React.ReactNode };
// DataFile = "round3.json" | "round2.json" | "dev.json" | "xai.json" | "photos.json" | "gemini.json" | ...
<Source file="xai.json" path="conditions.g1_en.restored">6 of 6</Source>
```
- Renders the value plus a small superscript link (`[1]`-style chip, accessible name "Source: xai.json, conditions.g1_en.restored").
- The link targets the deployed data file: `${basePath}/data/xai.json`. Its `title` and the Sources list also show the GitHub blob URL (`https://github.com/jaideep-aher/horn-ok-please/blob/<SHA>/eval/xai/results/summary.json`), with the SHA injected at build time from `GITHUB_SHA`.
- The repo is private (Pages works via GitHub Pro), so the GitHub link stays hidden (env `NEXT_PUBLIC_REPO_PUBLIC=false`) until the repo is made public. No link 404s for visitors.
- **Values come from the data, never from children:** `useNumber(file, path)` resolves the value from the same loaded JSON, and `<Source>` throws in dev if `children` is passed as a hardcoded number.
- Formatting goes through `lib/format.ts` (`k of n`, percentages to whole numbers, CIs as "95% CI a–b").
- Add a `data-source="xai.json#conditions.g1_en.restored"` attribute on the rendered value element.

**Build-time check**: `web/scripts/check-claims.mjs`, run after `next build`:
1. Parse every HTML file in `out/` (node-html-parser).
2. For each `[data-source]`, load `out/data/<file>`, resolve the dotted path (array indices allowed, e.g. `gate.0.go_correct`), format it with the same formatter, and assert it equals the element's text.
3. Find every digit sequence in visible text that isn't inside `[data-source]`, `<code>`, a date, or an allowlist (`web/scripts/claims-allow.json`: e.g. "590", "2026", "3B", "6×6", "1200").
4. Any untraced number fails the job with the file, selector and text.
5. It also verifies that each `public/data/*.json` matches its `eval/**/results` origin byte-for-byte (sha256), using a map in `web/scripts/data-map.json`.

Note: because pages fetch JSON client-side today, static HTML has no numbers. **Change to build-time data:** import the JSON in server components (`import xai from "@/../public/data/xai.json"`, or `fs` reads in `page.tsx`) so numbers are in the exported HTML. This helps SEO, no-JS users and LCP, and makes the check meaningful. Keep client components only for interactivity.

---

## 5. OG, share and icons

- **OG image:** 1200×630 PNG at `public/og.png`, generated at build time by `web/scripts/make-og.mjs` (satori + @resvg/resvg-js as devDependencies, or `next/og` `ImageResponse` in a `opengraph-image.tsx` route, which is supported in static export as a prerendered file).
  - **Layout:** left 60% is a blurred truck-tail photo (from the blurred set only) with a slight night gradient. Right 40% is the night background with "HORN OK PLEASE" in marigold display serif, the subtitle "Can paint on a truck steer a driving AI?" in paper colour, and "Jaideep Aher · Duke AIPI 590" in muted text.
  - No numbers on the OG image (they can go stale).
  - Text is at least 48px for the title. Keep a 40px safe margin.
- **Metadata** (`layout.tsx`, `export const metadata`):
  - `metadataBase: new URL("https://jaideep-aher.github.io/horn-ok-please/")`, a title, a description of 155 characters or fewer, `openGraph` (type website, image og.png 1200×630 with alt text), `twitter: { card: "summary_large_image" }`, and `themeColor` #14132A.
  - Canonical URL without the query string.
- **Icons:** replace the default `favicon.ico` with a truck-art "OK" lotus mark. Ship `icon.svg` (existing; refine), `apple-icon.png` 180×180, `icon-192.png`, `icon-512.png`, and a `manifest.webmanifest`. Delete the create-next-app SVGs.
- **Poster QR:** encodes `https://jaideep-aher.github.io/horn-ok-please/?src=poster`.
  - The site reads `src` only to optionally show a "Welcome from the poster" one-liner. No visit counting or analytics (decision recorded).
  - Generate the QR with error correction level M, at least 3cm printed, and test it with two phones.
  - Add a `/qr/` page variant? No: one URL keeps it simple.

---

## 6. Performance budget

- **LCP < 2.0s** on a Moto G Power-class phone with simulated 4G (Lighthouse mobile default). CLS < 0.05, INP < 200ms, TBT < 200ms.
- **JS:** at most 90 KB gz first-load for `/`, at most 30 KB gz per lazily loaded interactive island. Use `next/dynamic` for the painter, compare slider, photo gallery and charts, triggered on near-viewport.
- **Fonts:** at most 120 KB woff2 above the fold. Load Nastaliq only on demand.
- **Images** (`unoptimized` export, so pre-process): `web/scripts/optimize-images.mjs` (sharp) converts `public/**/*.png|jpg` into `.avif` (q 50) and `.webp` (q 72) at widths 480/960/1440. Write `public/img-manifest.json` with width, height and blurhash/LQIP.
  - A `<Picture>` component emits `<picture>` with `srcset`/`sizes`, explicit width and height, `loading="lazy"`, and `decoding="async"`, except for the hero.
  - Hero: `fetchpriority="high"`, plus `<link rel="preload" as="image" imagesrcset=... type="image/avif">` in the head (basePath-prefixed).
  - Budget: hero at most 120 KB AVIF at 960w, and each other image at most 80 KB.
- **Data:** `pilot.json` is 172 KB. Don't ship it whole. Build-time imports should pick only the fields used. Total `/data` loaded on first paint should be 0 bytes, because the numbers are in the HTML.
- No third-party requests at all (fonts are self-hosted, with no analytics or CDNs).

---

## 7. Accessibility checklist (WCAG 2.2 AA)

- [ ] Landmarks: `header`, `nav` (in-page section links), `main`, `footer`. One h1, and headings in order.
- [ ] Skip link to `#studio` (exists) plus a skip link to `#findings`.
- [ ] Text contrast at least 4.5:1, large text and UI parts at least 3:1, using the tokens in §2 only. Marigold is never text on paper.
- [ ] Focus visible: 3px peacock outline with a 2px offset on paper, marigold on night. Focus is never hidden by the sticky sheet (2.4.11 Focus Not Obscured).
- [ ] Target size at least 24×24 CSS px (2.5.8). The design goal is 44px.
- [ ] Dragging alternative (2.5.7): the compare slider is a range input, so keys and taps work. Plus three snap buttons (Clean / Half / Painted).
- [ ] `lang="mr"`, `lang="hi"` or `lang="ur" dir="rtl"` on every non-English span, including phrase chips, alt text fragments and table cells.
- [ ] Every image has alt text that states the scene and the painted text. Decorative motifs use `aria-hidden`.
- [ ] Heatmaps: hatching pattern plus text summary. Charts have an adjacent `<table>` with caption and `scope` headers.
- [ ] `aria-live="polite"` for painter results and the slider decision. No live region spam during count-up.
- [ ] Reduced motion honoured everywhere. No autoplay video. Nothing flashes.
- [ ] Zoom to 200% and a 320px reflow without horizontal scroll (except the thumbnail rail).
- [ ] Forms and controls have visible labels. Toggle buttons use `aria-pressed`. Radio groups use arrow-key navigation.
- [ ] Links are descriptive (no "here"). External links are marked.
- [ ] axe-core reports 0 violations (serious or critical fail CI). A manual VoiceOver iOS pass and a TalkBack pass happen once before the expo.

---

## 8. QA plan

**Additions to the `web` job in `.github/workflows/ci.yml`.** Only `web/` and that workflow file change.
```yaml
      - name: Build (Pages basePath)
        run: npm run build
        env: { NEXT_PUBLIC_BASE_PATH: /horn-ok-please }
      - name: Claims trace
        run: node scripts/check-claims.mjs
      - name: Serve out/ under basePath
        run: |
          mkdir -p /tmp/site && cp -r out /tmp/site/horn-ok-please
          npx --yes http-server /tmp/site -p 4173 -s &
          npx --yes wait-on http://127.0.0.1:4173/horn-ok-please/
      - name: Link check
        uses: lycheeverse/lychee-action@v2
        with:
          args: --no-progress --base http://127.0.0.1:4173/horn-ok-please/ --exclude-loopback=false 'out/**/*.html'
          fail: true
      - name: Accessibility (axe via pa11y-ci)
        run: npx --yes pa11y-ci --config .pa11yci.json
      - name: Lighthouse CI
        run: npx --yes @lhci/cli@0.14 autorun --config=./lighthouserc.json
```
- `web/.pa11yci.json`: runner `axe`, url `http://127.0.0.1:4173/horn-ok-please/`, viewports 390×844 and 1280×800, standard WCAG2AA.
- `web/lighthouserc.json`:
  - url as above, mobile preset, 3 runs.
  - Assertions: `categories:performance >= 0.9`, `accessibility = 1`, `best-practices >= 0.95`, `seo >= 0.95`, `largest-contentful-paint <= 2000`, `cumulative-layout-shift <= 0.05`, `total-blocking-time <= 200`, `resource-summary:script:size <= 92160`.
- `npm run check:images` fails if any non-hero image is over 80 KB or the hero is over 120 KB, or if any image path lacks an AVIF variant.
- A guard script fails if any file under `public/photos/` lacks the `_blur` suffix or isn't listed as blurred in `photos.json`.
- External links (Commons, GitHub) are checked by lychee on a weekly schedule only, so flaky third-party sites don't block PRs.

**Manual verification (after each deploy, on the live Pages URL):**
- [ ] Open https://jaideep-aher.github.io/horn-ok-please/ and https://jaideep-aher.github.io/horn-ok-please/?src=poster: HTTP 200, correct title.
- [ ] Take full-page screenshots at desktop 1440×900 and mobile 390×844 (Playwright `scripts/screens.mjs`). Attach them to the PR and compare with the previous ones.
- [ ] Scan the printed poster QR with iPhone (Safari) and Android (Chrome) on cellular. The page should be usable in under 3 seconds.
- [ ] Painter: every phrase and plate shows an image (no broken icons). Live mode is absent.
- [ ] Slider: drag with touch, use arrow keys, and check the VoiceOver readout.
- [ ] Heatmap toggles on and off. The pattern is visible in grayscale (DevTools emulate achromatopsia).
- [ ] Every `<Source>` chip opens a JSON that contains the shown value.
- [ ] Share the URL in Slack/iMessage and check that the OG card shows the image and title (use opengraph.xyz as well).
- [ ] Spot-check that photos are blurred: plates and faces are unreadable at 200% zoom.
- [ ] Check reduced-motion (OS setting) and dark mode.

---

## 9. Implementation PR breakdown

Sequential: each PR is based on the previous one and only starts after the prerequisite changes land on main.

1. **PR1: Build-time data + Source pattern**
   - Files: `src/app/page.tsx`, `src/lib/data.ts` (new), `src/components/source.tsx` (new), `src/lib/format.ts`, `scripts/check-claims.mjs`, `scripts/data-map.json`, `scripts/claims-allow.json`, `package.json` scripts.
   - Accept: numbers appear in `out/index.html`. `check-claims` passes, and fails when a number is hand-edited. Data files hash-match `eval/**/results`.
2. **PR2: Visual system**
   - Files: `src/app/layout.tsx` (next/font: Noto Serif Devanagari, Noto Sans, Noto Sans Devanagari, lazy Noto Nastaliq Urdu), `src/app/globals.css` (tokens, type scale, light/dark), `components/action-chip.tsx` (icon + word), `components/ui/*`.
   - Accept: the token contrast table is reproduced in a unit test (`scripts/contrast.test.mjs`) and passes AA. No default create-next-app assets remain.
3. **PR3: Story order + hook**
   - Files: `components/exhibit.tsx` (reorder to hook → painter → see → findings → limits → about; old round reports go into `<details>` under Findings), `components/hero.tsx` (paint-stroke SVG, new copy), `components/site-header.tsx` (section nav).
   - Accept: the reduced-motion snapshot shows the painted title. h1 is real text. Lighthouse a11y = 100.
4. **PR4: Images pipeline + Picture**
   - Files: `scripts/optimize-images.mjs`, `public/img-manifest.json`, `components/picture.tsx`, hero preload in `layout.tsx`, all `<img>` replaced.
   - Accept: LCP ≤ 2.0s in LHCI mobile. No image over budget. CLS ≤ 0.05.
5. **PR5: Painter + compare slider + heatmap**
   - Files: `components/painter.tsx`, `components/compare-slider.tsx` (new), `components/see-panel.tsx`, `components/photo-gallery.tsx` (6×6 hatch, `lang="ur" dir="rtl"`).
   - Accept: works with only the keyboard and only touch. `aria-live` announces results. Heatmap text summaries are present. pa11y 0 errors.
6. **PR6: Findings cards**
   - Files: `components/finding-card.tsx` (new), `components/findings.tsx`, `components/round3-report.tsx` (dot plot + table), Gemini card conditional on `gemini.json`.
   - Accept: count-up runs only when in view and once. Its screen-reader value is final. Every numeral has a `data-source`. No card renders for missing data.
7. **PR7: OG, metadata, icons, QR**
   - Files: `src/app/opengraph-image.tsx` or `scripts/make-og.mjs`, `layout.tsx` metadata, `src/app/icon.svg`, `apple-icon.png`, `manifest.webmanifest`, `public/` cleanup, `poster/` QR URL note (doc only).
   - Accept: `out/og.png` is 1200×630 and under 300 KB. The OG validator shows a large card. The QR URL resolves with 200.
8. **PR8: QA gates in CI**
   - Files: `.github/workflows/ci.yml` (web job steps above), `web/.pa11yci.json`, `web/lighthouserc.json`, `web/scripts/screens.mjs`, `web/scripts/check-blur.mjs`.
   - Accept: CI is green on main, and a deliberately broken link, contrast problem or untraced number makes it red (shown in the PR description).
   - **Alternative:** land this PR first as non-blocking (`continue-on-error`), then flip it to blocking here.

## Decisions (recorded 2026-10-18)
- **Pages on a private repo:** Jay has GitHub Pro, so Pages deploys from the private repo. GitHub blob links in `<Source>` and the Sources list stay hidden (`NEXT_PUBLIC_REPO_PUBLIC=false`) until the repo is public. Deployed `/data/*.json` links are always shown.
- **`?src=poster`:** no visit counting or analytics of any kind. The parameter may only toggle a "Welcome from the poster" line.
- **Alba:** the Duke AIPI 2025 hackathon extension (see §1).
