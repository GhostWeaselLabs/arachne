#!/usr/bin/env bash
set -euo pipefail

# Meridian Runtime - One-shot Verification Script
# Runs: smoke + critical integrations, short stress, observability, and coverage thresholds
# Provides clear PASS/FAIL output with summaries and guidance.
#
# Usage:
#   ./scripts/verify.sh
#   ./scripts/verify.sh --quick        # skip stress/soak
#   ./scripts/verify.sh --no-cov       # skip coverage enforcement
#   ./scripts/verify.sh --cov-thresh 80 90  # overall core thresholds override (overall core)
#   ./scripts/verify.sh --seed 1234    # deterministic seed
#
# Exit codes:
#   0 => PASS
#   1 => FAIL

# --- Configurable defaults ---
OVERALL_COV_THRESHOLD="${OVERALL_COV_THRESHOLD:-80}"  # percent
CORE_COV_THRESHOLD="${CORE_COV_THRESHOLD:-90}"        # percent
PYTEST="${PYTEST:-pytest}"
PYTHON="${PYTHON:-python}"
SEED="${SEED:-0}"
QUICK=0
RUN_COVERAGE=1
# Allow users to pass extra pytest args via env: PYTEST_ARGS

# Determine repo root (script can be invoked from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

# Colors
if [ -t 1 ]; then
  GREEN="\033[32m"
  RED="\033[31m"
  YELLOW="\033[33m"
  BLUE="\033[34m"
  BOLD="\033[1m"
  RESET="\033[0m"
else
  GREEN=""; RED=""; YELLOW=""; BLUE=""; BOLD=""; RESET=""
fi

log()  { echo -e "${BLUE}${1}${RESET}"; }
ok()   { echo -e "${GREEN}${1}${RESET}"; }
warn() { echo -e "${YELLOW}${1}${RESET}"; }
err()  { echo -e "${RED}${1}${RESET}" >&2; }

print_header() {
  echo -e "\n${BOLD}== $1 ==${RESET}\n"
}

usage() {
  cat <<EOF
Meridian Runtime - verify.sh

Runs smoke/integration, short stress, observability, and coverage thresholds with clear PASS/FAIL.

Options:
  --quick                 Skip stress and soak-like tests (fast verification).
  --no-cov                Skip coverage enforcement step.
  --cov-thresh O C        Set coverage thresholds (overall O%, core C%).
  --seed N                Set deterministic seed (default: ${SEED}).
  -h, --help              Show this help.

Environment:
  PYTEST                  Override pytest executable (default: pytest)
  PYTEST_ARGS             Extra args passed through to pytest
  OVERALL_COV_THRESHOLD   Override overall coverage threshold
  CORE_COV_THRESHOLD      Override core coverage threshold
EOF
}

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --quick) QUICK=1; shift ;;
    --no-cov) RUN_COVERAGE=0; shift ;;
    --cov-thresh)
      OVERALL_COV_THRESHOLD="${2:-$OVERALL_COV_THRESHOLD}"
      CORE_COV_THRESHOLD="${3:-$CORE_COV_THRESHOLD}"
      shift 3 ;;
    --seed) SEED="${2:-$SEED}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

# --- Pre-flight checks ---
print_header "Pre-flight"
if ! command -v "${PYTEST}" >/dev/null 2>&1; then
  err "pytest not found. Activate your venv or install dev deps."
  exit 1
fi

if [ ! -d "tests" ] || [ ! -d "src" ]; then
  err "This script must be run from the repository root (detected: ${REPO_ROOT})."
  exit 1
fi

ok "Using pytest: $(${PYTEST} --version 2>/dev/null | head -n1)"
ok "Seed: ${SEED}"
[ "${RUN_COVERAGE}" -eq 1 ] && ok "Coverage thresholds -> overall: ${OVERALL_COV_THRESHOLD}% | core: ${CORE_COV_THRESHOLD}%"

# Determinism and consistent hashing
export PYTHONHASHSEED="${SEED}"

# Accumulators
FAILURES=()

run_step() {
  local name="$1"
  shift
  print_header "${name}"
  set +e
  "$@"
  local rc=$?
  set -e
  if [ $rc -ne 0 ]; then
    err "${name}: FAILED (exit ${rc})"
    FAILURES+=("${name}")
  else
    ok "${name}: PASSED"
  fi
  return $rc
}

# Build a compact summary of failures
summarize() {
  echo
  if [ ${#FAILURES[@]} -eq 0 ]; then
    ok "All verification steps PASSED."
    exit 0
  fi
  err "Verification FAILED in ${#FAILURES[@]} step(s):"
  for f in "${FAILURES[@]}"; do
    err " - ${f}"
  done
  exit 1
}

# --- Steps ---

# 1) Smoke and critical integrations (must “just work”)
run_step "Smoke: unit + examples" \
  ${PYTEST} -q \
    tests/unit/test_smoke.py \
    tests/integration/test_examples_smoke.py \
    ${PYTEST_ARGS:-}

run_step "Integration: backpressure, priorities, mixed policies, shutdown" \
  ${PYTEST} -q \
    tests/integration/test_backpressure_end_to_end.py \
    tests/integration/test_priority_preemption_under_load.py \
    tests/integration/test_mixed_overflow_policies.py \
    tests/integration/test_shutdown_semantics.py \
    ${PYTEST_ARGS:-}

# 2) Observability and error isolation
run_step "Observability: logging/metrics/tracing + lifecycle error isolation" \
  ${PYTEST} -q \
    tests/unit/test_observability_logging.py \
    tests/unit/test_observability_metrics.py \
    tests/unit/test_observability_tracing.py \
    tests/unit/test_node_lifecycle_error_isolation.py \
    ${PYTEST_ARGS:-}

# 3) Short stress (timeboxed) to catch obvious regressions
if [ "${QUICK}" -eq 0 ]; then
  # Many stress tests support markers/filters; we run the core latency/throughput checks.
  run_step "Stress (short): throughput and loop latency budgets" \
    ${PYTEST} -q -k "throughput or latency or loop_latency" \
      tests/stress/test_throughput_and_latency.py \
      ${PYTEST_ARGS:-}
else
  warn "Skipping stress due to --quick"
fi

# 4) Coverage enforcement (overall + core)
if [ "${RUN_COVERAGE}" -eq 1 ]; then
  print_header "Coverage enforcement"
  # Remove any previous coverage artifacts so we read fresh data
  rm -f .coverage || true
  # Run full test subset for verification with coverage. Users can run the entire suite separately.
  # We run unit + integration selections to keep execution time reasonable while validating breadth.
  set +e
  ${PYTEST} \
    --maxfail=1 \
    --disable-warnings \
    --cov=src \
    --cov-report=term-missing \
    -q \
    tests/unit \
    tests/integration/test_backpressure_end_to_end.py \
    tests/integration/test_priority_preemption_under_load.py \
    tests/integration/test_mixed_overflow_policies.py \
    tests/integration/test_shutdown_semantics.py \
    ${PYTEST_ARGS:-}
  cov_rc=$?
  set -e

  if [ $cov_rc -ne 0 ]; then
    err "Coverage run failed. See output above."
    FAILURES+=("Coverage: run failed")
  else
    # Parse coverage from 'coverage report' which is more machine-friendly
    # We compute overall coverage from the summary line.
    # For core coverage, we approximate by filtering core modules under src/meridian (adjust path if needed).
    print_header "Coverage: parsing results"

    # Generate machine-friendly reports
    coverage report > /tmp/coverage_report.txt || true
    coverage xml -o /tmp/coverage.xml || true

    overall_cov="$(awk '/TOTAL/ {print $4}' /tmp/coverage_report.txt | tr -d '%')"
    if [[ -z "${overall_cov}" ]]; then
      warn "Unable to parse overall coverage from coverage report. Will not enforce."
      overall_cov="0"
    fi

    # Compute "core" coverage: sum statements and covered for core packages, then compute percentage.
    # Adjust the include pattern for your core modules if needed.
    core_stmt_total=0
    core_stmt_cov=0
    while IFS= read -r line; do
      # Expected format per file line: name stmts miss branch brpart cover%
      # We include src/ paths that represent core runtime (meridian or core modules).
      # Adjust pattern below if your package path differs.
      name="$(echo "$line" | awk '{print $1}')"
      if [[ "$name" == src/* ]]; then
        stmts="$(echo "$line" | awk '{print $2}')"
        miss="$(echo "$line" | awk '{print $3}')"
        # Basic sanity
        if [[ "$stmts" =~ ^[0-9]+$ ]] && [[ "$miss" =~ ^[0-9]+$ ]]; then
          core_stmt_total=$((core_stmt_total + stmts))
          core_stmt_cov=$((core_stmt_cov + (stmts - miss)))
        fi
      fi
    done < <(grep -E "^src/" /tmp/coverage_report.txt || true)

    if [ "$core_stmt_total" -gt 0 ]; then
      core_cov=$(( 100 * core_stmt_cov / core_stmt_total ))
    else
      core_cov=0
    fi

    echo "Overall coverage: ${overall_cov}% (threshold: ${OVERALL_COV_THRESHOLD}%)"
    echo "Core coverage (src/*): ${core_cov}% (threshold: ${CORE_COV_THRESHOLD}%)"

    cov_fail=0
    if [ "${overall_cov:-0}" -lt "${OVERALL_COV_THRESHOLD}" ]; then
      err "Overall coverage below threshold"
      cov_fail=1
    fi
    if [ "${core_cov:-0}" -lt "${CORE_COV_THRESHOLD}" ]; then
      err "Core coverage below threshold"
      cov_fail=1
    fi

    if [ $cov_fail -eq 1 ]; then
      FAILURES+=("Coverage: thresholds not met")
    else
      ok "Coverage thresholds met."
    fi
  fi
else
  warn "Skipping coverage enforcement due to --no-cov"
fi

# 5) Final summary
print_header "Summary"
summarize
