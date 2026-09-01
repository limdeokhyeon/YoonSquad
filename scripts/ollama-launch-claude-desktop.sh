#!/usr/bin/env bash
# Starts the local Ollama server (if not already running) and opens the
# Claude Desktop app. The two run side by side; this script does not wire
# them together.
#
# Usage: ./scripts/ollama-launch-claude-desktop.sh
#
# Env vars:
#   OLLAMA_HOST_URL        Ollama API URL to check/start (default http://127.0.0.1:11434)
#   OLLAMA_STARTUP_TIMEOUT Seconds to wait for Ollama to come up (default 30)
#   CLAUDE_DESKTOP_APP     macOS app name, if not installed as "Claude"
#   CLAUDE_DESKTOP_BIN     Linux executable name/path, if not auto-detected

set -euo pipefail

OLLAMA_HOST_URL="${OLLAMA_HOST_URL:-http://127.0.0.1:11434}"
OLLAMA_STARTUP_TIMEOUT="${OLLAMA_STARTUP_TIMEOUT:-30}"

log() { printf '[ollama-launch] %s\n' "$1"; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is not installed or not on PATH." >&2
    exit 1
  fi
}

ollama_is_running() {
  curl -fsS -o /dev/null --max-time 2 "$OLLAMA_HOST_URL" 2>/dev/null
}

start_ollama() {
  if ollama_is_running; then
    log "Ollama server already running at $OLLAMA_HOST_URL"
    return
  fi

  require_cmd ollama
  log "Starting Ollama server..."
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
  disown

  local waited=0
  until ollama_is_running; do
    sleep 1
    waited=$((waited + 1))
    if [ "$waited" -ge "$OLLAMA_STARTUP_TIMEOUT" ]; then
      echo "Error: Ollama server did not start within ${OLLAMA_STARTUP_TIMEOUT}s. Check /tmp/ollama-serve.log" >&2
      exit 1
    fi
  done
  log "Ollama server is up."
}

launch_claude_desktop_macos() {
  local app_name="${CLAUDE_DESKTOP_APP:-Claude}"
  if [ -d "/Applications/${app_name}.app" ] || [ -d "$HOME/Applications/${app_name}.app" ]; then
    log "Launching Claude Desktop (${app_name})..."
    open -a "$app_name"
  else
    echo "Error: Could not find '${app_name}.app' in /Applications or ~/Applications." >&2
    echo "Install Claude Desktop from https://claude.ai/download, or set CLAUDE_DESKTOP_APP" >&2
    echo "to match your installed app's name." >&2
    exit 1
  fi
}

launch_claude_desktop_linux() {
  if [ -n "${CLAUDE_DESKTOP_BIN:-}" ] && command -v "$CLAUDE_DESKTOP_BIN" >/dev/null 2>&1; then
    log "Launching Claude Desktop (${CLAUDE_DESKTOP_BIN})..."
    nohup "$CLAUDE_DESKTOP_BIN" >/tmp/claude-desktop.log 2>&1 &
    disown
    return
  fi

  # Note: intentionally not matching a bare "claude" binary here — that name
  # is commonly the Claude Code CLI (e.g. /opt/node22/bin/claude on dev
  # machines), not the Claude Desktop GUI app, and would silently "launch"
  # the wrong thing.
  if command -v claude-desktop >/dev/null 2>&1; then
    log "Launching Claude Desktop (claude-desktop)..."
    nohup claude-desktop >/tmp/claude-desktop.log 2>&1 &
    disown
    return
  fi

  if command -v gtk-launch >/dev/null 2>&1 && [ -f "/usr/share/applications/claude-desktop.desktop" ]; then
    log "Launching Claude Desktop via desktop entry..."
    gtk-launch claude-desktop
    return
  fi

  echo "Error: Could not find a Claude Desktop launcher on this Linux system." >&2
  echo "Anthropic does not officially ship a native Linux build of Claude Desktop." >&2
  echo "If you installed one (e.g. an unofficial community package), set CLAUDE_DESKTOP_BIN" >&2
  echo "to its executable name or full path and re-run this script." >&2
  exit 1
}

main() {
  require_cmd curl
  start_ollama

  case "$(uname -s)" in
    Darwin) launch_claude_desktop_macos ;;
    Linux) launch_claude_desktop_linux ;;
    *)
      echo "Error: Unsupported OS '$(uname -s)'. On Windows, use scripts/ollama-launch-claude-desktop.ps1" >&2
      exit 1
      ;;
  esac
}

main "$@"
