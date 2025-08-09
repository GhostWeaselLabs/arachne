from __future__ import annotations

import argparse
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path(".meridian") / "artifacts" / "migration-backups"


def run_git(*args: str) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def ensure_clean_working_tree() -> None:
    status = run_git("status", "--porcelain=v1")
    if status:
        raise SystemExit("Working tree not clean. Commit or stash changes before backup.")


def archive_paths(paths: list[Path], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out_path, "w:gz") as tar:
        for p in paths:
            if p.exists():
                tar.add(str(p), arcname=str(p))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create backups and anchors for examples/notebooks migration")
    parser.add_argument("--tag-prefix", default="migration/pre-split", help="Prefix for git tag anchors")
    parser.add_argument("--paths", nargs="*", default=["examples", "notebooks"], help="Paths to back up")
    args = parser.parse_args()

    ensure_clean_working_tree()

    dt = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    tag = f"{args.tag_prefix}/{dt}"

    # Create a lightweight tag as an anchor point
    run_git("tag", tag)

    # Create tar.gz of requested paths
    paths = [Path(p) for p in args.paths]
    out_path = BACKUP_DIR / f"working-tree-{dt}.tar.gz"
    archive_paths(paths, out_path)

    print(f"[backup] created git tag: {tag}")
    print(f"[backup] archive written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
