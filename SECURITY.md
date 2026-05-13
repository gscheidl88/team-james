# Security Policy

## Supported scope

This repository is intended to publish reusable framework assets only.

Out of scope for publication:

- personal notes in `PersonalNotes/`
- local vault metadata in `.obsidian/`
- generated reviews, telemetry, and temp files
- real credentials and environment secrets

## Reporting

If you discover a security issue, do not publish secrets or exploit details in public issues.

Report with:

- affected file or tool
- impact summary
- reproduction steps
- whether secrets or private operator data may be exposed

## Secret handling

- Never commit real tokens, cookies, or credentials.
- Prefer Windows Credential Manager for durable local secrets.
- Treat `.env` as local-only and excluded from version control.
- Keep example env files free of inline commentary on secret lines.

## Hardening expectations

- Keep `.gitignore` aligned with `config/repo-publish-inventory.json`.
- Keep publish-facing examples sanitized.
- Do not use personal notes or generated review output as canonical repository inputs.
