from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class MigrationConfig:
    remote_name: str
    remote_url: str | None
    prefixes: list[str]
    target_branch: str | None
    dry_run: bool
    verbose: int
    debug: bool
    json_output: bool
    status_file: Path | None
    resume: bool


class StatusReporter:
    def __init__(self, json_output: bool, verbose: int) -> None:
        self.json_output = json_output
        self.verbose = verbose
        self._last_activity = time.monotonic()
        self._stop_event = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None

    def start_heartbeat(self, interval_seconds: float = 30.0) -> None:
        if self._heartbeat_thread is not None:
            return

        def run() -> None:
            while not self._stop_event.wait(interval_seconds):
                now = time.monotonic()
                if now - self._last_activity >= interval_seconds:
                    self.log("info", phase="heartbeat", step="tick", message="no visible activity; still running")

        self._heartbeat_thread = threading.Thread(target=run, name="status-heartbeat", daemon=True)
        self._heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        self._stop_event.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=1.0)

    def touch(self) -> None:
        self._last_activity = time.monotonic()

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log(self, level: str, *, phase: str, step: str, message: str, repo: str | None = None, progress: dict | None = None, duration_ms: int | None = None, commit: str | None = None) -> None:
        self.touch()
        if self.json_output:
            event = {
                "timestamp": self._timestamp(),
                "level": level,
                "phase": phase,
                "step": step,
                "message": message,
            }
            if repo:
                event["repo"] = repo
            if progress is not None:
                event["progress"] = progress
            if duration_ms is not None:
                event["duration_ms"] = duration_ms
            if commit is not None:
                event["commit"] = commit
            print(json.dumps(event))
        else:
            prefix = f"[{phase}:{step}]"
            print(prefix, message)

    def banner(self, phase: str, step: str, detail: str | None = None) -> None:
        msg = f"{phase.upper()} ▸ {step}"
        if detail:
            msg += f" — {detail}"
        self.log("info", phase=phase, step=step, message=msg)


def run_git(args: list[str], reporter: StatusReporter | None = None, cwd: Path | None = None, dry_run: bool = False, stream: bool = False) -> str:
    cmd = ["git", *args]
    if dry_run:
        print("$", " ".join(cmd))
        return ""
    if stream:
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert proc.stdout is not None
        output_lines: list[str] = []
        for line in proc.stdout:
            output_lines.append(line)
            sys.stdout.write(line)
            sys.stdout.flush()
            if reporter is not None:
                reporter.touch()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed (code {proc.returncode})")
        return "".join(output_lines).strip()
    else:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if reporter is not None:
            reporter.touch()
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed (code {proc.returncode})\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
        return proc.stdout.strip()


def check_clean_working_tree(reporter: StatusReporter, dry_run: bool = False) -> None:
    status = run_git(["status", "--porcelain=v1"], reporter=reporter, dry_run=dry_run)
    if not dry_run and status.strip():
        raise SystemExit("Working tree is not clean. Commit or stash changes before migration.")


def get_git_root(reporter: StatusReporter, dry_run: bool = False) -> Path:
    out = run_git(["rev-parse", "--show-toplevel"], reporter=reporter, dry_run=dry_run)
    return Path(out) if out else Path.cwd()


def create_split_branch(prefix: str, split_branch: str, reporter: StatusReporter, dry_run: bool, stream: bool) -> None:
    # Create a subtree split branch containing only the history for the prefix
    run_git(["subtree", "split", f"--prefix={prefix}", "-b", split_branch], reporter=reporter, dry_run=dry_run, stream=stream)


def ensure_remote(remote_name: str, remote_url: str | None, reporter: StatusReporter, dry_run: bool) -> None:
    remotes = run_git(["remote"], reporter=reporter, dry_run=dry_run)
    if not dry_run and remote_name in (remotes.split() if remotes else []):
        return
    if dry_run:
        if remote_url is None:
            reporter.log("info", phase="prepare", step="ensure_remote", message=f"dry-run: assuming remote '{remote_name}' exists")
            return
        # Simulate adding remote
        run_git(["remote", "add", remote_name, remote_url], reporter=reporter, dry_run=True)
        return
    if remote_url is None:
        raise SystemExit(f"Remote '{remote_name}' does not exist. Provide --remote-url to add it.")
    run_git(["remote", "add", remote_name, remote_url], reporter=reporter, dry_run=False)


def push_split(remote: str, split_branch: str, target_branch: str, reporter: StatusReporter, dry_run: bool) -> None:
    run_git(["push", remote, f"{split_branch}:{target_branch}"], reporter=reporter, dry_run=dry_run)


def delete_branch(branch: str, reporter: StatusReporter, dry_run: bool) -> None:
    run_git(["branch", "-D", branch], reporter=reporter, dry_run=dry_run)


def parse_args() -> MigrationConfig:
    parser = argparse.ArgumentParser(description="Migrate directories with history to a new repository using git subtree split")
    parser.add_argument("--remote-name", default="examples-origin", help="Name for the remote to push splits to")
    parser.add_argument("--remote-url", default=None, help="URL of the new repository remote (required if remote does not exist)")
    parser.add_argument("--prefix", action="append", dest="prefixes", default=None, help="Directory prefix to migrate (repeatable)")
    parser.add_argument("--target-branch", default=None, help="Branch name on the target repository (default: use split branch name)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--dry-run", dest="dry_run_flag", action="store_true", help="Simulate commands without changing repositories")
    group.add_argument("--no-dry-run", dest="no_dry_run_flag", action="store_true", help="Actually run git commands instead of printing them")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase log verbosity (repeatable)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output including stack traces")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Emit NDJSON events for logs")
    parser.add_argument("--status-file", type=Path, default=None, help="Path to a status checkpoint file for resume")
    parser.add_argument("--resume", action="store_true", help="Resume from the last checkpoint in --status-file")
    args = parser.parse_args()
    # Default to dry-run unless explicitly disabled
    dry_run = True
    if getattr(args, "no_dry_run_flag", False):
        dry_run = False
    if getattr(args, "dry_run_flag", False):
        dry_run = True
    prefixes = args.prefixes if args.prefixes is not None else ["examples", "notebooks"]
    return MigrationConfig(
        remote_name=args.remote_name,
        remote_url=args.remote_url,
        prefixes=prefixes,
        target_branch=args.target_branch,
        dry_run=dry_run,
        verbose=args.verbose,
        debug=args.debug,
        json_output=args.json_output,
        status_file=args.status_file,
        resume=args.resume,
    )


def load_checkpoint(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def save_checkpoint(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
    except Exception:
        # Best-effort; do not fail migration on checkpoint issues
        pass


def main() -> int:
    config = parse_args()
    reporter = StatusReporter(json_output=config.json_output, verbose=config.verbose)
    reporter.start_heartbeat()
    start_time = time.monotonic()
    checkpoint: dict = {}
    if config.status_file is not None and config.resume:
        checkpoint = load_checkpoint(config.status_file)
    try:
        # Basic preflight checks
        if shutil.which("git") is None:
            raise SystemExit("git is required on PATH")
        reporter.banner("prepare", "preflight", "checking tooling and working tree")
        check_clean_working_tree(reporter, dry_run=config.dry_run)
        repo_root = get_git_root(reporter, dry_run=config.dry_run)
        reporter.log("info", phase="prepare", step="preflight", message=f"repository root: {repo_root}")

        # Persist checkpoint
        if config.status_file is not None:
            checkpoint.setdefault("completed", [])
            if "preflight" not in checkpoint["completed"]:
                checkpoint["completed"].append("preflight")
                save_checkpoint(config.status_file, checkpoint)

        # Ensure remote
        if not (config.resume and "ensure_remote" in checkpoint.get("completed", [])):
            reporter.banner("prepare", "ensure_remote", f"{config.remote_name}")
            ensure_remote(config.remote_name, config.remote_url, reporter, dry_run=config.dry_run)
            if config.status_file is not None:
                checkpoint.setdefault("completed", []).append("ensure_remote")
                save_checkpoint(config.status_file, checkpoint)

        # For each prefix, create a split branch and push
        split_branches: list[str] = checkpoint.get("split_branches", [])
        completed_splits: set[str] = set(checkpoint.get("completed_splits", []))
        for prefix in config.prefixes:
            split_branch = f"subtree-split/{prefix.replace('/', '_')}"
            if split_branch in completed_splits:
                continue
            reporter.banner("migrate", "split", f"{prefix} -> {split_branch}")
            # Stream output for subtree split on verbosity >= 1
            stream = config.verbose >= 1 and not config.json_output
            t0 = time.monotonic()
            create_split_branch(prefix, split_branch, reporter, dry_run=config.dry_run, stream=stream)
            dt_ms = int((time.monotonic() - t0) * 1000)
            reporter.log("info", phase="migrate", step="split", message=f"created split {split_branch}", progress=None, duration_ms=dt_ms)
            split_branches.append(split_branch)
            if config.status_file is not None:
                checkpoint["split_branches"] = split_branches
                checkpoint.setdefault("completed_splits", []).append(split_branch)
                save_checkpoint(config.status_file, checkpoint)

        if not checkpoint.get("pushed", False):
            for split_branch in split_branches:
                target = config.target_branch or split_branch
                reporter.banner("migrate", "push", f"{split_branch} -> {config.remote_name}:{target}")
                push_split(config.remote_name, split_branch, target, reporter, dry_run=config.dry_run)
            if config.status_file is not None:
                checkpoint["pushed"] = True
                save_checkpoint(config.status_file, checkpoint)

        # Cleanup local split branches
        if not checkpoint.get("cleaned", False):
            for split_branch in split_branches:
                reporter.banner("integrate", "cleanup", f"{split_branch}")
                delete_branch(split_branch, reporter, dry_run=config.dry_run)
            if config.status_file is not None:
                checkpoint["cleaned"] = True
                save_checkpoint(config.status_file, checkpoint)

        total_ms = int((time.monotonic() - start_time) * 1000)
        reporter.log("info", phase="integrate", step="summary", message=f"done in {total_ms} ms; prefixes={len(config.prefixes)}")
        if config.dry_run:
            reporter.log("info", phase="integrate", step="summary", message="dry run: no changes were made")
        return 0
    except SystemExit as exc:
        reporter.log("error", phase="error", step="system_exit", message=str(exc))
        if config.debug:
            raise
        return 2
    except Exception as exc:  # noqa: BLE001
        reporter.log("error", phase="error", step="unexpected", message=f"{type(exc).__name__}: {exc}")
        if config.debug:
            raise
        return 1
    finally:
        reporter.stop_heartbeat()


if __name__ == "__main__":
    raise SystemExit(main())
