# Open Source Release Checklist

## Before Pushing

1. Confirm `.env` is not staged.
2. Confirm private folders are ignored:
   - `Personal_Info/`
   - `Plans/`
   - `Daily_Logs/`
   - `Projects/`
3. Verify the bot runs from a clean clone with repository-relative paths.
4. Decide on a license and add a `LICENSE` file before publishing.
5. Review `University/` content and make sure you are allowed to publish it.

## Recommended Commands

```bash
git status
python3 -m json.tool command.json > /dev/null
python3 -m py_compile Documents/scripts/project_paths.py
python3 -m py_compile Documents/scripts/mansur_bot.py
python3 -m py_compile Documents/scripts/get_chat_id.py
python3 -m py_compile Documents/scripts/send_file.py
python3 -m py_compile Documents/scripts/test_quiz_loader.py
```

## Codex Auth

Codex authentication is local. Do not commit any auth state.

```bash
codex login
codex login status
```

Or:

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
codex login status
```
