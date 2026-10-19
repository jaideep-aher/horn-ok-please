# Site

Static Next.js export. From this directory:

```bash
npm ci
npm run dev
```

`npm run build` writes `out/`. On Vercel, set the project root to `web`, the build command to `npm run build`, and the output directory to `out`. No environment variables are required.

Pictures live in `public/` as real files: illustrated scenes under `public/stimuli`, explanation frames under `public/xai`, and blurred Commons photographs under `public/photos`.

Live mode is hidden unless the build sets `NEXT_PUBLIC_LIVE_MODE=1`. That dialog keeps a key in the browser only. It is not part of the scored counts.
