from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MigrationConfig:
    remote_name: str
    remote_url: str | None
    prefixes: list[str]
    target_branch: str
    dry_run: bool


def run_git(args: list[str], cwd: Path | None = None, dry_run: bool = False) -> str:
    cmd = ["git", *args]
    if dry_run:
        print("$", " ".join(cmd))
        return ""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed (code {proc.returncode})\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc.stdout.strip()


def check_clean_working_tree(dry_run: bool = False) -> None:
    status = run_git(["status", "--porcelain=v1"], dry_run=dry_run)
    if not dry_run and status.strip():
        raise SystemExit("Working tree is not clean. Commit or stash changes before migration.")


def get_git_root(dry_run: bool = False) -> Path:
    out = run_git(["rev-parse", "--show-toplevel"], dry_run=dry_run)
    return Path(out) if out else Path.cwd()


def create_split_branch(prefix: str, split_branch: str, dry_run: bool) -> None:
    # Create a subtree split branch containing only the history for the prefix
    run_git(["subtree", "split", f"--prefix={prefix}", "-b", split_branch], dry_run=dry_run)


def ensure_remote(remote_name: str, remote_url: str | None, dry_run: bool) -> None:
    remotes = run_git(["remote"], dry_run=dry_run)
    if not dry_run and remote_name in remotes.split():
        return
    if remote_url is None:
        raise SystemExit(f"Remote '{remote_name}' does not exist. Provide --remote-url to add it.")
    run_git(["remote", "add", remote_name, remote_url], dry_run=dry_run)


def push_split(remote: str, split_branch: str, target_branch: str, dry_run: bool) -> None:
    run_git(["push", remote, f"{split_branch}:{target_branch}"], dry_run=dry_run)


def delete_branch(branch: str, dry_run: bool) -> None:
    run_git(["branch", "-D", branch], dry_run=dry_run)


def parse_args() -> MigrationConfig:
    parser = argparse.ArgumentParser(description="Migrate directories with history to a new repository using git subtree split")
    parser.add_argument("--remote-name", default="examples-origin", help="Name for the remote to push splits to")
    parser.add_argument("--remote-url", default=None, help="URL of the new repository remote (required if remote does not exist)")
    parser.add_argument("--prefix", action="append", dest="prefixes", default=["examples", "notebooks"], help="Directory prefix to migrate (repeatable)")
    parser.add_argument("--target-branch", default="main", help="Branch name on the target repository")
    parser.add_argument("--no-dry-run", action="store_true", help="Actually run git commands instead of printing them")
    args = parser.parse_args()
    return MigrationConfig(
        remote_name=args.remote_name,
        remote_url=args.remote_url,
        prefixes=args.prefixes,
        target_branch=args.target_branch,
        dry_run=not args.no_dry_run,
    )


def main() -> int:
    config = parse_args()
    try:
        # Basic preflight checks
        if shutil.which("git") is None:
            raise SystemExit("git is required on PATH")
        check_clean_working_tree(dry_run=config.dry_run)
        repo_root = get_git_root(dry_run=config.dry_run)
        print(f"[migration] repository root: {repo_root}")

        # Ensure remote
        ensure_remote(config.remote_name, config.remote_url, dry_run=config.dry_run)

        # For each prefix, create a split branch and push
        split_branches: list[str] = []
        for prefix in config.prefixes:
            split_branch = f"subtree-split/{prefix.replace('/', '_')}"
            print(f"[migration] creating split for '{prefix}' -> '{split_branch}'")
            create_split_branch(prefix, split_branch, dry_run=config.dry_run)
            split_branches.append(split_branch)

        for split_branch in split_branches:
            print(f"[migration] pushing '{split_branch}' to '{config.remote_name}:{config.target_branch}'")
            push_split(config.remote_name, split_branch, config.target_branch, dry_run=config.dry_run)

        # Cleanup local split branches
        for split_branch in split_branches:
            print(f"[migration] cleaning up local branch '{split_branch}'")
            delete_branch(split_branch, dry_run=config.dry_run)

        print("[migration] done")
        if config.dry_run:
            print("[migration] dry run: no changes were made")
        return 0
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
