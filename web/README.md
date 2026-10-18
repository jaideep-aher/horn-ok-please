# Horn OK Please site

Static explainer for the study in the repository root. It reads `public/data/summary.json`, which `python poster/publish.py` copies from `eval/results/summary.json`. Until that file has attack-success rows, the page says the rates are pending.

```bash
npm ci
npm run dev -- -H 0.0.0.0 -p 43123
```

`npm run build` writes a static export to `out/`. The pictures are the symlink `public/stimuli` → `../../eval/stimuli`.
