from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="only check drift; non-zero on drift")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    # Placeholder: implement real sync by comparing pyproject/uv.lock with main repo
    if args.check:
        print("[sync] dependency drift check: OK (stub)")
        return 0
    print("[sync] sync not implemented yet; this is a stub")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
