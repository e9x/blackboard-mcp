#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Blackboard MCP — One-shot installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/sasindudilshanranwadana/blackboard-mcp/main/install.sh | bash
#
# What it does:
#   1. Checks Python 3.11+ is available
#   2. Clones the repo to ~/blackboard-mcp  (or updates if already installed)
#   3. Installs Python dependencies with pip
#   4. Runs the interactive setup wizard
#
# Works on: macOS, Linux, Windows (WSL)
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
BOLD="\033[1m"
DIM="\033[2m"
CYAN="\033[36m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

ok()   { echo -e "  ${GREEN}✅${RESET}  $*"; }
info() { echo -e "  ${DIM}ℹ${RESET}   $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}   $*"; }
fail() { echo -e "  ${RED}✗${RESET}   $*"; exit 1; }
step() { echo -e "\n${CYAN}${BOLD}▶  $*${RESET}"; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║        Blackboard MCP  —  Installer          ║"
echo "  ║  Connect any AI assistant to your university ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

# ── Config ────────────────────────────────────────────────────────────────────
REPO_URL="https://github.com/sasindudilshanranwadana/blackboard-mcp.git"
INSTALL_DIR="${BLACKBOARD_MCP_DIR:-$HOME/blackboard-mcp}"

# ── Step 1: Check OS ─────────────────────────────────────────────────────────
step "Checking your system"

OS="$(uname -s 2>/dev/null || echo Unknown)"
case "$OS" in
  Darwin)  ok "macOS detected" ;;
  Linux)   ok "Linux detected" ;;
  *)       warn "OS: $OS — proceeding anyway" ;;
esac

# ── Step 2: Check Python ──────────────────────────────────────────────────────
step "Checking Python version"

PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" &>/dev/null; then
    ver=$("$candidate" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    major="${ver%%.*}"
    minor="${ver##*.}"
    if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
      PYTHON="$candidate"
      ok "Python $ver found  ($candidate)"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  fail "Python 3.11 or later is required but was not found.

  ${BOLD}Install options:${RESET}
    macOS:   brew install python@3.13
    Ubuntu:  sudo apt install python3.13
    Windows: https://python.org/downloads"
fi

# ── Step 3: Check git ─────────────────────────────────────────────────────────
step "Checking git"

if ! command -v git &>/dev/null; then
  fail "git is required but was not found.

  ${BOLD}Install options:${RESET}
    macOS:  brew install git   (or install Xcode Command Line Tools)
    Ubuntu: sudo apt install git
    Windows: https://git-scm.com/downloads"
fi
ok "git found ($(git --version))"

# ── Step 4: Clone or update ───────────────────────────────────────────────────
step "Setting up Blackboard MCP in ${BOLD}${INSTALL_DIR}${RESET}"

if [ -d "${INSTALL_DIR}/.git" ]; then
  info "Already installed — pulling latest updates..."
  git -C "${INSTALL_DIR}" pull --quiet
  ok "Updated to latest version"
else
  info "Cloning repository to ${INSTALL_DIR}..."
  git clone --quiet "$REPO_URL" "${INSTALL_DIR}"
  ok "Repository cloned"
fi

# ── Step 5: Check write permissions ──────────────────────────────────────────
if ! touch "${INSTALL_DIR}/.write_test" 2>/dev/null; then
  fail "Cannot write to ${INSTALL_DIR}. Check folder permissions and try again."
fi
rm -f "${INSTALL_DIR}/.write_test"

# ── Step 6: Install Python dependencies ──────────────────────────────────────
step "Installing Python dependencies"

info "Installing packages..."
"${PYTHON}" -m pip install --quiet -r "${INSTALL_DIR}/requirements.txt"
ok "Python packages installed"

# ── Step 7: Wrapper script ────────────────────────────────────────────────────
WRAPPER="${INSTALL_DIR}/run_server.sh"
cat > "${WRAPPER}" <<WRAPPER_EOF
#!/usr/bin/env bash
exec "${PYTHON}" "${INSTALL_DIR}/server.py" "\$@"
WRAPPER_EOF
chmod +x "${WRAPPER}"

# ── Step 8: Run setup wizard ──────────────────────────────────────────────────
step "Launching setup wizard"
echo ""
info "The wizard will:"
info "  • Ask for your university's Blackboard URL"
info "  • Open your browser — log in as you normally would"
info "  • Configure your AI assistants automatically"
echo ""

# When installed via `curl ... | bash`, this script's stdin is the pipe,
# not the terminal — so interactive prompts would silently read garbage.
# Redirect setup.py's stdin from /dev/tty so the wizard talks to the user
# directly. Fall back to no redirect if /dev/tty isn't available.
if [ -r /dev/tty ]; then
  "${PYTHON}" "${INSTALL_DIR}/setup.py" < /dev/tty
else
  warn "No TTY available — running setup.py non-interactively."
  warn "Pass --url <your blackboard URL> via the installer to skip the prompt:"
  warn "  BLACKBOARD_URL=https://your.uni.edu bash install.sh"
  if [ -n "${BLACKBOARD_URL:-}" ]; then
    "${PYTHON}" "${INSTALL_DIR}/setup.py" --url "${BLACKBOARD_URL}" --yes
  else
    "${PYTHON}" "${INSTALL_DIR}/setup.py"
  fi
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║   🎉  Blackboard MCP installed & ready!      ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
info "Installed to: ${BOLD}${INSTALL_DIR}${RESET}"
info ""
info "To update later:"
info "  cd \"${INSTALL_DIR}\" && git pull && python3 setup.py"
info ""
info "To reset your session:"
info "  python3 \"${INSTALL_DIR}/setup.py\" --reset"
echo ""
