#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║        NotebookLM Prep — Launcher Script                 ║
# ║      Runs notebook_lm_prep.py in the project venv        ║
# ╚══════════════════════════════════════════════════════════╝

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
PYTHON_SCRIPT="$SCRIPT_DIR/notebook_lm_prep.py"

# Check if venv exists (created by main run.sh)
if [[ ! -f "$VENV_PYTHON" ]]; then
    echo "❌ Virtual environment not found."
    echo "Please run './run.sh' first to set up the environment."
    exit 1
fi

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "❌ notebook_lm_prep.py not found!"
    exit 1
fi

echo "🚀 Launching NotebookLM Dataset Preparer..."
"$VENV_PYTHON" "$PYTHON_SCRIPT"
