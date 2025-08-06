---
title: About This Documentation
description: How this documentation is organized and how to navigate it effectively.
tags:
  - about
  - documentation
  - navigation
---

# About This Documentation

This documentation provides comprehensive information about **Meridian Runtime**, organized to help you get started quickly and dive deeper as needed.

## Quick links

- Repo: https://github.com/GhostWeaselLabs/meridian-runtime
- Documentation: https://ghostweasellabs.github.io/meridian-runtime/
- MkDocs config: [mkdocs.yml](https://github.com/ghostweasellabs/meridian-runtime/blob/main/mkdocs.yml)

## Structure

- index.md — Docs homepage (user-facing landing page)
- getting-started/
    - quickstart.md — 60-second setup and first run
    - guide.md — Full setup, verification, development loop, and Hello Graph
- examples/
    - index.md — Examples overview
    - sentiment.md — Control-plane preemption, priorities, mixed capacities
    - streaming-coalesce.md — Deterministic coalescing under pressure
- concepts/
    - about.md — This page
    - patterns.md — Common design patterns and guidance
    - observability.md — Logs, metrics, tracing
- reference/
    - api.md — API reference and primitives
- contributing/
    - guide.md — Contribution guidelines and release process
    - RELEASING.md — Release process
    - docs-conventions.md — Docs style and conventions
- support/
    - troubleshooting.md — Common issues and fixes
    - how-to-report-issues.md — Reporting guidance
    - troubleshooting-legacy.md — Legacy notes
- roadmap/ — Governance and roadmap documents

## How the site is built and deployed

- The site is built by a GitHub Actions workflow on every push to main.
- Dependencies are pinned and installs are cached for faster, deterministic builds.
- Pages is configured to deploy from GitHub Actions (not from a branch).

## Contributing to docs

1. Make changes to files under `docs/` or update the nav in `mkdocs.yml`.
2. Run locally with:
     - `uv lock && uv sync`
     - `uv run mkdocs serve`
3. Verify links and nav. Keep pages concise and task‑focused.
4. Open a PR. On merge to `main`, the site auto‑deploys.

## Authoring guidelines

- Keep pages scoped: one concept or task per page.
- Prefer short intros, then examples and practical steps.
- Cross‑link related topics (Quickstart, Guide, Examples, API, Patterns).
- Use consistent terminology: node, edge, subgraph, scheduler, message.
- Include minimal runnable snippets where helpful.

## Adding new pages

1. Create a new `.md` under `docs/`.
2. Add it to the nav in `mkdocs.yml` under an appropriate section.
3. If the page is user‑facing, link it from `index.md` or a relevant section.
4. For examples, add a page under `docs/examples/` and link it from `docs/examples/index.md`.

## Issues and support

- Open issues at: https://github.com/GhostWeaselLabs/meridian-runtime/issues
- See support guidance in: [report an issue](../support/HOW-TO-REPORT-ISSUES.md)

Thank you for helping improve the Meridian Runtime docs! 