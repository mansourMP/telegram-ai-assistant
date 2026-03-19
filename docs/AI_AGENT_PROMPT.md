# AI Agent Prompt

Use this prompt when delegating work on this repository to another AI coding agent:

```text
You are working on a Telegram study-bot repository.

Primary entrypoint:
- Documents/scripts/mansur_bot.py

Primary content files:
- University/Calculus/Calculus_Questions.md
- University/Economics/Exam_Prep.md

Your task:
1. Inspect the relevant files before proposing changes.
2. Do not introduce absolute filesystem paths.
3. Keep Telegram output plain-text safe; avoid Markdown parsing unless explicitly required.
4. If a question contains pickable options (A/B/C/D or A/B/C), preserve it as an MCQ.
5. Do not move or renumber assignments/questions unless the task explicitly asks for reorganization.
6. If you edit scripts, keep them portable and repository-relative.
7. After changes, run:
   - python3 -m py_compile Documents/scripts/mansur_bot.py
   - python3 -m py_compile Documents/scripts/get_chat_id.py
   - python3 -m py_compile Documents/scripts/send_file.py
   - python3 -m py_compile Documents/scripts/test_quiz_loader.py
8. Summarize what changed, what was verified, and any remaining risk.

Deliver:
- Minimal, correct code changes
- No secrets
- No placeholder TODOs unless explicitly requested
```

## Review Prompt

Use this when asking another agent for a review:

```text
Review this repo change like a strict production code reviewer.
Prioritize:
1. Behavioural regressions
2. Telegram formatting/runtime risks
3. Question parsing/classification mistakes
4. Portability issues (absolute paths, local-only assumptions)
5. Missing validation

Give findings first with file references, then a short summary.
```
