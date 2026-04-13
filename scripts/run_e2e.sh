#!/usr/bin/env bash
# run_e2e.sh — end-to-end unattended test for GAT
#
# Usage:
#   ./scripts/run_e2e.sh [--preset <preset>] [--rd <requirements_file>]
#
# Runs all three phases (requirements → hire → execute) using a sample
# requirements document and verifies that all expected output files exist.
# Exits non-zero on any failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Defaults
PRESET="${PRESET:-fast}"
RD="${RD:-${REPO_ROOT}/tasks/task_calculator.md}"
CONFIG="${CONFIG:-${REPO_ROOT}/gat/gat.yaml}"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --preset) PRESET="$2"; shift 2 ;;
    --rd)     RD="$2";     shift 2 ;;
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# --- Validate inputs ---
if [[ ! -f "$RD" ]]; then
  echo "ERROR: Requirements document not found: $RD" >&2
  exit 1
fi

echo "========================================"
echo "GAT end-to-end test"
echo "  requirements: $RD"
echo "  preset:       $PRESET"
echo "  config:       $CONFIG"
echo "========================================"

# Create a timestamped run dir inside runs/e2e/
STAMP=$(date +"%Y-%m-%dT%H-%M-%S")
RUN_DIR="${REPO_ROOT}/runs/e2e/${STAMP}"
mkdir -p "$RUN_DIR"
echo "  run dir:      $RUN_DIR"
echo ""

cd "$REPO_ROOT"

# --- Phase 1: requirements ---
echo ">>> Phase 1/3: requirements"
python -m gat \
  --config "$CONFIG" \
  --preset "$PRESET" \
  --run-dir "$RUN_DIR" \
  requirements \
  --rd "$RD"

# Verify expected outputs
for f in requirements.md review.md requirements_reviewed.md; do
  if [[ ! -f "${RUN_DIR}/${f}" ]]; then
    echo "FAIL: Missing expected file after requirements phase: ${RUN_DIR}/${f}" >&2
    exit 1
  fi
  echo "  OK: ${f}"
done

# --- Phase 2: hire (use the reviewed requirements) ---
echo ""
echo ">>> Phase 2/3: hire"
python -m gat \
  --config "$CONFIG" \
  --preset "$PRESET" \
  --run-dir "$RUN_DIR" \
  hire \
  --rd "${RUN_DIR}/requirements_reviewed.md"

if [[ ! -f "${RUN_DIR}/crew.yaml" ]]; then
  echo "FAIL: Missing expected file after hire phase: ${RUN_DIR}/crew.yaml" >&2
  exit 1
fi
echo "  OK: crew.yaml"

# --- Phase 3: execute ---
echo ""
echo ">>> Phase 3/3: execute"
python -m gat \
  --config "$CONFIG" \
  --preset "$PRESET" \
  --run-dir "$RUN_DIR" \
  run \
  --rd "${RUN_DIR}/requirements_reviewed.md" \
  --crew "${RUN_DIR}/crew.yaml"

# Verify work logs were written
LOG_DIR="${RUN_DIR}/logs"
for phase in requirements hiring execution; do
  if [[ ! -d "${LOG_DIR}/${phase}" ]]; then
    echo "FAIL: Missing work log directory: ${LOG_DIR}/${phase}" >&2
    exit 1
  fi
  md_count=$(find "${LOG_DIR}/${phase}" -name "*.md" | wc -l)
  if [[ "$md_count" -lt 1 ]]; then
    echo "FAIL: No work log entries in ${LOG_DIR}/${phase}" >&2
    exit 1
  fi
  echo "  OK: logs/${phase}/ (${md_count} log file(s))"
done

echo ""
echo "========================================"
echo "ALL CHECKS PASSED"
echo "Run artifacts: $RUN_DIR"
echo "========================================"
