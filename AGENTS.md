# AGENTS.md

## Project Overview

This repository hosts a Telegram-based study bot and supporting study-content tooling.

Primary runtime entrypoint:
- `src/mansur_bot/bot.py`

Primary content sources:
- `examples/content/` (Default)
- Configurable via `UNIVERSITY_DIR` environment variable.

## Code Structure

- `src/mansur_bot/`: Main application logic
- `scripts/`: Helper scripts (PDF generation, stats)
- `tests/`: Unit tests
- `examples/`: Sample content

## Working Rules

- Prefer changes that keep the bot portable. Do not reintroduce absolute local filesystem paths.
- Treat `University/` markdown files as source content, not generated files.
- Avoid changing assignment/question numbering unless the task explicitly requires reorganization.
- Keep Telegram output plain-text safe. Markdown parsing is intentionally avoided in the quiz path.
- If a question has pickable options, preserve it as MCQ. Do not silently convert it to study-only.

## Validation

Before finalizing changes, run:

```bash
make test
```

## Open-Source Constraints

- Never commit `.env` or personal folders.
- Do not depend on `/Users/...` paths.
- Document required credentials in `.env.example`, not in code.
