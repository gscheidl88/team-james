# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | yes       |
| < 0.1   | no        |

## Supported Scope

This repository is intended to publish reusable framework assets only.

Out of scope for publication:

- personal notes in `PersonalNotes/`
- local vault metadata in `.obsidian/`
- generated reviews, telemetry, and temp files
- real credentials and environment secrets

## Reporting a Vulnerability

If you discover a security issue, do not publish secrets or exploit details in public issues.

Preferred reporting path:

1. Use GitHub private vulnerability reporting / security advisories for this repository when available.
2. If private reporting is unavailable, contact the maintainer privately through the repository owner's GitHub profile before opening any public issue.

Include:

- affected file, workflow, or tool
- impact summary
- reproduction steps
- whether secrets or private operator data may be exposed
- any suggested mitigation or temporary workaround

Response targets:

- acknowledgement within 5 business days
- triage update within 10 business days when reproduction is possible
- coordinated disclosure target of 90 days unless a different timeline is agreed explicitly

## Secret handling

- Never commit real tokens, cookies, or credentials.
- Prefer Windows Credential Manager for durable local secrets.
- Treat `.env` as local-only and excluded from version control.
- Keep example env files free of inline commentary on secret lines.

## Disclosure Policy

- Do not open public issues for unpatched vulnerabilities.
- Do not include live credentials, access tokens, cookies, or exploit payloads in reports.
- After a fix is available, public disclosure should describe impact and remediation without exposing unnecessary operator detail.

## Hardening Expectations

- Keep `.gitignore` aligned with `config/repo-publish-inventory.json`.
- Keep publish-facing examples sanitized.
- Do not use personal notes or generated review output as canonical repository inputs.
