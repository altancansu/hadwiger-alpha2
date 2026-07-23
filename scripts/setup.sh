#!/usr/bin/env bash
#
# setup.sh — one-shot provisioning for the hadwiger-alpha2 harness on a fresh
# Ubuntu 24.04 x86-64 box (bare VM or a vast.ai/Docker container).
#
# Usage — either bootstrap straight from GitHub (public repo, no token):
#   bash <(curl -fsSL https://raw.githubusercontent.com/altancansu/hadwiger-alpha2/main/scripts/setup.sh)
# ...or, if you already cloned the repo, from inside it:
#   bash scripts/setup.sh
#
# Safe to re-run. Works whether you are root (vast containers usually are) or
# a normal sudo user — it auto-detects.
set -euo pipefail

REPO_URL="https://github.com/altancansu/hadwiger-alpha2.git"
REPO_DIR="hadwiger-alpha2"

# use sudo only when NOT already root
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

echo "▶ 1/6  System packages (nauty→geng/pickg/shortg, build tools, tmux, htop)"
$SUDO apt-get update
$SUDO apt-get install -y build-essential git curl ca-certificates nauty tmux htop

echo "▶ 2/6  uv (pins CPython 3.12.13 + the locked venv)"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
# shellcheck disable=SC1091
[ -f "$HOME/.local/bin/env" ] && source "$HOME/.local/bin/env"
export PATH="$HOME/.local/bin:$PATH"

echo "▶ 3/6  Node 22 + Claude Code CLI"
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | $SUDO -E bash -
  $SUDO apt-get install -y nodejs
fi
$SUDO npm install -g @anthropic-ai/claude-code

echo "▶ 4/6  Locate or clone the repo"
if [ -f "pyproject.toml" ] && grep -q 'name = "alpha2"' pyproject.toml 2>/dev/null; then
  echo "  already inside the repo: $(pwd)"
elif [ -d "$REPO_DIR/.git" ]; then
  cd "$REPO_DIR"; echo "  using existing clone: $(pwd)"
else
  git clone "$REPO_URL"; cd "$REPO_DIR"; echo "  cloned into: $(pwd)"
fi

echo "▶ 5/6  Build the exact locked environment (incl. pynauty extra)"
uv sync --extra nauty

echo "▶ 6/6  Verify (nauty on PATH + full non-slow suite)"
which geng pickg shortg
uv run pytest -q -m "not slow" || echo "⚠ verify reported failures — inspect the output above before running sweeps"

cat <<'EOF'

✅ Setup complete.

Next steps:
  cd hadwiger-alpha2
  claude                 # then type /login and authenticate in the browser

Run long work inside tmux so it survives SSH drops:
  tmux new -s work       # detach: Ctrl-b then d   |   reattach: tmux attach -t work
  uv run pytest -n "$(nproc)" -m slow          # generation / has_cdm: full cores
  # CP-SAT-heavy sweeps: back off -n to fit RAM (watch htop), e.g. -n 180
  # discipline: keep num_workers=1 on any reported impossibility/INFEASIBLE verdict

Re-sync later after pushing new work locally:
  git pull --ff-only && uv sync --extra nauty
EOF
