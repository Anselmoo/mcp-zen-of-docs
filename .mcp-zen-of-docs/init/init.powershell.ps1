Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $PSCommandPath
$StateFile = Join-Path $ScriptDir 'state.json'
if (-not (Test-Path -LiteralPath $StateFile)) {
    throw "mcp-zen-of-docs init (powershell) failed: missing state file at $StateFile"
}
Write-Output "mcp-zen-of-docs init (powershell) completed: $StateFile"
