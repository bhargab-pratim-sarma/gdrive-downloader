#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║     GDrive Advanced Downloader — Launcher Script         ║
# ║  Sets up Python venv, installs deps, runs manager        ║
# ╚══════════════════════════════════════════════════════════╝

set -euo pipefail

# ─── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
PYTHON_SCRIPT="$SCRIPT_DIR/gdrive_manager.py"

# ─── Colors ───────────────────────────────────────────────────────────────────
RED='\033[91m'; GREEN='\033[92m'; YELLOW='\033[93m'
CYAN='\033[96m'; DIM='\033[2m'; RESET='\033[0m'; BOLD='\033[1m'

ok()   { echo -e "${GREEN}✅ $*${RESET}"; }
warn() { echo -e "${YELLOW}⚠️  $*${RESET}"; }
err()  { echo -e "${RED}❌ $*${RESET}"; }
info() { echo -e "${CYAN}ℹ️  $*${RESET}"; }
sep()  { echo -e "${DIM}──────────────────────────────────────────────────────${RESET}"; }

# ─── Banner ───────────────────────────────────────────────────────────────────
echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║       GDrive Advanced Downloader — Launcher              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${RESET}"

# ─── Check Python ─────────────────────────────────────────────────────────────
sep
info "Checking Python installation…"

# Prefer python3 from pyenv if available, else system python3
if command -v python3 &>/dev/null; then
    PYTHON_BIN="$(command -v python3)"
    PYTHON_VER="$("$PYTHON_BIN" --version 2>&1)"
    ok "Found: $PYTHON_VER  ($PYTHON_BIN)"
else
    err "Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Enforce minimum Python 3.8
PY_MINOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.minor)')"
PY_MAJOR="$("$PYTHON_BIN" -c 'import sys; print(sys.version_info.major)')"
if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 8 ]]; then
    err "Python 3.8+ required. Found: $PYTHON_VER"
    exit 1
fi

# ─── Create / Activate venv ───────────────────────────────────────────────────
sep
if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating Python virtual environment at .venv …"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    ok "Virtual environment created."
else
    ok "Virtual environment already exists."
fi

# Activate
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"
ok "Virtual environment activated."

# ─── Upgrade pip silently ─────────────────────────────────────────────────────
info "Upgrading pip…"
"$VENV_PIP" install --quiet --upgrade pip

# ─── Write requirements.txt if missing ───────────────────────────────────────
if [[ ! -f "$REQUIREMENTS" ]]; then
    info "Creating requirements.txt…"
    cat > "$REQUIREMENTS" << 'EOF'
gdown>=5.2.0
tqdm>=4.66.0
requests>=2.31.0
EOF
    ok "requirements.txt created."
fi

# ─── Install / Update dependencies ────────────────────────────────────────────
sep
info "Checking and installing dependencies…"

# Track if anything was installed
INSTALLED=0

while IFS= read -r pkg || [[ -n "$pkg" ]]; do
    # Skip blank lines and comments
    [[ -z "$pkg" || "$pkg" == \#* ]] && continue

    pkg_name="${pkg%%[>=<]*}"   # strip version specifier for check
    if "$VENV_PIP" show "$pkg_name" &>/dev/null 2>&1; then
        echo -e "  ${DIM}• $pkg_name — already installed${RESET}"
    else
        info "Installing $pkg_name…"
        "$VENV_PIP" install --quiet "$pkg"
        ok "$pkg_name installed."
        INSTALLED=1
    fi
done < "$REQUIREMENTS"

if [[ $INSTALLED -eq 0 ]]; then
    ok "All dependencies are up to date."
fi

# ─── Verify Python script exists ──────────────────────────────────────────────
sep
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    err "gdrive_manager.py not found at: $PYTHON_SCRIPT"
    exit 1
fi
ok "gdrive_manager.py found."

# ─── Parse CLI arguments ──────────────────────────────────────────────────────
# Allow passing a menu option directly: ./run.sh 1  (runs verify non-interactively)
DIRECT_CHOICE="${1:-}"

# ─── Launch ───────────────────────────────────────────────────────────────────
sep
echo ""
if [[ -n "$DIRECT_CHOICE" ]]; then
    info "Running gdrive_manager.py with auto-choice: $DIRECT_CHOICE"
    echo -e "$DIRECT_CHOICE\nq" | "$VENV_PYTHON" "$PYTHON_SCRIPT"
else
    info "Launching gdrive_manager.py …"
    echo ""
    "$VENV_PYTHON" "$PYTHON_SCRIPT"
fi

# ─── Exit ─────────────────────────────────────────────────────────────────────
echo ""
sep
ok "Session complete. Virtual env stays active for next run."
