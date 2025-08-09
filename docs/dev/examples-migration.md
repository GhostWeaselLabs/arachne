# Examples & Notebooks Migration Runbook

This document describes a safe procedure to migrate `examples/` and `notebooks/` into a dedicated repository while preserving history.

## Prerequisites

- Clean working tree in `meridian-runtime`
- New empty repository created, e.g. `GhostWeaselLabs/meridian-runtime-examples`
- Obtain its Git URL (SSH or HTTPS)

## Dry run

```
uv run python scripts/migrate_with_history.py --remote-name examples-origin --remote-url git@github.com:GhostWeaselLabs/meridian-runtime-examples.git
```

## Execute

Once validated, run with `--no-dry-run`:

```
uv run python scripts/migrate_with_history.py --remote-name examples-origin --remote-url git@github.com:GhostWeaselLabs/meridian-runtime-examples.git --no-dry-run
```

This will:
- Create subtree splits for `examples/` and `notebooks/`
- Push the split history to the target repository `main` branch
- Clean up local split branches

## Post-migration

- Verify history in the new repository
- Open PRs to remove `examples/` and `notebooks/` from the main repo
- Update documentation links and add migration notes
