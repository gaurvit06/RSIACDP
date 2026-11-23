#requires -Version 7.0
param([ValidateSet('Start','Stop','Status','Rebuild')][string]$Action = 'Start')
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$statePath = Join-Path $repo '.local/state.json'
$envPath = Join-Path $repo '.local/compose.env'
if (-not (Test-Path -LiteralPath $statePath) -or -not (Test-Path -LiteralPath $envPath)) {
    throw 'Local configuration is missing. Follow LOCALHOST.md to initialize or recover it; do not replace an existing database password or upload key.'
}
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
if ($state.project -notmatch '^[a-z0-9][a-z0-9_-]+$') { throw 'Invalid local Compose project name.' }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Install Docker Desktop with Docker Compose, then retry.' }
& docker info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Engine is unavailable. Start Docker Desktop, wait for Engine running, then retry.' }
$compose = @('compose','--project-name',$state.project,'--env-file',$envPath,'-f',(Join-Path $repo 'docker-compose.yml'),'-f',(Join-Path $repo 'compose.local.yaml'))
switch ($Action) {
    'Start' { $operation = @('up','--no-build','-d','--wait','--wait-timeout','300') }
    'Rebuild' { $operation = @('up','--build','-d','--wait','--wait-timeout','300') }
    'Stop' { $operation = @('stop') }
    'Status' { $operation = @('ps','--all') }
}
& docker @compose @operation
if ($LASTEXITCODE -ne 0) { throw "Local $Action failed. Inspect Docker's error above. If images are missing, run this script with -Action Rebuild." }
if ($Action -in @('Start','Rebuild')) {
    $ready = Invoke-RestMethod 'http://127.0.0.1:8001/health/ready' -TimeoutSec 15
    $web = Invoke-WebRequest 'http://127.0.0.1:5175/' -TimeoutSec 15
    $policy = Invoke-WebRequest 'http://127.0.0.1:5175/api/policy' -TimeoutSec 15
    if ($ready.status -ne 'ready' -or $web.StatusCode -ne 200 -or $policy.StatusCode -ne 200) { throw 'Local HTTP readiness verification failed.' }
    Write-Output 'Application ready: http://localhost:5175/ (API, database readiness and web proxy verified).'
}
