param(
    [string]$BackupDirectory = ".\backups"
)

$ErrorActionPreference = "Stop"
$cryptoModule = Join-Path $PSScriptRoot "backup-crypto.psm1"
Import-Module $cryptoModule -Force
$backupKey = Get-BackupEncryptionKey
$backupRoot = [System.IO.Path]::GetFullPath($BackupDirectory)
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
$workingRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("rsaicdp-backup-" + $stamp + "-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $workingRoot -Force | Out-Null
if ($env:OS -ne "Windows_NT") {
    [System.IO.File]::SetUnixFileMode($workingRoot, [System.IO.UnixFileMode]::UserRead -bor [System.IO.UnixFileMode]::UserWrite -bor [System.IO.UnixFileMode]::UserExecute)
}
$dbDumpInContainer = "/tmp/rsaicdp-$stamp.dump"
$uploadsArchiveInContainer = "/tmp/rsaicdp-$stamp-uploads.tar.gz"
$workerBackupContainer = "rsaicdp-backup-$stamp-$([guid]::NewGuid().ToString('N').Substring(0, 8))"
$dbPlaintextPath = Join-Path $workingRoot "postgres-$stamp.dump"
$uploadsPlaintextPath = Join-Path $workingRoot "private-uploads-$stamp.tar.gz"
$dbBackupPath = Join-Path $backupRoot "postgres-$stamp.dump.enc"
$uploadsBackupPath = Join-Path $backupRoot "private-uploads-$stamp.tar.gz.enc"
$manifestPath = Join-Path $backupRoot "SHA256SUMS-$stamp.txt"
$manifestTempPath = "$manifestPath.tmp"
foreach ($path in @($dbPlaintextPath, $uploadsPlaintextPath, $dbBackupPath, $uploadsBackupPath, $manifestPath, $manifestTempPath)) {
    if (Test-Path -LiteralPath $path) { throw "Backup output already exists: $path" }
}

function Invoke-Compose([string[]]$Arguments) {
    & docker compose @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

$servicesMayNeedRestart = $false
$backupComplete = $false
try {
    # Keep PostgreSQL rows and upload files at one consistent point in time.
    # Set the flag before stop so a partial stop failure still triggers recovery.
    $servicesMayNeedRestart = $true
    Invoke-Compose @("stop", "api", "worker")
    Invoke-Compose @("exec", "-T", "db", "sh", "-c", "pg_dump -Fc -U `"`$POSTGRES_USER`" `"`$POSTGRES_DB`" -f $dbDumpInContainer")
    Invoke-Compose @("cp", "db:$dbDumpInContainer", $dbPlaintextPath)
    Invoke-Compose @("run", "-T", "--no-deps", "--name", $workerBackupContainer, "--entrypoint", "sh", "worker", "-c", "tar -czf $uploadsArchiveInContainer -C /app/private_uploads .")
    & docker cp "${workerBackupContainer}:$uploadsArchiveInContainer" $uploadsPlaintextPath
    if ($LASTEXITCODE -ne 0) { throw "docker cp from backup worker failed with exit code $LASTEXITCODE" }

    Protect-BackupFile -InputPath $dbPlaintextPath -OutputPath $dbBackupPath -Context postgres -Key $backupKey
    Remove-Item -LiteralPath $dbPlaintextPath -Force
    Protect-BackupFile -InputPath $uploadsPlaintextPath -OutputPath $uploadsBackupPath -Context uploads -Key $backupKey
    Remove-Item -LiteralPath $uploadsPlaintextPath -Force

    $dbHash = (Get-FileHash -LiteralPath $dbBackupPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $uploadsHash = (Get-FileHash -LiteralPath $uploadsBackupPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $backupKeyId = Get-BackupKeyId -Key $backupKey
    Set-Content -LiteralPath $manifestTempPath -Encoding ascii -Value @(
        "# format=RSAICDPBK2",
        "# backup_key_id=$backupKeyId",
        "$dbHash  $(Split-Path -Leaf $dbBackupPath)",
        "$uploadsHash  $(Split-Path -Leaf $uploadsBackupPath)"
    )
    [System.IO.File]::Move($manifestTempPath, $manifestPath)
    $backupComplete = $true
    Write-Output "Backup complete: $backupRoot"
    Write-Output "Encrypted PostgreSQL: postgres-$stamp.dump.enc"
    Write-Output "Encrypted private uploads: private-uploads-$stamp.tar.gz.enc"
    Write-Output "Checksums: SHA256SUMS-$stamp.txt"
    Write-Output "Neo4j is a rebuildable projection; rebuild it from PostgreSQL after recovery."
}
finally {
    & docker rm -f $workerBackupContainer 2>$null
    & docker compose exec -T db sh -c "rm -f $dbDumpInContainer" 2>$null
    $restartError = $null
    if ($servicesMayNeedRestart) {
        & docker compose up -d --wait --wait-timeout 120 api worker
        if ($LASTEXITCODE -ne 0) { $restartError = "API and worker did not restart cleanly (docker compose exit $LASTEXITCODE)" }
    }

    if (-not $backupComplete) {
        Remove-Item -LiteralPath @($dbPlaintextPath, $uploadsPlaintextPath, $dbBackupPath, $uploadsBackupPath, $manifestTempPath, $manifestPath) -Force -ErrorAction SilentlyContinue
    } else {
        Remove-Item -LiteralPath @($dbPlaintextPath, $uploadsPlaintextPath) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $workingRoot -Recurse -Force -ErrorAction SilentlyContinue
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($backupKey)
    if ($restartError) { throw $restartError }
}
