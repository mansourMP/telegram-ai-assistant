# Security Policy

## Supported Scope

This repository contains a Telegram bot and helper scripts for markdown-backed study content.

## Reporting

Do not open a public issue for:
- exposed tokens
- `.env` leaks
- Telegram bot credentials
- personal data accidentally committed

Instead, rotate the affected credential immediately and remove it from version control history before publishing.

## Operational Guidance

- Keep `.env` local only.
- Review `git status` before every commit.
- Do not publish private study content or personal files unless you intend to make them public.
