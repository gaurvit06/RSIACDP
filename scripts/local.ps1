#requires -Version 7.1
param([ValidateSet('Init','Start','Stop','Status','Rebuild','CreateInvestigator','CreateReviewer')][string]$Action = 'Start')
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$statePath = Join-Path $repo '.local/state.json'
$envPath = Join-Path $repo '.local/compose.env'
if ($Action -eq 'Init') {
    if ((Test-Path -LiteralPath $statePath -PathType Leaf) -and (Test-Path -LiteralPath $envPath -PathType Leaf)) {
        Write-Output 'This installation is already configured. Run Start to reopen it, or Rebuild for a first build.'
        return
    }
    $privateDir = Split-Path $statePath -Parent
    if ((Test-Path -LiteralPath $privateDir) -or (Test-Path -LiteralPath (Join-Path $repo '.env'))) {
        throw 'Existing local configuration detected. Recover your original configuration using LOCALHOST.md, or initialize a fresh clone.'
    }
    $settings = [ordered]@{}
    foreach ($key in @('POSTGRES_PASSWORD','NEO4J_PASSWORD','JWT_SECRET','INITIAL_INVESTIGATOR_CODE','INITIAL_REVIEWER_CODE')) {
        $settings[$key] = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    }
    foreach ($key in @('UPLOAD_ENCRYPTION_KEY','BACKUP_ENCRYPTION_KEY')) {
        $settings[$key] = [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    }
    $project = 'casework-' + [guid]::NewGuid().ToString('N').Substring(0,12)
    New-Item -ItemType Directory -Path $privateDir -ErrorAction Stop | Out-Null
    $settings.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" } | Set-Content -LiteralPath $envPath -Encoding utf8NoBOM
    @{project=$project} | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8NoBOM
    Write-Output 'Local settings created in .local. Keep a private recovery copy. Next run Rebuild.'
    return
}
if (-not (Test-Path -LiteralPath $statePath) -or -not (Test-Path -LiteralPath $envPath)) {
    throw 'Local configuration is missing. Follow LOCALHOST.md to initialize or recover it; do not replace an existing database password or upload key.'
}
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
if ($state.project -notmatch '^[a-z0-9][a-z0-9_-]+$') { throw 'Invalid local Compose project name.' }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Install Docker Desktop with Docker Compose, then retry.' }
& docker info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Engine is unavailable. Start Docker Desktop, wait for Engine running, then retry.' }
$compose = @('compose','--project-name',$state.project,'--env-file',$envPath,'-f',(Join-Path $repo 'docker-compose.yml'),'-f',(Join-Path $repo 'compose.local.yaml'))
if ($Action -in @('CreateInvestigator','CreateReviewer')) {
    $binding = & docker @compose port api 8000
    if ($LASTEXITCODE -ne 0 -or $binding -notmatch '^127\.0\.0\.1:[0-9]+$') {
        throw 'Start this installation first. Its API must be bound to an IPv4 loopback port.'
    }
    $settings = Get-Content -LiteralPath $envPath -Raw | ConvertFrom-StringData
    $key = if ($Action -eq 'CreateInvestigator') { 'INITIAL_INVESTIGATOR_CODE' } else { 'INITIAL_REVIEWER_CODE' }
    if (-not $settings[$key]) { throw "Missing $key in the private environment file." }
    $email = Read-Host 'Sign-in email'
    $password = Read-Host 'Choose a password (12 to 128 characters)' -MaskInput
    if ($password.Length -lt 12 -or $password.Length -gt 128) { throw 'Password length must be 12 to 128 characters.' }
    $body = @{email=$email; password=$password; setup_code=$settings[$key]} | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri "http://$binding/api/auth/register" -Body $body -ContentType 'application/json; charset=utf-8' -MaximumRedirection 0 -NoProxy | Out-Null
    Write-Output 'Account created. Open http://localhost:5175/ and sign in to the workspace.'
    return
}
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
