# Starts the local Ollama server (if not already running) and opens the
# Claude Desktop app. The two run side by side; this script does not wire
# them together.
#
# Usage: .\scripts\ollama-launch-claude-desktop.ps1
#
# Env vars:
#   OLLAMA_HOST_URL        Ollama API URL to check/start (default http://127.0.0.1:11434)
#   OLLAMA_STARTUP_TIMEOUT Seconds to wait for Ollama to come up (default 30)
#   CLAUDE_DESKTOP_BIN     Executable name or full path, if not auto-detected

#Requires -Version 5.1
$ErrorActionPreference = 'Stop'

$OllamaHostUrl = if ($env:OLLAMA_HOST_URL) { $env:OLLAMA_HOST_URL } else { 'http://127.0.0.1:11434' }
$StartupTimeoutSec = if ($env:OLLAMA_STARTUP_TIMEOUT) { [int]$env:OLLAMA_STARTUP_TIMEOUT } else { 30 }

function Write-Log([string]$msg) { Write-Host "[ollama-launch] $msg" }

function Test-OllamaRunning {
    try {
        Invoke-WebRequest -Uri $OllamaHostUrl -UseBasicParsing -TimeoutSec 2 | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Start-Ollama {
    if (Test-OllamaRunning) {
        Write-Log "Ollama server already running at $OllamaHostUrl"
        return
    }

    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        Write-Error "Error: 'ollama' is not installed or not on PATH."
        exit 1
    }

    Write-Log "Starting Ollama server..."
    Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden

    $waited = 0
    while (-not (Test-OllamaRunning)) {
        Start-Sleep -Seconds 1
        $waited++
        if ($waited -ge $StartupTimeoutSec) {
            Write-Error "Error: Ollama server did not start within ${StartupTimeoutSec}s."
            exit 1
        }
    }
    Write-Log "Ollama server is up."
}

function Find-ClaudeDesktopExe {
    $searchRoots = @(
        "$env:LOCALAPPDATA\AnthropicClaude",
        "$env:LOCALAPPDATA\Programs\Claude"
    )
    foreach ($root in $searchRoots) {
        if (Test-Path $root) {
            $found = Get-ChildItem -Path $root -Filter '*laude*.exe' -Recurse -File -ErrorAction SilentlyContinue |
                Select-Object -First 1
            if ($found) { return $found.FullName }
        }
    }
    return $null
}

function Start-ClaudeDesktop {
    if ($env:CLAUDE_DESKTOP_BIN -and (Test-Path $env:CLAUDE_DESKTOP_BIN)) {
        Write-Log "Launching Claude Desktop ($($env:CLAUDE_DESKTOP_BIN))..."
        Start-Process -FilePath $env:CLAUDE_DESKTOP_BIN
        return
    }

    $exePath = Find-ClaudeDesktopExe
    if ($exePath) {
        Write-Log "Launching Claude Desktop ($exePath)..."
        Start-Process -FilePath $exePath
        return
    }

    Write-Error "Error: Could not find Claude Desktop. Install it from https://claude.ai/download, or set CLAUDE_DESKTOP_BIN to its full .exe path."
    exit 1
}

Start-Ollama
Start-ClaudeDesktop
