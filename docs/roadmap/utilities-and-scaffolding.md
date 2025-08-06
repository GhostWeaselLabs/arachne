# Milestone M5: Utilities and Scaffolding

## EARS Tasks and Git Workflow

**Branch name**: `feature/m5-utilities-scaffolding`

**EARS loop**

- Explore: identify id/time/validation helpers and scaffolding CLI needs
- Analyze: finalize templates and validation contracts
- Implement: utils (ids, time, validation) and generators (node, subgraph)
- Specify checks: unit tests for utils; e2e generation smoke tests
- Commit after each major step

**Git commands**

```bash
git checkout -b feature/m5-utilities-scaffolding
git add -A && git commit -m "feat(utils): add ids and time helpers"
git add -A && git commit -m "feat(utils): add validation helpers for ports/graphs"
git add -A && git commit -m "feat(scaffold): generate_node CLI with templates and tests"
git add -A && git commit -m "feat(scaffold): generate_subgraph CLI with templates and tests"
git add -A && git commit -m "test(utils,scaffold): unit and generation smoke tests"
git push -u origin feature/m5-utilities-scaffolding
```

Open PR early; keep commits small and focused

---

## Overview

Provide developer utilities and project scaffolding to accelerate consistent, SRP/DRY-friendly node and subgraph creation. Utilities include time helpers, correlation ID generation, and validation helpers for types and graph contracts. Scaffolding includes generators to create node and subgraph skeletons conforming to Meridian conventions (~200 lines/file, explicit typing, docstrings, tests).

## EARS Requirements

- The system shall provide utilities for correlation ID generation, monotonic time, and validation helpers for ports and graphs.
- The system shall provide scaffolding commands to generate node and subgraph templates with recommended structure, typing, and tests.
- When a developer runs a generator, the system shall create files in the appropriate package locations with consistent naming and boilerplate.
- If the target path already exists, the generator shall abort with a clear error or optionally support a `--force` overwrite flag.
- The system shall maintain SRP/DRY by keeping generator templates small, focused, and extensible.
- Where Pydantic is enabled, the utilities shall support optional schema adapters without hard dependencies.

## Deliverables

- `src/meridian/utils/ids.py`
    - Correlation ID generator (uuid4, ULID-like or short lexicographic-friendly option).
    - Functions: `new_trace_id()`, `new_id(prefix: str | None = None)`.
- `src/meridian/utils/time.py`
    - Monotonic and wall-clock helpers: `now_ts_ms()`, `now_rfc3339()`, `monotonic_ns()`.
    - Simple duration context manager: `time_block()` → elapsed seconds.
- `src/meridian/utils/validation.py`
    - Port and schema validation helpers.
    - Graph wiring checks (non-exhaustive): type compatibility, unique names, positive capacities.
    - Optional Pydantic adapter interface for schema validation.
- `src/meridian/scaffolding/generate_node.py`
    - CLI for generating node modules with class skeleton, typing, docstring, and unit test.
    - Options: `--name`, `--package`, `--inputs`, `--outputs`, `--dir`, `--force`, `--include-tests`.
- `src/meridian/scaffolding/generate_subgraph.py`
    - CLI for generating subgraph modules with exposed ports, connect wiring stubs, and tests.
    - Options: `--name`, `--package`, `--dir`, `--force`, `--include-tests`.
- Template files (inline within generators or small template directory) that adhere to ~200 lines/file guidance.
- Documentation updates:
    - Scaffolding usage guide with examples.
    - Utilities reference and examples for ids/time/validation.

---

## Scaffolding CLI Design

### Command: `generate_node.py`

**Usage**:

```bash
uv run python -m meridian-runtime.scaffolding.generate_node --name PriceNormalizer --package meridian-runtime.nodes --inputs in:dict --outputs out:dict --dir src --include-tests
```

**Behavior**:

- Create `src/meridian-runtime/nodes/price_normalizer.py` with class `PriceNormalizer(Node)`.
- Generate stubs for `name()`, `inputs()`, `outputs()`, `on_start()`, `on_message()`, `on_tick()`, `on_stop()`, and emit usage.
- Create `tests/unit/test_price_normalizer.py` with a smoke test and typing checks.

**Options**:

- `--name`: PascalCase class name (required).
- `--package`: dot path under `src/` (default: `meridian-runtime.nodes`).
- `--inputs`/`--outputs`: comma-separated list of port:type pairs (e.g., `in:int,in2:dict`).
- `--dir`: base directory (default: `src`).
- `--force`: overwrite files if they exist.
- `--include-tests`: create test file under `tests/unit/`.
- `--policy`: default edge policy hints in docstring.

**Validation**:

- Validate package path exists or create it.
- Validate name convention and no conflicts unless `--force`.

### Command: `generate_subgraph.py`

**Usage**:
```bash
uv run python -m meridian-runtime.scaffolding.generate_subgraph --name MarketPipeline --package meridian-runtime.subgraphs --dir src --include-tests
```

**Behavior**:

- Create `src/meridian-runtime/subgraphs/market_pipeline.py` with class `MarketPipeline(Subgraph)`.
- Add stubs for `add_node`/`connect` wiring, `expose_input`/`expose_output`, and `validate` call.
- Create `tests/integration/test_market_pipeline.py` with a smoke run (scheduler added by M6/M7 examples).

**Options**:

- `--name`: PascalCase class name (required).
- `--package`: dot path under `src/` (default: `meridian-runtime.subgraphs`).
- `--dir`: base directory (default: `src`).
- `--force`: overwrite files if they exist.
- `--include-tests`: create integration test file.

---

## Template Content Guidelines

### Node template highlights

- Class name, module docstring, explicit typing on all public methods.
- Minimal logic in constructor; keep runtime behavior in lifecycle hooks.
- Docstring sections: Purpose, Ports, Policies, Error handling, Observability.
- Emit helper usage with type-safe `Message` creation.
- Example usage snippet at bottom (guarded by `if __name__ == "__main__":`) optional and disabled by default.

### Subgraph template highlights

- Composition pattern with TODO comments to wire nodes.
- Expose input/output patterns with clear type comments.
- `validate()` invocation and simple example of capacity/policy configuration in comments.

### Tests templates

- Unit test for node: lifecycle calls, `on_message` invoked, basic emit/contract checks.
- Integration test for subgraph: basic wiring validation; optional scheduler smoke deferred to M6/M7 but included as TODO.
- Coverage-friendly structure and markers (pytest).

---

## Utilities Design

### `ids.py`

```python
new_trace_id() -> str
    Default: UUID4 hex without dashes for compactness.
    Alternative: ULID-like for lexicographic sort (optional; documented).

new_id(prefix: str | None = None) -> str
    If prefix given, return f"{prefix}_{uuid4hex}".
```

**Non-cryptographic note**: Document use; not for security tokens.

### `time.py`

```python
now_ts_ms() -> int: epoch milliseconds.
now_rfc3339() -> str: RFC3339 with UTC.
monotonic_ns() -> int: time.monotonic_ns passthrough.
time_block(name: str | None = None) -> context manager:
    Yields start time, on exit returns elapsed seconds (float) to caller's variable if used with `as`.
    Keep allocation minimal; no logging here (observed by M4 metrics).
```

### `validation.py`

```python
validate_ports(node) -> list[Issue]
    Ensure declared inputs/outputs are PortSpec or supported types.

validate_connection(src_spec, dst_spec) -> Issue | None
    Schema compatibility rules (basic isinstance/typing checks).

validate_graph(subgraph) -> list[Issue]
    Check unique names, capacities > 0, policies not None, and no dangling exposures.

pydantic adapter (optional):
    Protocol class for `validate_payload(model, payload)` if model provided; otherwise no-op.

Issue dataclass:
    severity: "error" | "warning"
    message: str
    location: tuple or string identifier (node, port, edge)
```

---

## Developer Experience and Conventions

- Generated code adheres to ~200 lines/file guideline; split if expanding.
- All public methods strictly typed; docstrings explain contracts.
- Avoid runtime reflection/magic in templates; keep it explicit and easy to test.
- Scaffolding creates minimal viable code that passes lint, type-check, and unit tests immediately.

---

## Documentation Updates

- `docs/scaffolding.md`:
    - Installation/usage examples for both generators.
    - Naming conventions: snake_case modules, PascalCase classes, short port names.
    - Examples of input/output type annotations and Policies usage in docstrings.
- `docs/utils.md`:
    - Quick reference for ids/time/validation helpers.
    - Examples integrating `validate_graph` into CI or pre-commit.

---

## Testing Strategy

### Unit tests

- `ids_test.py`: ensure unique IDs; prefix handling; basic performance sanity.
- `time_test.py`: monotonic returns increasing values; RFC3339 formatting; `time_block` duration sanity.
- `validation_test.py`: correct issue detection for incompatible port types, duplicate names, and invalid capacities.
- `scaffolding_node_test.py`: invoke generator in a temp dir; validate created files compile and basic test template runs.
- `scaffolding_subgraph_test.py`: invoke generator; validate module import and integration test template created.

### Integration tests

- End-to-end generation + run lint/type/tests:
    - Programmatically generate a node and subgraph; run ruff, mypy (on generated code subset), and pytest for generated tests.
- Optional: Use `uv run` to simulate actual developer flow in CI (documented, not mandatory in M5).

---

## Performance and Maintainability

- Keep generators small; prefer inline string templates with format variables or a tiny templating helper (no heavy templating engines).
- Limit options to what's needed; extensibility via comments and TODOs in generated files.
- Ensure templates are idempotent and deterministic to ease code review in downstream projects.

---

## Acceptance Criteria

- Utilities (ids, time, validation) implemented with docstrings and typing; unit tests pass and coverage ≥90% for utilities.
- Scaffolding CLIs generate runnable, typed skeletons and tests that pass lint/type/test on creation.
- Documentation for scaffolding and utilities is added and links from README.
- Generated files conform to conventions (naming, typing, ~200 lines guidance).
- CI includes a job that runs scaffolding smoke tests in a temporary workspace.

---

## Risks and Mitigations

- **Overly complex generators**:
    - Mitigation: Keep to a small option set; expose extensibility via TODOs, not codegen complexity.
- **Template drift with core API evolution**:
    - Mitigation: Add tests that validate generated code imports core APIs; update alongside breaking changes.
- **Hidden dependency on optional libs (Pydantic)**:
    - Mitigation: Use adapters; document optional installation for schema validation.

---

## Out of Scope (deferred)

- Cookiecutter or large templating frameworks.
- IDE project files or editor integrations.
- Auto-registration or plugin discovery mechanisms.

---

## Traceability

- Implements Technical Blueprint Implementation Plan M5.
- Satisfies EARS requirements for utilities and scaffolding, enabling consistent developer experience and faster adoption.

---

## Checklist

- [ ] `ids.py` implemented and tested
- [ ] `time.py` implemented and tested
- [ ] `validation.py` implemented and tested
- [ ] `generate_node.py` CLI implemented; templates and tests
- [ ] `generate_subgraph.py` CLI implemented; templates and tests
- [ ] Docs updated: `scaffolding.md`, `utils.md`, README references
- [ ] CI smoke test for scaffolding end-to-end