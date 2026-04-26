#!/usr/bin/env bash
# deploy.sh — test and deploy linux_focus_mode to a Home Assistant instance
#
# Usage:
#   ./scripts/deploy.sh --test              # only run pytest
#   ./scripts/deploy.sh --deploy            # only copy files
#   ./scripts/deploy.sh --reload            # only reload integration via API
#   ./scripts/deploy.sh --all               # test + deploy + reload
#   ./scripts/deploy.sh --test --deploy     # combine freely
#
# Configuration — edit the block below OR export variables before calling:
#   export HA_HOST=192.168.1.10 HA_TOKEN=xxx ./scripts/deploy.sh --all

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────

# Home Assistant network address and port
HA_HOST="${HA_HOST:-homeassistant.local}"
HA_PORT="${HA_PORT:-8123}"

# Long-Lived Access Token (Settings → Profile → Security → Long-lived access tokens)
HA_TOKEN="${HA_TOKEN:-}"

# Path to HA config directory that contains custom_components/
# Examples: /config  |  /home/user/.homeassistant  |  /root/config
HA_CONFIG_DIR="${HA_CONFIG_DIR:-}"

# SSH deploy: set HA_SSH_USER (e.g. root) to deploy over SSH instead of local copy
# Leave empty for a local filesystem deploy (HA_CONFIG_DIR must be accessible)
HA_SSH_USER="${HA_SSH_USER:-}"
HA_SSH_PORT="${HA_SSH_PORT:-22}"

# Python venv used for running tests (created automatically if missing)
VENV_PATH="${VENV_PATH:-.venv}"

# ─── Internal ─────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INTEGRATION_DIR="$REPO_ROOT/custom_components/linux_focus_mode"
DOMAIN="linux_focus_mode"

RUN_TEST=0
RUN_DEPLOY=0
RUN_RELOAD=0
RUN_RESTART=0

# ─── Helpers ──────────────────────────────────────────────────────────────────

info()    { printf '\033[0;34m[ INFO ]\033[0m %s\n' "$*"; }
ok()      { printf '\033[0;32m[  OK  ]\033[0m %s\n' "$*"; }
warn()    { printf '\033[0;33m[ WARN ]\033[0m %s\n' "$*"; }
err()     { printf '\033[0;31m[ ERR  ]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --test      Run pytest (creates .venv if missing)
  --deploy    Copy integration files to HA (local or via SSH)
  --reload    Reload the integration via HA REST API  [requires HA_TOKEN]
  --restart   Full HA restart via REST API            [requires HA_TOKEN]
  --all       --test + --deploy + --reload
  -h, --help  Show this help

Required environment variables (deploy/reload):
  HA_CONFIG_DIR   Absolute path to HA config dir (e.g. /config)
  HA_TOKEN        Long-Lived Access Token (for --reload / --restart)

Optional environment variables:
  HA_HOST         HA hostname or IP   (default: homeassistant.local)
  HA_PORT         HA HTTP port        (default: 8123)
  HA_SSH_USER     SSH user for remote deploy (empty = local copy)
  HA_SSH_PORT     SSH port            (default: 22)
  VENV_PATH       Path to Python venv (default: .venv)

Examples:
  # Local HA, full workflow
  HA_CONFIG_DIR=~/.homeassistant HA_TOKEN=xxx ./scripts/deploy.sh --all

  # Remote HA over SSH, deploy + reload
  HA_SSH_USER=root HA_HOST=192.168.1.10 HA_CONFIG_DIR=/config \\
    HA_TOKEN=xxx ./scripts/deploy.sh --deploy --reload

  # Tests only (no HA needed)
  ./scripts/deploy.sh --test
EOF
}

# ─── Argument parsing ─────────────────────────────────────────────────────────

[[ $# -eq 0 ]] && usage && exit 0

for arg in "$@"; do
  case "$arg" in
    --test)    RUN_TEST=1 ;;
    --deploy)  RUN_DEPLOY=1 ;;
    --reload)  RUN_RELOAD=1 ;;
    --restart) RUN_RESTART=1 ;;
    --all)     RUN_TEST=1; RUN_DEPLOY=1; RUN_RELOAD=1 ;;
    -h|--help) usage; exit 0 ;;
    *) err "Unknown option: $arg  (run with --help for usage)" ;;
  esac
done

# ─── Step 1: Tests ────────────────────────────────────────────────────────────

run_tests() {
  info "Setting up Python venv at $VENV_PATH ..."
  if [[ ! -f "$VENV_PATH/bin/python" ]]; then
    python3 -m venv "$VENV_PATH"
    ok "Venv created."
  fi

  if ! "$VENV_PATH/bin/python" -c "import pytest_homeassistant_custom_component" 2>/dev/null; then
    info "Installing dev dependencies ..."
    "$VENV_PATH/bin/pip" install -q -r "$REPO_ROOT/requirements-dev.txt"
    ok "Dependencies installed."
  fi

  info "Running pytest ..."
  cd "$REPO_ROOT"
  "$VENV_PATH/bin/pytest" tests/ \
    --cov=custom_components/linux_focus_mode \
    --cov-report=term-missing \
    -v
  ok "All tests passed."
}

# ─── Step 2: Deploy ───────────────────────────────────────────────────────────

run_deploy() {
  [[ -z "$HA_CONFIG_DIR" ]] && err "HA_CONFIG_DIR is not set. Example: export HA_CONFIG_DIR=/config"
  [[ -d "$INTEGRATION_DIR" ]] || err "Integration source not found: $INTEGRATION_DIR"

  DEST="$HA_CONFIG_DIR/custom_components/$DOMAIN"

  if [[ -n "$HA_SSH_USER" ]]; then
    # ── Remote deploy via rsync over SSH ──
    info "Deploying to $HA_SSH_USER@$HA_HOST:$DEST (SSH port $HA_SSH_PORT) ..."
    rsync -az --delete \
      -e "ssh -p $HA_SSH_PORT" \
      "$INTEGRATION_DIR/" \
      "$HA_SSH_USER@$HA_HOST:$DEST/"
    ok "Files synced via rsync."
  else
    # ── Local deploy ──
    [[ -d "$HA_CONFIG_DIR" ]] || err "HA_CONFIG_DIR does not exist: $HA_CONFIG_DIR"
    info "Deploying locally to $DEST ..."
    mkdir -p "$DEST"
    rsync -a --delete "$INTEGRATION_DIR/" "$DEST/"
    ok "Files copied locally."
  fi
}

# ─── Step 3: Reload / Restart ─────────────────────────────────────────────────

ha_api() {
  # $1 = HTTP method, $2 = path, $3 = optional JSON body
  local method="$1" path="$2" body="${3:-}"
  local url="http://$HA_HOST:$HA_PORT$path"
  local args=(-s -o /dev/null -w "%{http_code}"
              -X "$method"
              -H "Authorization: Bearer $HA_TOKEN"
              -H "Content-Type: application/json")
  [[ -n "$body" ]] && args+=(-d "$body")
  curl "${args[@]}" "$url"
}

check_token() {
  [[ -z "$HA_TOKEN" ]] && err "HA_TOKEN is not set. Create one at: HA → Profile → Security → Long-lived access tokens"
}

run_reload() {
  check_token
  info "Looking up config entry for domain '$DOMAIN' ..."

  # Fetch all config entries and find the one matching our domain
  entries=$(curl -s \
    -H "Authorization: Bearer $HA_TOKEN" \
    "http://$HA_HOST:$HA_PORT/api/config/config_entries/entry" \
    | python3 -c "
import sys, json
entries = json.load(sys.stdin)
matches = [e for e in entries if e.get('domain') == '$DOMAIN']
for e in matches:
    print(e['entry_id'])
")

  if [[ -z "$entries" ]]; then
    warn "No config entry found for '$DOMAIN'. Is the integration set up in HA?"
    warn "Falling back to full restart ..."
    run_restart
    return
  fi

  while IFS= read -r entry_id; do
    info "Reloading entry $entry_id ..."
    code=$(ha_api POST "/api/config/config_entries/entry/$entry_id/reload")
    if [[ "$code" == "200" ]]; then
      ok "Entry $entry_id reloaded successfully."
    else
      warn "Reload returned HTTP $code for entry $entry_id."
    fi
  done <<< "$entries"
}

run_restart() {
  check_token
  info "Sending full restart request to HA ..."
  code=$(ha_api POST "/api/services/homeassistant/restart" '{}')
  if [[ "$code" == "200" ]]; then
    ok "Restart triggered. HA will be back in ~30 seconds."
  else
    err "Restart request failed (HTTP $code)."
  fi
}

# ─── Main ─────────────────────────────────────────────────────────────────────

echo ""
echo "  linux_focus_mode — deploy script"
echo "  repo: $REPO_ROOT"
echo ""

[[ $RUN_TEST    -eq 1 ]] && run_tests
[[ $RUN_DEPLOY  -eq 1 ]] && run_deploy
[[ $RUN_RELOAD  -eq 1 ]] && run_reload
[[ $RUN_RESTART -eq 1 ]] && run_restart

echo ""
ok "Done."
