# Cloud sessions follow the owner's focus clock (11 Nov 2026)

Cloud sessions do not run the Mac's `~/.claude/hooks/focus-guard.py`, so `.claude/hooks/focus-guard-cloud.py` (registered in `.claude/settings.json` as a `UserPromptSubmit` hook) applies the same rule here. It acts only when `CLAUDE_CODE_REMOTE=true`; on the Mac it exits at once.

```mermaid
flowchart LR
  P[Prompt arrives] --> R{Cloud session?}
  R -- no, Mac --> OK[Pass: Mac guard handles it]
  R -- yes --> A{Automated message?}
  A -- yes --> OK2[Pass]
  A -- no --> N{21:30 to 07:00 Eastern?}
  N -- yes --> OK2
  N -- no --> J{Job pipeline work?}
  J -- yes --> OK2
  J -- no --> F{First prompt of the session?}
  F -- yes, no job words --> B[Block: send one application first]
  F -- yes, job words --> JG[Session model judges]
  F -- no, running work --> OK2
  F -- no, new side project words --> JG
```
Why this picture: the only thing ever stopped is a typed prompt that starts new side work in the day; everything else flows through.

- Time is `America/New_York`, because cloud runs in UTC.
- `applied <n> <companies>` earns 15 min per application for that cloud session (cap 120).
- Any error in the hook exits 0, so it can never break Claude Code.
- Test: `python3 .claude/hooks/test_focus_guard_cloud.py` (runs only this guard, not the app suite).
