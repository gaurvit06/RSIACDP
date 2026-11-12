$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$cryptoModule = Join-Path $PSScriptRoot "backup-crypto.psm1"
Import-Module $cryptoModule -Force
$previousBackupKey = [Environment]::GetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", "Process")
$previousUploadKey = [Environment]::GetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", "Process")
$syntheticBackupKey = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($syntheticBackupKey)
$syntheticUploadKey = [byte[]]::new(32)
[System.Security.Cryptography.RandomNumberGenerator]::Fill($syntheticUploadKey)
[Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", [Convert]::ToBase64String($syntheticBackupKey), "Process")
[Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", [Convert]::ToBase64String($syntheticUploadKey), "Process")
$testKey = Get-BackupEncryptionKey -EnvironmentFile (Join-Path $repoRoot ".missing-backup-test-env")
$probeRoot = Join-Path $repoRoot (".test-sandbox-tmp/restore-orchestration-" + [guid]::NewGuid().ToString("N"))
$successRoot = Join-Path $probeRoot "success"
$failureRoot = Join-Path $probeRoot "failure"
New-Item -ItemType Directory -Path $successRoot -Force | Out-Null
New-Item -ItemType Directory -Path $failureRoot -Force | Out-Null

$global:RestoreDockerCalls = [System.Collections.Generic.List[string]]::new()
$global:RestoreFailMatch = ""
function global:docker {
    $arguments = @($args)
    [void]$global:RestoreDockerCalls.Add(($arguments -join " "))
    $global:LASTEXITCODE = 0
    if ($global:RestoreFailMatch -and ($arguments -join " ") -like "*$global:RestoreFailMatch*") {
        $global:LASTEXITCODE = 42
    }
}

function New-SyntheticBackupSet([string]$Directory) {
    $suffix = [guid]::NewGuid().ToString("N")
    $databasePlaintext = Join-Path $Directory "source-$suffix-postgres.dump"
    $uploadsPlaintext = Join-Path $Directory "source-$suffix-private-uploads.tar.gz"
    $database = Join-Path $Directory "synthetic-$suffix-postgres.dump.enc"
    $uploads = Join-Path $Directory "synthetic-$suffix-private-uploads.tar.gz.enc"
    $manifest = Join-Path $Directory "synthetic-$suffix-SHA256SUMS.txt"
    [System.IO.File]::WriteAllText($databasePlaintext, "synthetic database backup")
    [System.IO.File]::WriteAllText($uploadsPlaintext, "synthetic uploads archive")
    Protect-BackupFile -InputPath $databasePlaintext -OutputPath $database -Context postgres -Key $testKey
    Protect-BackupFile -InputPath $uploadsPlaintext -OutputPath $uploads -Context uploads -Key $testKey
    Remove-Item -LiteralPath @($databasePlaintext, $uploadsPlaintext) -Force
    $databaseHash = (Get-FileHash -LiteralPath $database -Algorithm SHA256).Hash.ToLowerInvariant()
    $uploadsHash = (Get-FileHash -LiteralPath $uploads -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath $manifest -Encoding ascii -Value @(
        "# format=RSAICDPBK2",
        "# backup_key_id=$(Get-BackupKeyId -Key $testKey)",
        "$databaseHash  $(Split-Path -Leaf $database)",
        "$uploadsHash  $(Split-Path -Leaf $uploads)"
    )
    return @{ Database = $database; Uploads = $uploads; Manifest = $manifest }
}

try {
    $success = New-SyntheticBackupSet $successRoot

    $missingConfirmationFailed = $false
    try {
        & (Join-Path $PSScriptRoot "restore.ps1") -PostgresDump $success.Database -PrivateUploadsArchive $success.Uploads -ChecksumManifest $success.Manifest
    }
    catch { $missingConfirmationFailed = $true }
    if (-not $missingConfirmationFailed -or $global:RestoreDockerCalls.Count -ne 0) {
        throw "Restore did not require confirmation before contacting Docker."
    }

    [System.IO.File]::AppendAllText($success.Uploads, "changed")
    $badChecksumFailed = $false
    try {
        & (Join-Path $PSScriptRoot "restore.ps1") -PostgresDump $success.Database -PrivateUploadsArchive $success.Uploads -ChecksumManifest $success.Manifest -ConfirmRestore
    }
    catch { $badChecksumFailed = $true }
    if (-not $badChecksumFailed -or $global:RestoreDockerCalls.Count -ne 0) {
        throw "Restore did not reject a checksum mismatch before contacting Docker."
    }
    [System.IO.File]::WriteAllText($success.Uploads, "synthetic uploads archive")
    $success = New-SyntheticBackupSet $successRoot

    $priorBackupKey = [Environment]::GetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", "Process")
    $wrongBackupKey = [byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($wrongBackupKey)
    [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", [Convert]::ToBase64String($wrongBackupKey), "Process")
    $wrongKeyFailed = $false
    try {
        & (Join-Path $PSScriptRoot "restore.ps1") -PostgresDump $success.Database -PrivateUploadsArchive $success.Uploads -ChecksumManifest $success.Manifest -ConfirmRestore
    }
    catch { $wrongKeyFailed = $true }
    finally {
        [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($wrongBackupKey)
        [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $priorBackupKey, "Process")
    }
    if (-not $wrongKeyFailed -or $global:RestoreDockerCalls.Count -ne 0) {
        throw "Restore did not reject an invalid recovery key before contacting Docker."
    }

    & (Join-Path $PSScriptRoot "restore.ps1") -PostgresDump $success.Database -PrivateUploadsArchive $success.Uploads -ChecksumManifest $success.Manifest -ConfirmRestore
    $stopIndex = $global:RestoreDockerCalls.IndexOf("compose stop api worker")
    $copyIndex = $global:RestoreDockerCalls.FindIndex([Predicate[string]]{ param($call) $call.StartsWith("compose cp ") })
    $restoreIndex = $global:RestoreDockerCalls.FindIndex([Predicate[string]]{ param($call) $call -like "*pg_restore*" })
    $uploadsIndex = $global:RestoreDockerCalls.FindIndex([Predicate[string]]{ param($call) $call -like "*app.restore_uploads*" })
    $restartIndex = $global:RestoreDockerCalls.IndexOf("compose up -d --wait --wait-timeout 120 api worker")
    $graphIndex = $global:RestoreDockerCalls.FindIndex([Predicate[string]]{ param($call) $call -like "*app.graph_rebuild*" })
    if ($stopIndex -lt 0 -or $copyIndex -le $stopIndex -or $restoreIndex -le $copyIndex -or $uploadsIndex -le $restoreIndex -or $restartIndex -le $uploadsIndex -or $graphIndex -le $restartIndex) {
        throw "Successful restore did not follow stop, database restore, upload restore, health-checked restart, and graph rebuild order."
    }

    $global:RestoreDockerCalls.Clear()
    $failure = New-SyntheticBackupSet $failureRoot
    $global:RestoreFailMatch = "pg_restore"
    $restoreFailureWasReported = $false
    try {
        & (Join-Path $PSScriptRoot "restore.ps1") -PostgresDump $failure.Database -PrivateUploadsArchive $failure.Uploads -ChecksumManifest $failure.Manifest -ConfirmRestore
    }
    catch { $restoreFailureWasReported = $true }
    if (-not $restoreFailureWasReported) { throw "A simulated database restore failure was not reported." }
    if (-not $global:RestoreDockerCalls.Contains("compose stop api worker")) { throw "Restore failure did not stop writes before replacement." }
    if ($global:RestoreDockerCalls.Contains("compose up -d --wait --wait-timeout 120 api worker")) { throw "Failed restore unexpectedly restarted services before operator review." }
    if (-not ($global:RestoreDockerCalls | Where-Object { $_ -like "compose exec -T db sh -c rm*" })) { throw "Temporary database dump cleanup was not attempted after failure." }

    Write-Output "Restore orchestration checks passed: confirmation, checksums, operation order, graph rebuild, and safe failure stop."
}
finally {
    Remove-Item -LiteralPath $probeRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Function:\docker -ErrorAction SilentlyContinue
    Remove-Variable RestoreDockerCalls, RestoreFailMatch -Scope Global -ErrorAction SilentlyContinue
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($testKey)
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($syntheticBackupKey)
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($syntheticUploadKey)
    [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $previousBackupKey, "Process")
    [Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", $previousUploadKey, "Process")
    Remove-Module backup-crypto -ErrorAction SilentlyContinue
}
