# Site

Static Next.js export. From this directory:

```bash
npm ci
npm run dev
```

`npm run build` writes `out/`. On Vercel, set the project root to `web`, the build command to `npm run build`, and the output directory to `out`. No environment variables are required.

Pictures live in `public/` as real files: illustrated scenes under `public/stimuli` and explanation frames under `public/xai`. Commons photographs are withheld; `public/photos` is empty until painted registration numbers and phone numbers are covered.

Live mode is hidden unless the build sets `NEXT_PUBLIC_LIVE_MODE=1`. That dialog keeps a key in the browser only. It is not part of the scored counts.
