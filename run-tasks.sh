#!/usr/bin/env bash
set -euo pipefail

MODEL="gpt-4.1"
TASK_DIR="./tasks"
TMP_DIR="./tmp"
mkdir -p "$TMP_DIR"

min_iter=3
max_iter=10
iter=0
changed=1

while [[ $iter -lt $max_iter ]]; do
    echo "Iteration $((iter+1))"
    changed=0

    for task in "$TASK_DIR"/*.md; do
        base=$(basename "$task")
        tmp="$TMP_DIR/$base.out"

        # Run Copilot CLI in YOLO mode (non-interactive)
        copilot -p "$(cat "$task")" \
            --model "$MODEL" \
            --yolo \
            --silent \
            > "$tmp"

        # Detect changes
        if ! cmp -s "$task" "$tmp"; then
            echo "Updated: $task"
            cp "$tmp" "$task"
            changed=1
        fi
    done

    iter=$((iter+1))

    # Stop only if:
    # - no changes AND
    # - we have completed at least min_iter iterations
    if [[ $changed -eq 0 && $iter -ge $min_iter ]]; then
        break
    fi
done

echo "Finished after $iter iterations."

