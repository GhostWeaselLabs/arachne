# Documentation Style Guide (DOCS_STYLE)

This guide defines conventions for Meridian Runtime’s documentation to ensure the content renders correctly in both GitHub and our MkDocs Material site, remains consistent, and is easy to maintain.

Scope
- Applies to all Markdown files in docs/.
- Complements project-wide standards in CONTRIBUTING and the M99 plan.
- Use these rules for new pages and when editing existing content.

***

1) Fenced Code Blocks

Always specify a language for fenced code blocks. This improves rendering, syntax highlighting, and snippet tooling.

Common languages
- bash: shell commands (avoid prompts like `$`)
- python: code examples and snippets
- yaml / toml / json: configuration
- text: plain output or logs when no syntax is appropriate

Examples
```bash
uv lock
uv sync
uv run pytest
```

```python
from meridian.core import Message, MessageType

msg = Message(type=MessageType.DATA, payload=42)
```

```yaml
site_name: Meridian Runtime
theme:
  name: material
```

Do
- Keep commands copy‑paste‑ready (no shell prompts).
- Use separate blocks when switching languages.
- Prefer minimal runnable examples for Python.

Don’t
- Use bare ``` without a language.
- Mix multiple languages in one block.

***

2) Visual Separators

Never use “---” as a visual separator in page content. It can be misinterpreted as YAML front‑matter. Use one of the following:

Preferred
- Three asterisks on their own line:
  ***
- HTML hr tag:
  <hr>

Do
- Use separators sparingly to break large pages into readable sections.
- Ensure blank lines around separators for clarity.

Don’t
- Use triple dashes (“---”) anywhere except in a YAML front‑matter context (which we generally avoid in docs pages).

***

3) Internal Links

Internal links must work in both GitHub preview and MkDocs. Use short, local relative paths from the current file.

Patterns
- Link to pages in the same folder:
  ./quickstart.md
- Link to pages in subfolders:
  ./contributing/CONTRIBUTING.md
- Link to sibling pages when in subfolders:
  ../plan/M0-governance-and-overview.md

Anchors
- Use GitHub/MkDocs-style heading anchors, which are case-insensitive, dashed, and stripped of punctuation:
  ./patterns.md#backpressure-and-overflow

Do
- Prefer local, relative links (./ or ../) rather than site-root or absolute URLs.
- Validate link targets exist and headings are accurate.
- Cross-link to canonical pages to avoid duplication (e.g., link to API for semantics definitions, Patterns for examples).

Don’t
- Use “../docs/” in links.
- Rely on “/absolute” paths that don’t resolve in GitHub preview.

***

4) Headings and Structure

Use a single H1 at the top of each page. Keep a logical, shallow structure for scanability.

Hierarchy
- H1: Page title (one per page)
- H2: Primary sections
- H3: Subsections when necessary
- Avoid going deeper than H3 unless absolutely required

Spacing and layout
- Ensure a blank line before and after headings.
- Keep paragraphs short and focused.
- Group related content with H2s; use separators (*** or <hr>) only when they add clarity.

Tone and content
- Lead with a concise summary.
- Prefer examples after a short explanation.
- Defer deeper narratives to linked pages to prevent duplication.

***

5) Checklists and Lists

Follow GitHub Flavored Markdown (GFM) task list formatting for compatibility with MkDocs Material.

Task lists
- Use a single space after the brackets:
  - [ ] Item not done
  - [x] Item done

Bullets and numbering
- Use “- ” for unordered lists.
- Use standard “1.” numbering for ordered lists (let Markdown auto-number subsequent items).

Spacing
- Leave a blank line before lists if preceded by a paragraph.
- For multi-paragraph list items, indent subsequent paragraphs by two spaces.

Don’t
- Misalign brackets or use inconsistent spacing in checklists.
- Nest checklists more than two levels deep.

***

6) Admonitions and Callouts

Use MkDocs Material admonition syntax where helpful.

Examples
!!! note
    Short clarifications or helpful context.

!!! warning
    Caveats, footguns, or compatibility notes.

!!! tip
    Practical advice and best practices.

Do
- Keep admonitions concise and actionable.
- Prefer admonitions for important notices over bold inline text.

Don’t
- Overuse admonitions; they are for emphasis, not general layout.

***

7) Examples and Snippets

Make examples minimal and runnable when possible.

Python
- Prefer short classes and functions with clear intent.
- Show imports aligned with published API paths.
- Avoid unnecessary dependencies or setup in snippets.
- When demonstrating runtime behavior, prefer module execution style:
  ```bash
  uv run python -m examples.hello_graph.main
  ```

Shell
- Use uv for all developer commands (lint, type, test).
- Avoid interactive prompts and environment-specific shortcuts.

Consistency
- Match message/schema APIs consistently:
  - Message(type=MessageType.DATA, payload=...)
  - PortSpec("in", int)
- Align examples with API overview and Patterns pages.

***

8) Content Hygiene and Style

Language
- Prefer active voice and short sentences.
- Avoid jargon; define terms once, then reuse consistently.
- Use consistent terminology: node, edge, subgraph, scheduler, message.

Privacy and safety
- Don’t include secrets, tokens, or PII in examples.
- Redact or use placeholders for any sensitive content in logs or configs.

Maintenance
- Cross-link instead of duplicating content.
- Keep pages focused; split overly long pages when needed.
- Ensure headings, anchors, and links remain accurate after edits.

***

9) Page Metadata and Navigation

We avoid YAML front‑matter for standard docs pages. Page titles are the H1. Navigation is controlled by mkdocs.yml.

Do
- Add new pages under docs/ and register them in mkdocs.yml.
- Link new pages from index.md or relevant sections to make them discoverable.

Don’t
- Add front‑matter at the top of docs pages unless explicitly needed for a special plugin.

***

10) Review Checklist (Author’s Quick Pass)

- [ ] One H1 at top; heading hierarchy is H2/H3 and consistent
- [ ] All code fences have language tags
- [ ] No “---” separators in content (use *** or <hr>)
- [ ] Internal links are relative and valid in GitHub and MkDocs
- [ ] Examples are minimal, correct, and copy‑paste‑able
- [ ] Admonitions (if any) are valid and justified
- [ ] No secrets, PII, or sensitive payloads in examples
- [ ] Page cross-links to canonical references (Quickstart, API, Patterns, Observability, Troubleshooting)

***

11) References

- MkDocs Material: https://squidfunk.github.io/mkdocs-material/
- GitHub Flavored Markdown (GFM): https://github.github.com/gfm/
- Project Quickstart: ./../quickstart.md
- API Overview: ./../api.md
- Patterns: ./../patterns.md
- Observability: ./../observability.md
- Troubleshooting: ./../troubleshooting.md

By following these conventions, we keep Meridian Runtime’s docs predictable, readable, and contributor‑friendly across GitHub and the generated site.