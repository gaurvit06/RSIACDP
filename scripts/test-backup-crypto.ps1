$ErrorActionPreference = "Stop"
$cryptoModule = Join-Path $PSScriptRoot "backup-crypto.psm1"
Import-Module $cryptoModule -Force
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("rsaicdp-backup-crypto-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null

try {
    $key = [byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($key)
    $wrongKey = [byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($wrongKey)
    $plainPath = Join-Path $testRoot "synthetic-postgres.dump"
    $encryptedPath = Join-Path $testRoot "synthetic-postgres.dump.enc"
    $roundTripPath = Join-Path $testRoot "round-trip.dump"
    $tamperedPath = Join-Path $testRoot "tampered.dump.enc"
    $tamperedOutputPath = Join-Path $testRoot "tampered-plaintext.dump"
    $wrongContextPath = Join-Path $testRoot "wrong-context.dump"

    $content = [byte[]]::new((4 * 1024 * 1024) + 123)
    for ($i = 0; $i -lt $content.Length; $i++) { $content[$i] = [byte](($i * 31 + 17) % 251) }
    [System.IO.File]::WriteAllBytes($plainPath, $content)

    $oldBackupKey = [Environment]::GetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", "Process")
    $oldUploadKey = [Environment]::GetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", "Process")
    try {
        [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $null, "Process")
        [Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", $null, "Process")
        $missingKeyRejected = $false
        try { Get-BackupEncryptionKey -EnvironmentFile (Join-Path $testRoot "missing.env") | Out-Null }
        catch { $missingKeyRejected = $true }
        if (-not $missingKeyRejected) { throw "Missing backup encryption key was accepted." }

        $keyText = [Convert]::ToBase64String($key)
        [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $keyText, "Process")
        [Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", $keyText, "Process")
        $sameKeyRejected = $false
        try { Get-BackupEncryptionKey -EnvironmentFile (Join-Path $testRoot "missing.env") | Out-Null }
        catch { $sameKeyRejected = $true }
        if (-not $sameKeyRejected) { throw "Backup and upload encryption accepted the same key." }

        $envBackupKey = [byte[]]::new(32)
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($envBackupKey)
        $envUploadKey = [byte[]]::new(32)
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($envUploadKey)
        $envFile = Join-Path $testRoot "backup-keys.env"
        Set-Content -LiteralPath $envFile -Encoding ascii -Value @(
            "BACKUP_ENCRYPTION_KEY=$([Convert]::ToBase64String($envBackupKey))",
            "UPLOAD_ENCRYPTION_KEY=$([Convert]::ToBase64String($envUploadKey))"
        )
        [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $null, "Process")
        [Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", $null, "Process")
        $loadedKey = Get-BackupEncryptionKey -EnvironmentFile $envFile
        if ([Convert]::ToBase64String($loadedKey) -ne [Convert]::ToBase64String($envBackupKey)) {
            throw "Backup encryption key was not read from the selected environment file."
        }
        [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($loadedKey)
        [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($envBackupKey)
        [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($envUploadKey)
    }
    finally {
        [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $oldBackupKey, "Process")
        [Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", $oldUploadKey, "Process")
    }

    Protect-BackupFile -InputPath $plainPath -OutputPath $encryptedPath -Context postgres -Key $key
    $encrypted = [System.IO.File]::ReadAllBytes($encryptedPath)
    if ([System.Text.Encoding]::ASCII.GetString($encrypted).Contains("synthetic-postgres")) {
        throw "Encrypted backup contains a plaintext test marker."
    }
    Unprotect-BackupFile -InputPath $encryptedPath -OutputPath $roundTripPath -Context postgres -Key $key
    $plainHash = (Get-FileHash -LiteralPath $plainPath -Algorithm SHA256).Hash
    $roundTripHash = (Get-FileHash -LiteralPath $roundTripPath -Algorithm SHA256).Hash
    if ($plainHash -ne $roundTripHash) { throw "Encrypted backup round-trip checksum mismatch." }

    $wrongKeyFailed = $false
    try { Unprotect-BackupFile -InputPath $encryptedPath -OutputPath $wrongContextPath -Context postgres -Key $wrongKey }
    catch { $wrongKeyFailed = $true }
    if (-not $wrongKeyFailed -or (Test-Path -LiteralPath $wrongContextPath)) {
        throw "Backup wrong-key rejection failed (rejected=$wrongKeyFailed, outputExists=$(Test-Path -LiteralPath $wrongContextPath))."
    }

    $wrongContextFailed = $false
    try { Unprotect-BackupFile -InputPath $encryptedPath -OutputPath $wrongContextPath -Context uploads -Key $key }
    catch { $wrongContextFailed = $true }
    if (-not $wrongContextFailed -or (Test-Path -LiteralPath $wrongContextPath)) {
        throw "Backup decryption did not reject a context substitution cleanly."
    }

    [System.IO.File]::Copy($encryptedPath, $tamperedPath)
    $tamperedBytes = [System.IO.File]::ReadAllBytes($tamperedPath)
    $tamperedBytes[52] = $tamperedBytes[52] -bxor 1
    [System.IO.File]::WriteAllBytes($tamperedPath, $tamperedBytes)
    $tamperFailed = $false
    try { Unprotect-BackupFile -InputPath $tamperedPath -OutputPath $tamperedOutputPath -Context postgres -Key $key }
    catch { $tamperFailed = $true }
    if (-not $tamperFailed -or (Test-Path -LiteralPath $tamperedOutputPath)) {
        throw "Backup decryption did not reject a modified authenticated frame cleanly."
    }

    $truncatedPath = Join-Path $testRoot "truncated.dump.enc"
    [System.IO.File]::WriteAllBytes($truncatedPath, $encrypted[0..($encrypted.Length - 2)])
    $truncatedFailed = $false
    try { Unprotect-BackupFile -InputPath $truncatedPath -OutputPath (Join-Path $testRoot "truncated.dump") -Context postgres -Key $key }
    catch { $truncatedFailed = $true }
    if (-not $truncatedFailed) { throw "Backup decryption did not reject a truncated archive." }

    Write-Output "Backup crypto checks passed: multi-chunk round-trip, authenticated context, wrong-key/tamper/truncation rejection, and plaintext removal after failed decryption."
}
finally {
    Remove-Item -LiteralPath $testRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Module backup-crypto -ErrorAction SilentlyContinue
}
