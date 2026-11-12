param(
    [switch]$AllowSyntheticWrites,
    [switch]$RequirePrivateUpload,
    [string]$ApiReadinessUrl = "http://127.0.0.1:8000/health/ready"
)

$ErrorActionPreference = "Stop"
if (-not $AllowSyntheticWrites) {
    throw "This script mutates and restores a synthetic Compose database. Pass -AllowSyntheticWrites only inside a disposable verification project."
}
foreach ($required in @("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "UPLOAD_ENCRYPTION_KEY")) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($required, "Process"))) {
        throw "The disposable Compose verification environment is missing $required."
    }
}
$readinessUri = [Uri]$ApiReadinessUrl
if ($readinessUri.Scheme -ne "http" -or $readinessUri.Host -notin @("localhost", "127.0.0.1", "::1")) {
    throw "API readiness verification is restricted to a loopback HTTP address."
}

$runtimeRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "../backend/.test-runtime"))
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
$backupDirectory = Join-Path $runtimeRoot ("compose-backup-restore-" + [guid]::NewGuid().ToString("N"))
$previousBackupKey = [Environment]::GetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", "Process")
$backupKey = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($backupKey)
[Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", [Convert]::ToBase64String($backupKey), "Process")
Import-Module (Join-Path $PSScriptRoot "backup-crypto.psm1") -Force

function Get-CaseFingerprint {
    $rows = & docker compose exec -T db psql -v ON_ERROR_STOP=1 -U $env:POSTGRES_USER -d $env:POSTGRES_DB -tAc "SELECT id || ':' || md5(title) FROM cases ORDER BY id LIMIT 1" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Could not read the synthetic case fingerprint from PostgreSQL." }
    $value = ($rows | Out-String).Trim()
    if ($value -notmatch '^(\d+):([0-9a-f]{32})$') {
        throw "The disposable Compose E2E database must contain at least one case before the backup restore check."
    }
    return @{ Id = [int]$Matches[1]; TitleHash = $Matches[2] }
}

function Get-PrivateUploadCount {
    $result = & docker compose exec -T worker python -c "from pathlib import Path; print(sum(1 for item in Path('/app/private_uploads').iterdir() if item.is_file()))" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Could not count private upload objects in the disposable worker volume." }
    $value = ($result | Out-String).Trim()
    if ($value -notmatch '^\d+$') { throw "Worker returned an invalid private upload count." }
    return [int]$value
}

try {
    $baseline = Get-CaseFingerprint
    $uploadCountBefore = Get-PrivateUploadCount
    if ($RequirePrivateUpload -and $uploadCountBefore -lt 1) {
        throw "The Compose PDF E2E must create at least one private upload before backup verification."
    }
    & (Join-Path $PSScriptRoot "backup.ps1") -BackupDirectory $backupDirectory

    $manifest = Get-ChildItem -LiteralPath $backupDirectory -Filter "SHA256SUMS-*.txt" | Select-Object -First 1
    $databaseBackup = Get-ChildItem -LiteralPath $backupDirectory -Filter "postgres-*.dump.enc" | Select-Object -First 1
    $uploadsBackup = Get-ChildItem -LiteralPath $backupDirectory -Filter "private-uploads-*.tar.gz.enc" | Select-Object -First 1
    if (-not $manifest -or -not $databaseBackup -or -not $uploadsBackup) {
        throw "Live backup did not produce both encrypted artifacts and a checksum manifest."
    }
    $manifestRows = @(Get-Content -LiteralPath $manifest.FullName)
    if (@($manifestRows | Where-Object { $_ -eq "# format=RSAICDPBK2" }).Count -ne 1) {
        throw "Live backup manifest does not identify authenticated format RSAICDPBK2."
    }
    $keyIdRows = @($manifestRows | Where-Object { $_ -match '^# backup_key_id=([0-9a-f]{64})$' })
    if ($keyIdRows.Count -ne 1 -or ($keyIdRows[0] -split "=", 2)[1] -cne (Get-BackupKeyId -Key $backupKey)) {
        throw "Live backup manifest recovery-key fingerprint does not match the key used by this test."
    }

    $mutation = & docker compose exec -T db psql -v ON_ERROR_STOP=1 -U $env:POSTGRES_USER -d $env:POSTGRES_DB -c "UPDATE cases SET title='synthetic restore mutation' WHERE id=$($baseline.Id)" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Could not apply the temporary synthetic restore mutation." }
    $mutated = Get-CaseFingerprint
    if ($mutated.TitleHash -eq $baseline.TitleHash) { throw "Synthetic restore mutation did not change the case title." }

    & (Join-Path $PSScriptRoot "restore.ps1") -PostgresDump $databaseBackup.FullName -PrivateUploadsArchive $uploadsBackup.FullName -ChecksumManifest $manifest.FullName -ConfirmRestore
    $restored = Get-CaseFingerprint
    if ($restored.Id -ne $baseline.Id -or $restored.TitleHash -ne $baseline.TitleHash) {
        throw "Live restore did not recover the original synthetic database row."
    }
    $uploadCountAfter = Get-PrivateUploadCount
    if ($uploadCountAfter -ne $uploadCountBefore) {
        throw "Live restore changed the private upload count from $uploadCountBefore to $uploadCountAfter."
    }
    $ready = Invoke-WebRequest -Uri $readinessUri.AbsoluteUri -UseBasicParsing
    if ($ready.StatusCode -ne 200) { throw "API readiness failed after live database and upload restore." }
    Write-Output "Live disposable Compose backup/restore passed: RSAICDPBK2 manifest key fingerprint matched, encrypted database/upload archives restored, synthetic mutation rolled back, $uploadCountAfter private upload object(s) retained, and API readiness returned 200."
}
finally {
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($backupKey)
    [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $previousBackupKey, "Process")
    Remove-Item -LiteralPath $backupDirectory -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Module backup-crypto -ErrorAction SilentlyContinue
}
