# Meridian Runtime Documentation

This directory contains the source for the Meridian Runtime documentation site, published via GitHub Pages and built with MkDocs Material.

Quick links
- Live site: https://ghostweasellabs.github.io/meridian-runtime/
- MkDocs config: ../mkdocs.yml
- Repo: https://github.com/GhostWeaselLabs/meridian-runtime

Structure
- index.md — Docs homepage (user-facing landing page)
- quickstart.md — Install, setup, and first run
- api.md — API reference and primitives
- patterns.md — Common design patterns and guidance
- observability.md — Logs, metrics, tracing
- troubleshooting.md — Common issues and fixes
- contributing/ — Contribution guidelines and release process
- plan/ — Governance and roadmap documents
- support/ — How to report issues and templates

How the site is built and deployed
- The site is built by a GitHub Actions workflow on every push to main.
- Dependencies are pinned and pip installs are cached for faster, deterministic builds.
- Pages is configured to deploy from GitHub Actions (not from a branch).

Contributing to docs
1) Make changes to files in this directory or update the nav in mkdocs.yml.
2) Run locally with:
   - uv lock && uv sync
   - uv run mkdocs serve
3) Verify links and nav. Keep pages concise and task-focused.
4) Open a PR. On merge to main, the site auto-deploys.

Authoring guidelines
- Keep pages scoped: one concept or task per page.
- Prefer short intros, then examples and practical steps.
- Cross-link related topics (Quickstart, API, Patterns).
- Use consistent terminology: node, edge, subgraph, scheduler, message.
- Include minimal runnable snippets where helpful.

Adding new pages
1) Create a new .md under docs/.
2) Add it to the nav in mkdocs.yml under an appropriate section.
3) If the page is user-facing, link it from index.md or a relevant section.

Issues and support
- Open issues at: https://github.com/GhostWeaselLabs/meridian-runtime/issues
- See support guidance in: support/HOW-TO-REPORT-ISSUES.md

Thank you for helping improve the Meridian Runtime docs!