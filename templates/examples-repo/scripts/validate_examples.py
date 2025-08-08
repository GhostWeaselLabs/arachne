from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"


@dataclass
class ExampleValidationResult:
    path: str
    has_readme: bool
    has_main: bool


def validate_example_dir(example_dir: Path) -> ExampleValidationResult:
    return ExampleValidationResult(
        path=str(example_dir.relative_to(ROOT)),
        has_readme=(example_dir / "README.md").exists(),
        has_main=(example_dir / "main.py").exists(),
    )


def main() -> None:
    results = []
    if EXAMPLES_DIR.exists():
        for sub in EXAMPLES_DIR.iterdir():
            if sub.is_dir():
                results.append(validate_example_dir(sub).__dict__)
    print(json.dumps({"results": results}, indent=2))


if __name__ == "__main__":
    main()
