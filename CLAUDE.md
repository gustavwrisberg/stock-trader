# stock-trader

A daily paper trader. GitHub Actions runs `run.py` every weekday. The website in `docs/` reads `docs/data/dashboard.json`.

- The stock-analysis skill lives in `.claude/skills/stock-analysis`. Do not edit it; update it by re-copying from upstream and bumping `VERSION`.
- For a single-company deep dive, follow that skill's full workflow and save the report to `analyses/<TICKER>-analysis-<date>.md`. If the analysis raises a gate (see `score.py --explain gates`), add it to `config/flags.json` with evidence.
- Never hand-edit `data/` or `docs/data/`: they are bot output.
- Test changes offline with `python run.py --demo`, which writes to `demo/` and is gitignored.
- This is paper money and research, not investment advice. Keep that framing in anything user-facing.
