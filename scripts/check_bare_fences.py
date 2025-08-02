#!/usr/bin/env python3
"""
check_bare_fences.py

A small, robust checker for Markdown files that flags "bare" triple-backtick
code fences (``` with no language specifier). This avoids brittle shell-based
regex and quoting issues in local hooks.

Usage (pre-commit):
  - Configure a local pre-commit hook to run:
      entry: python3 scripts/check_bare_fences.py
    and scope it to docs/**/*.md (or whichever paths you prefer).

Behavior:
  - Scans provided file paths (intended to be Markdown).
  - Reports any line where a fence line is exactly ```.
  - Exits non-zero if any violations are found.

Notes:
  - This does not validate language names. It only ensures a language is present.
  - It ignores closing fences like ``` that are intended to end a block, because
    the rule is to always use language on the opening fence, not the closing.
    However, since static analysis cannot always perfectly distinguish opens
    from closes, the heuristic is:
      * If a line is exactly "```", it is considered a violation.
      * Typical closing fences appear as "```" as well; the simple rule is:
        always specify a language on the opening fence to avoid this violation.
  - If you need stricter behavior (e.g., pairing fences), extend the heuristic.

Exit codes:
  0 - success (no bare fences found)
  1 - failure (one or more bare fences found)
  2 - invalid invocation (no files provided)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


def find_bare_fences(path: Path) -> List[Tuple[int, str]]:
    """
    Return a list of (line_number, line_content) where a bare fence is found.

    A "bare fence" is a line that, after stripping trailing newline characters,
    is exactly three backticks with no language specifier.
    """
    results: List[Tuple[int, str]] = []
    try:
        # Use strict UTF-8 with fallback to ignoring errors to avoid crashes
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            for i, raw in enumerate(f, start=1):
                line = raw.rstrip("\n")
                # Normalize whitespace; we consider only pure "```" as bare
                if line.strip() == "```":
                    results.append((i, line))
    except Exception as e:
        print(f"ERROR: Could not read {path}: {e}", file=sys.stderr)
    return results


def iter_md_files(files: Iterable[str]) -> Iterable[Path]:
    """
    Yield all Markdown file paths from an iterable of file paths.
    """
    for p in files:
        path = Path(p)
        # Only check existing markdown files
        if path.suffix.lower() in {".md", ".markdown"} and path.exists():
            yield path


def main(argv: Iterable[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Detect bare triple-backtick code fences in Markdown files."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Markdown files to check (usually provided by your VCS/hooks).",
    )
    args = parser.parse_args(list(argv))

    if not args.files:
        print("No files provided to check_bare_fences.py", file=sys.stderr)
        return 2

    total_failures = 0
    for md_path in iter_md_files(args.files):
        violations = find_bare_fences(md_path)
        if violations:
            total_failures += len(violations)
            print(f"{md_path}: bare code fence(s) without language:")
            for line_no, content in violations:
                # Show a caret-style indicator without leaking entire file
                print(f"  line {line_no}: {repr(content)}")
            print("  Hint: specify a language, e.g., ```text or ```bash, etc.")

    if total_failures:
        print(
            f"Found {total_failures} bare code fence(s) without language.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
