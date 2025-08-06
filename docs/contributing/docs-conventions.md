# Documentation Style Guide (DOCS_STYLE)

## Introduction

This guide defines conventions for Meridian Runtime's documentation to ensure the content renders correctly in both GitHub and our MkDocs Material site, remains consistent, and is easy to maintain.

### Scope

- Applies to all Markdown files in `docs/`.
- Complements project-wide standards in `CONTRIBUTING` and the `M99` plan.
- Use these rules for new pages and when editing existing content.

## Code Blocks

Use MkDocs Material features to make examples clear, skimmable, and copy‑paste‑ready.

### Languages

- Always specify a language for fenced blocks (`bash`, `python`, `yaml`, `toml`, `json`, `text`).
- Keep commands copy‑paste‑ready (no shell prompts like `$`).

### Inline Code

- Wrap all code, commands, file paths, and data references in backticks (`) when not in code blocks.
- This includes: function names, class names, file paths, command names, configuration values, etc.

**Examples:**

- Use `uv run python` instead of uv run python
- Use `examples/sentiment/main.py` instead of examples/sentiment/main.py
- Use `MessageType.DATA` instead of MessageType.DATA
- Use `--human` flag instead of --human flag

### Tabs (parallel examples)

Use tabbed blocks for multi-language or platform variants.

=== "Bash"
    ```bash
    uv lock
    uv sync
    uv run pytest -q
    ```

=== "PowerShell"
    ```powershell
    uv lock
    uv sync
    uv run pytest -q
    ```

### Line numbers and highlights

- Add `linenums` for long code (> ~8 lines) or when referencing specific lines.
- Use `hl_lines` to draw attention to critical lines.

```python linenums="1" hl_lines="5 12"
from meridian.core.policies import Latest

def build_graph(sg):
    # Connect producer to consumer; keep only the latest on overflow
    sg.connect(("producer","out"), ("consumer","in"), capacity=16, policy=Latest())
    return sg
```

### Titles (filename/context)

- Use `title="path/to/file.py"` to orient readers.

```python title="examples/hello_graph/main.py"
from meridian.core import Message, MessageType
# ...
```

### Collapsible blocks

- Collapse long, ancillary snippets (logs, full configs) with callouts.

??? note "Full error output (click to expand)"
    ```text
    <REDACTED ERROR OUTPUT>
    ...
    ```

### Diffs (before/after)

- Use `diff` fences to show changes succinctly.

```diff
- sg.connect(("prod","out"), ("cons","in"), capacity=16)
+ sg.connect(("prod","out"), ("cons","in"), capacity=16, policy=Latest())
```

### Commands vs output

- Use `bash` for commands and `text` for output; label with `title` when helpful.

```bash title="Run tests"
uv run pytest -q
```

```text title="Expected output (abridged)"
================== test session starts ==================
collected 34 items
...
```

### Privacy and safety

- Never include secrets or PII in code/output.
- Redact with `<REDACTED>` or placeholders like `PLACEHOLDER`, `TOKEN`, or `CHECKSUM(...)`.
- Prefer structure/log keys and counts over payload contents in examples.

**Do**

- Use separate blocks when switching languages.
- Keep examples minimal and runnable.

**Don't**

- Use bare ``` without a language.
- Mix multiple languages in one block.

## Visual Separators

Use a consistent horizontal rule to avoid linter ambiguity and ensure portability.

**Allowed**

- Three hyphens on their own line (`---`):
  ---

**Forbidden**

- Triple asterisk (`***`)
- Raw HTML `<hr>`

**Do**

- Prefer headings (H2/H3) or admonitions over separators where possible.
- Use separators sparingly to break large pages into readable sections.
- Ensure blank lines around separators for clarity.

## Internal Links

Internal links must work in both GitHub preview and MkDocs. Use short, local relative paths from the current file.

### Patterns

- Link to pages in the same folder:
  `./quickstart.md`
- Link to pages in subfolders:
  `./contributing/CONTRIBUTING.md`
- Link to sibling pages when in subfolders:
  `../roadmap/governance-and-overview.md`

### Anchors

- Use GitHub/MkDocs-style heading anchors, which are case-insensitive, dashed, and stripped of punctuation:
  `./patterns.md#backpressure-and-overflow`

**Do**

- Prefer local, relative links (`./` or `../`) rather than site-root or absolute URLs.
- Validate link targets exist and headings are accurate.
- Cross-link to canonical pages to avoid duplication (e.g., link to API for semantics definitions, Patterns for examples).

**Don't**

- Use `../docs/` in links.
- Rely on `/absolute` paths that don't resolve in GitHub preview.

## Headings and Structure

Use a single H1 at the top of each page. Keep a logical, shallow structure for scanability.

### Hierarchy

- H1: Page title (one per page)
- H2: Primary sections
- H3: Subsections when necessary
- Avoid going deeper than H3 unless absolutely required

### Spacing and layout

- Ensure a blank line before and after headings.
- Keep paragraphs short and focused.
- Group related content with H2s; use separators (`---`) only when they add clarity.

### Tone and content

- Lead with a concise summary.
- Prefer examples after a short explanation.
- Defer deeper narratives to linked pages to prevent duplication.

## Checklists and Lists

Follow GitHub Flavored Markdown (GFM) task list formatting for compatibility with MkDocs Material.

### Task lists

- Use a single space after the brackets:
    - [ ] Item not done
    - [x] Item done

### Bullets and numbering

- Use `-` for unordered lists.
- Use standard `1.` numbering for ordered lists (let Markdown auto-number subsequent items).

### Spacing and indentation

- Leave a blank line before lists if preceded by a paragraph or heading.
- **Always leave a blank line before any list** (bulleted or numbered) to ensure proper rendering.
- Indent nested lists by exactly four spaces per level for proper rendering.
- For multi-paragraph list items, indent subsequent paragraphs by two spaces (keep bullet/number indent at four spaces).
- For tabbed code blocks inside lists, keep the list indentation at four spaces and the tab content indented accordingly.

**Don't**

- Misalign brackets or use inconsistent spacing in checklists.
- Nest checklists more than two levels deep.

## Admonitions and Callouts

Use MkDocs Material admonition syntax where helpful.

### Examples

!!! note
    Short clarifications or helpful context.

!!! warning
    Caveats, footguns, or compatibility notes.

!!! tip
    Practical advice and best practices.

**Do**

- Keep admonitions concise and actionable.
- Prefer admonitions for important notices over bold inline text.

**Don't**

- Overuse admonitions; they are for emphasis, not general layout.

## Examples and Snippets

Make examples minimal and runnable when possible.

### Python

- Prefer short classes and functions with clear intent.
- Show imports aligned with published API paths.
- Avoid unnecessary dependencies or setup in snippets.
- When demonstrating runtime behavior, prefer module execution style:

  ```bash
  uv run python -m examples.hello_graph.main
  ```

### Shell

- Use `uv` for all developer commands (lint, type, test).
- Avoid interactive prompts and environment-specific shortcuts.

### Consistency

- Match message/schema APIs consistently:
    - `Message(type=MessageType.DATA, payload=...)`
    - `PortSpec("in", int)`
- Align examples with API overview and Patterns pages.

## Content Hygiene and Style

### Language

- Prefer active voice and short sentences.
- Avoid jargon; define terms once, then reuse consistently.
- Use consistent terminology: node, edge, subgraph, scheduler, message.
- Skip unnecessary fluff and focus on concise documentation to get users going quickly.

### Privacy and safety

- **Don't** include secrets, tokens, or PII in examples.
- Redact or use placeholders for any sensitive content in logs or configs.

### Maintenance

- Cross-link instead of duplicating content.
- Keep pages focused; split overly long pages when needed.
- Ensure headings, anchors, and links remain accurate after edits.

## Page Metadata and Navigation

We avoid YAML front‑matter for standard docs pages. Page titles are the H1. Navigation is controlled by `mkdocs.yml`.

**Do**

- Add new pages under `docs/` and register them in `mkdocs.yml`.
- Link new pages from `index.md` or relevant sections to make them discoverable.

**Don't**

- Add front‑matter at the top of docs pages unless explicitly needed for a special plugin.

## Review Checklist (Author's Quick Pass)

- [x] One H1 at top; heading hierarchy is H2/H3 and consistent
- [x] All code fences have language tags
- [x] No `***` separators in content (use `---`)
- [x] Internal links are relative and valid in GitHub and MkDocs
- [x] Examples are minimal, correct, and copy‑paste‑able
- [x] Admonitions (if any) are valid and justified
- [x] No secrets, PII, or sensitive payloads in examples
- [x] Page cross-links to canonical references (Quickstart, API, Patterns, Observability, Troubleshooting)

## References

- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- [GitHub Flavored Markdown (GFM)](https://github.github.com/gfm/)
- [Project Quickstart](../getting-started/quickstart.md)
- [API Overview](../reference/api.md)
- [Patterns](../concepts/patterns.md)
- [Observability](../concepts/observability.md)
- [Troubleshooting](../support/TROUBLESHOOTING.md)

By following these conventions, we keep Meridian Runtime's docs predictable, readable, and contributor‑friendly across GitHub and the generated site.
