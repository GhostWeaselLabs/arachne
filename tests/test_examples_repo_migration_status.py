import io
import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest

# Import the script module
import scripts.migrate_with_history as mwh


def test_status_reporter_json_event_fields(capsys: Any) -> None:
    reporter = mwh.StatusReporter(json_output=True, verbose=0)
    reporter.log(
        "info",
        phase="prepare",
        step="preflight",
        message="starting",
        repo="local",
        progress={"current": 1, "total": 3, "pct": 33.3},
        duration_ms=12,
        commit="deadbeef",
    )
    out = capsys.readouterr().out.strip()
    evt = json.loads(out)
    assert evt["level"] == "info"
    assert evt["phase"] == "prepare"
    assert evt["step"] == "preflight"
    assert evt["message"] == "starting"
    assert evt["repo"] == "local"
    assert evt["progress"]["current"] == 1
    assert evt["duration_ms"] == 12
    assert evt["commit"] == "deadbeef"
    assert "timestamp" in evt


def test_status_reporter_plain_banner(capsys: Any) -> None:
    reporter = mwh.StatusReporter(json_output=False, verbose=0)
    reporter.banner("migrate", "split", "examples -> branch")
    out = capsys.readouterr().out
    assert "MIGRATE" in out
    assert "split" in out
    assert "examples" in out


def test_checkpoint_roundtrip(tmp_path: Path) -> None:
    data = {"completed": ["preflight"], "split_branches": ["subtree-split/examples"]}
    status_file = tmp_path / "status.json"
    mwh.save_checkpoint(status_file, data)
    loaded = mwh.load_checkpoint(status_file)
    assert loaded == data


@pytest.mark.timeout(2)
def test_heartbeat_emits_lines(capsys: Any) -> None:
    reporter = mwh.StatusReporter(json_output=False, verbose=0)
    reporter.start_heartbeat(interval_seconds=0.02)
    # Wait long enough to trigger at least one heartbeat
    time.sleep(0.05)
    reporter.stop_heartbeat()
    out = capsys.readouterr().out
    assert "heartbeat" in out


@pytest.mark.timeout(10)
def test_script_dry_run_with_json_and_status_file(tmp_path: Path) -> None:
    status_file = tmp_path / "status.json"
    # Simulate execution in dry-run with JSON output
    argv_backup = sys.argv
    stdout_backup = sys.stdout
    try:
        sys.argv = [
            "migrate_with_history.py",
            "--dry-run",
            "--remote-name",
            "origin",
            "--prefix",
            "examples",
            "--prefix",
            "notebooks",
            "--target-branch",
            "main",
            "--json",
            "--status-file",
            str(status_file),
        ]
        sys.stdout = io.StringIO()
        rc = mwh.main()
        output = sys.stdout.getvalue().strip().splitlines()
    finally:
        sys.argv = argv_backup
        sys.stdout = stdout_backup
    assert rc == 0
    assert status_file.exists()
    # Should have produced JSON lines
    assert len(output) > 0
    # The last line should be a summary event
    last = json.loads(output[-1])
    assert last["step"] == "summary"
    assert last["phase"] == "integrate"
