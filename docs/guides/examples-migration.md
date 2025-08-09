---
title: Examples & Notebooks Migration
description: Examples and notebooks have moved to the meridian-runtime-examples repository.
tags:
  - migration
  - examples
  - notebooks
---

# Examples & Notebooks Migration

Examples and notebooks were moved out of this repository into a dedicated public repository: `meridian-runtime-examples`.

## Why the change?

- Keep this repo focused on the core runtime.
- Enable faster iteration and community contributions for examples.
- CI separation: example execution and notebook checks run in their own pipelines.

## Where to find them

- Repository: `https://github.com/GhostWeaselLabs/meridian-runtime-examples`
- Layout:
  - `examples/`: runnable Python example projects
  - `notebooks/`: tutorials, interactive examples, and research notebooks

## How to run an example

```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
python examples/hello_graph/main.py
```

Using `uv`:

```bash
git clone https://github.com/GhostWeaselLabs/meridian-runtime-examples.git
cd meridian-runtime-examples
uv run python examples/sentiment/main.py --human --timeout-s 6.0
```

## Contributing examples

- Open PRs against `meridian-runtime-examples`.
- Follow the repo README for contribution and CI details.

## Impact on docs and CI

- Documentation in this repo links to the external examples repo.
- This repo no longer runs example smoke tests; those are handled in the examples repo CI.


