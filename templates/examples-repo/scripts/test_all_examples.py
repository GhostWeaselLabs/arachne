from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"


def discover_example_entrypoints() -> list[Path]:
    entrypoints: list[Path] = []
    if not EXAMPLES_DIR.exists():
        return entrypoints
    for sub in EXAMPLES_DIR.iterdir():
        if sub.is_dir():
            main_py = sub / "main.py"
            if main_py.exists():
                entrypoints.append(main_py)
    return entrypoints


def run_entrypoint(path: Path) -> None:
    print(f"[examples] running: {path}")
    proc = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)


def test_all_examples() -> None:
    """Pytest entry: executes each example's main.py if present."""
    for entry in discover_example_entrypoints():
        run_entrypoint(entry)


if __name__ == "__main__":
    test_all_examples()
