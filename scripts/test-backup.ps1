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
$probeRoot = Join-Path $repoRoot (".test-sandbox-tmp/backup-orchestration-" + [guid]::NewGuid().ToString("N"))
$successRoot = Join-Path $probeRoot "success"
$failureRoot = Join-Path $probeRoot "failure"
New-Item -ItemType Directory -Path $probeRoot -Force | Out-Null

$global:BackupDockerCalls = [System.Collections.Generic.List[string]]::new()
$global:BackupFailUploadArchive = $false
function global:docker {
    $arguments = @($args)
    [void]$global:BackupDockerCalls.Add(($arguments -join " "))
    $global:LASTEXITCODE = 0

    if ($arguments[0] -eq "compose" -and $arguments.Count -gt 1 -and
        $arguments[1] -eq "run" -and $global:BackupFailUploadArchive) {
        $global:LASTEXITCODE = 42
        return
    }
    if ($arguments[0] -eq "compose" -and $arguments.Count -gt 1 -and $arguments[1] -eq "cp") {
        [System.IO.File]::WriteAllText($arguments[-1], "synthetic database backup")
    }
    if ($arguments[0] -eq "cp") {
        [System.IO.File]::WriteAllText($arguments[-1], "synthetic upload archive")
    }
}

try {
    & (Join-Path $PSScriptRoot "backup.ps1") -BackupDirectory $successRoot
    $outputs = @(Get-ChildItem -LiteralPath $successRoot -File)
    if ($outputs.Count -ne 3) { throw "Expected two backup files and one manifest; found $($outputs.Count)." }

    $encryptedDatabase = Get-ChildItem -LiteralPath $successRoot -Filter "postgres-*.dump.enc" | Select-Object -First 1
    $encryptedUploads = Get-ChildItem -LiteralPath $successRoot -Filter "private-uploads-*.tar.gz.enc" | Select-Object -First 1
    if (-not $encryptedDatabase -or -not $encryptedUploads) { throw "Backup outputs must be encrypted database and upload artifacts." }
    $databaseProbe = Join-Path $successRoot "decrypted-database-probe.dump"
    $uploadsProbe = Join-Path $successRoot "decrypted-uploads-probe.tar.gz"
    Unprotect-BackupFile -InputPath $encryptedDatabase.FullName -OutputPath $databaseProbe -Context postgres -Key $testKey
    Unprotect-BackupFile -InputPath $encryptedUploads.FullName -OutputPath $uploadsProbe -Context uploads -Key $testKey
    if ([System.IO.File]::ReadAllText($databaseProbe) -ne "synthetic database backup" -or
        [System.IO.File]::ReadAllText($uploadsProbe) -ne "synthetic upload archive") {
        throw "Encrypted backup artifacts did not decrypt to the captured synthetic contents."
    }
    Remove-Item -LiteralPath @($databaseProbe, $uploadsProbe) -Force

    $manifestPath = (Get-ChildItem -LiteralPath $successRoot -Filter "SHA256SUMS-*.txt").FullName
    $manifestRows = @(Get-Content -LiteralPath $manifestPath)
    if (@($manifestRows | Where-Object { $_ -eq "# format=RSAICDPBK2" }).Count -ne 1) {
        throw "Manifest must identify the authenticated backup format."
    }
    $keyIdRows = @($manifestRows | Where-Object { $_ -match '^# backup_key_id=([0-9a-f]{64})$' })
    if ($keyIdRows.Count -ne 1 -or ($keyIdRows[0] -split "=", 2)[1] -cne (Get-BackupKeyId -Key $testKey)) {
        throw "Manifest must identify the recovery key used by the backup."
    }
    $checksumRows = @($manifestRows | Where-Object { $_ -match '^[0-9a-fA-F]{64}\s+\S+$' })
    if ($checksumRows.Count -ne 2) { throw "Expected exactly two checksum rows." }
    foreach ($row in $checksumRows) {
        $parts = $row -split "\s+"
        $actualHash = (Get-FileHash -LiteralPath (Join-Path $successRoot $parts[1]) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $parts[0]) { throw "Manifest hash mismatch for $($parts[1])." }
    }

    $stopIndex = $global:BackupDockerCalls.IndexOf("compose stop api worker")
    $dumpIndex = -1
    for ($i = 0; $i -lt $global:BackupDockerCalls.Count; $i++) {
        if ($global:BackupDockerCalls[$i] -like "*pg_dump*") { $dumpIndex = $i; break }
    }
    $restartIndex = $global:BackupDockerCalls.IndexOf("compose up -d --wait --wait-timeout 120 api worker")
    if ($stopIndex -lt 0 -or $dumpIndex -le $stopIndex -or $restartIndex -le $dumpIndex) {
        throw "Backup did not stop writes before capture and health-check services afterward."
    }

    $global:BackupDockerCalls.Clear()
    $global:BackupFailUploadArchive = $true
    $failureWasReported = $false
    try {
        & (Join-Path $PSScriptRoot "backup.ps1") -BackupDirectory $failureRoot
    }
    catch {
        $failureWasReported = $true
    }
    if (-not $failureWasReported) { throw "A simulated archive failure was not reported." }
    if (@(Get-ChildItem -LiteralPath $failureRoot -File -ErrorAction SilentlyContinue).Count -ne 0) {
        throw "Incomplete backup files were left behind after the simulated failure."
    }
    if (-not $global:BackupDockerCalls.Contains("compose up -d --wait --wait-timeout 120 api worker")) {
        throw "Services were not restarted and health-checked after the simulated failure."
    }

    Write-Output "Backup orchestration checks passed: consistent capture order, checksum manifest, failure cleanup, and service restart."
}
finally {
    Remove-Item -LiteralPath $probeRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item Function:\docker -ErrorAction SilentlyContinue
    Remove-Variable BackupDockerCalls, BackupFailUploadArchive -Scope Global -ErrorAction SilentlyContinue
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($testKey)
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($syntheticBackupKey)
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($syntheticUploadKey)
    [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $previousBackupKey, "Process")
    [Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", $previousUploadKey, "Process")
    Remove-Module backup-crypto -ErrorAction SilentlyContinue
}
