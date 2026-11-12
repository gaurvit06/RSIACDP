param(
    [Parameter(Mandatory = $true)]
    [string]$PostgresDump,
    [Parameter(Mandatory = $true)]
    [string]$PrivateUploadsArchive,
    [Parameter(Mandatory = $true)]
    [string]$ChecksumManifest,
    [switch]$ConfirmRestore
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmRestore) {
    throw "Restore replaces the current database and private upload contents. Re-run with -ConfirmRestore after verifying both backup files."
}

$dbBackup = [System.IO.Path]::GetFullPath($PostgresDump)
$uploadsBackup = [System.IO.Path]::GetFullPath($PrivateUploadsArchive)
$manifestPath = [System.IO.Path]::GetFullPath($ChecksumManifest)
if (-not (Test-Path -LiteralPath $dbBackup -PathType Leaf)) { throw "PostgreSQL backup not found: $dbBackup" }
if (-not (Test-Path -LiteralPath $uploadsBackup -PathType Leaf)) { throw "Private uploads archive not found: $uploadsBackup" }
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Checksum manifest not found: $manifestPath" }
$manifestRows = Get-Content -LiteralPath $manifestPath
foreach ($backupPath in @($dbBackup, $uploadsBackup)) {
    $fileName = [System.IO.Path]::GetFileName($backupPath)
    $manifestRow = $manifestRows | Where-Object { $_ -match "^[0-9a-fA-F]{64}\s+$([regex]::Escape($fileName))$" } | Select-Object -First 1
    if (-not $manifestRow) { throw "Checksum manifest does not contain $fileName" }
    $expectedHash = ($manifestRow -split "\s+")[0].ToLowerInvariant()
    $actualHash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -ne $expectedHash) { throw "SHA-256 verification failed for $fileName" }
}
$cryptoModule = Join-Path $PSScriptRoot "backup-crypto.psm1"
Import-Module $cryptoModule -Force
$backupKey = Get-BackupEncryptionKey
$keyIdRows = @($manifestRows | Where-Object { $_ -match '^# backup_key_id=([0-9a-f]{64})$' })
$formatRows = @($manifestRows | Where-Object { $_ -eq "# format=RSAICDPBK2" })
if ($formatRows.Count -ne 1 -or $keyIdRows.Count -ne 1) {
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($backupKey)
    throw "Backup manifest does not identify the authenticated backup format and recovery-key ID."
}
$expectedKeyId = ($keyIdRows[0] -split "=", 2)[1]
if ((Get-BackupKeyId -Key $backupKey) -cne $expectedKeyId) {
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($backupKey)
    throw "BACKUP_ENCRYPTION_KEY does not match the recovery-key ID in the manifest."
}
$restoreTempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("rsaicdp-restore-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $restoreTempRoot -Force | Out-Null
if ($env:OS -ne "Windows_NT") {
    [System.IO.File]::SetUnixFileMode($restoreTempRoot, [System.IO.UnixFileMode]::UserRead -bor [System.IO.UnixFileMode]::UserWrite -bor [System.IO.UnixFileMode]::UserExecute)
}
$dbRestorePath = Join-Path $restoreTempRoot "postgres.dump"
$uploadsRestorePath = Join-Path $restoreTempRoot "private-uploads.tar.gz"
$dbDumpInContainer = "/tmp/rsaicdp-restore-$([guid]::NewGuid().ToString('N')).dump"

function Invoke-Compose([string[]]$Arguments) {
    & docker compose @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

try {
    # Authenticate and decrypt both artifacts before stopping application writes.
    Unprotect-BackupFile -InputPath $dbBackup -OutputPath $dbRestorePath -Context postgres -Key $backupKey
    Unprotect-BackupFile -InputPath $uploadsBackup -OutputPath $uploadsRestorePath -Context uploads -Key $backupKey

    # Stop API and worker writes before replacing the system of record.
    Invoke-Compose @("stop", "api", "worker")
    try {
        Invoke-Compose @("cp", $dbRestorePath, "db:$dbDumpInContainer")
        Invoke-Compose @("exec", "-T", "db", "sh", "-c", "pg_restore --exit-on-error --clean --if-exists --no-owner -U `"`$POSTGRES_USER`" -d `"`$POSTGRES_DB`" $dbDumpInContainer")

        # Run a one-off worker container against the same private_uploads volume.
        $uploadsMountSource = $uploadsRestorePath.Replace('\', '/')
        $uploadsMount = "${uploadsMountSource}:/tmp/private-uploads.tar.gz:ro"
        Invoke-Compose @("run", "--rm", "--no-deps", "--volume", $uploadsMount, "--entrypoint", "python", "worker", "-m", "app.restore_uploads", "/tmp/private-uploads.tar.gz", "/app/private_uploads")
    }
    finally {
        & docker compose exec -T db sh -c "rm -f $dbDumpInContainer" 2>$null
    }

    Invoke-Compose @("up", "-d", "--wait", "--wait-timeout", "120", "api", "worker")
    Invoke-Compose @("exec", "-T", "worker", "python", "-m", "app.graph_rebuild")
    Write-Output "Restore completed from authenticated encrypted backups. Check API/worker health and review logs before accepting new cases."
}
finally {
    Remove-Item -LiteralPath $restoreTempRoot -Recurse -Force -ErrorAction SilentlyContinue
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($backupKey)
}
