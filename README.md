# YoonSquad

## Launching Ollama + Claude Desktop

Scripts in `scripts/` start the local Ollama server (if it isn't already
running) and then open the Claude Desktop app. The two run side by side —
Claude Desktop is not modified or reconfigured to use Ollama as a backend.

- macOS / Linux: `./scripts/ollama-launch-claude-desktop.sh`
- Windows (PowerShell): `.\scripts\ollama-launch-claude-desktop.ps1`

Requirements: [Ollama](https://ollama.com) and
[Claude Desktop](https://claude.ai/download) must already be installed.

Environment variables:
- `OLLAMA_HOST_URL` — Ollama API URL to check/start (default `http://127.0.0.1:11434`)
- `OLLAMA_STARTUP_TIMEOUT` — seconds to wait for Ollama to come up (default `30`)
- `CLAUDE_DESKTOP_APP` (macOS) — app name if not installed as "Claude"
- `CLAUDE_DESKTOP_BIN` (Linux/Windows) — executable name or full path if not auto-detected