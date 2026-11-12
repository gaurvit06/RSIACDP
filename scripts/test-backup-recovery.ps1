param(
    [ValidateSet("Recover", "RejectWrongKey")]
    [string]$ProbeMode,
    [string]$EscrowFile,
    [string]$EncryptedFile,
    [string]$ManifestFile,
    [string]$PlaintextOutput
)

$ErrorActionPreference = "Stop"
$modulePath = Join-Path $PSScriptRoot "backup-crypto.psm1"

if ($ProbeMode) {
    # The child process must obtain its key only from the escrow file. Never
    # accept a key through process arguments or inherited environment state.
    [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $null, "Process")
    [Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", $null, "Process")
    Import-Module $modulePath -Force
    $recoveryKey = Get-BackupEncryptionKey -EnvironmentFile $EscrowFile
    try {
        $rows = @(Get-Content -LiteralPath $ManifestFile)
        $keyRows = @($rows | Where-Object { $_ -match '^# backup_key_id=([0-9a-f]{64})$' })
        $formatRows = @($rows | Where-Object { $_ -eq "# format=RSAICDPBK2" })
        if ($keyRows.Count -ne 1 -or $formatRows.Count -ne 1) {
            throw "Synthetic manifest is missing its format or recovery-key ID."
        }
        $expectedKeyId = ($keyRows[0] -split "=", 2)[1]
        $actualKeyId = Get-BackupKeyId -Key $recoveryKey
        if ($ProbeMode -eq "RejectWrongKey") {
            if ($actualKeyId -ceq $expectedKeyId) { throw "Wrong-key probe unexpectedly received the matching recovery key." }
            if (Test-Path -LiteralPath $PlaintextOutput) { throw "Wrong-key probe produced a plaintext file." }
            Write-Output "Wrong recovery key rejected by manifest key ID before decryption."
            exit 0
        }
        if ($actualKeyId -cne $expectedKeyId) { throw "Escrow key does not match the manifest recovery-key ID." }
        Unprotect-BackupFile -InputPath $EncryptedFile -OutputPath $PlaintextOutput -Context postgres -Key $recoveryKey
        if ([System.IO.File]::ReadAllText($PlaintextOutput) -cne "synthetic recovery drill payload") {
            throw "Recovered plaintext did not match the synthetic source payload."
        }
        Write-Output "Escrow key recovered and authenticated the synthetic backup in a separate process."
    }
    finally {
        [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($recoveryKey)
        Remove-Module backup-crypto -ErrorAction SilentlyContinue
    }
    exit 0
}

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Import-Module $modulePath -Force
$priorBackupKey = [Environment]::GetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", "Process")
$priorUploadKey = [Environment]::GetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", "Process")
$recoveryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("rsaicdp-key-recovery-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $recoveryRoot -Force | Out-Null
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
& icacls.exe $recoveryRoot /inheritance:r /grant:r "$($identity.Name):(OI)(CI)F" /c | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Could not restrict access to the temporary recovery drill directory." }

function New-RandomKey {
    $value = [byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($value)
    return ,$value
}

function Write-Escrow([string]$Path, [byte[]]$Key) {
    Set-Content -LiteralPath $Path -Encoding ascii -Value "BACKUP_ENCRYPTION_KEY=$([Convert]::ToBase64String($Key))"
}

function Write-SyntheticBackup([string]$Name, [byte[]]$Key, [string]$EscrowPath) {
    $source = Join-Path $recoveryRoot "$Name-source.dump"
    $encrypted = Join-Path $recoveryRoot "$Name.dump.enc"
    $manifest = Join-Path $recoveryRoot "$Name-SHA256SUMS.txt"
    [System.IO.File]::WriteAllText($source, "synthetic recovery drill payload")
    Protect-BackupFile -InputPath $source -OutputPath $encrypted -Context postgres -Key $Key
    Remove-Item -LiteralPath $source -Force
    $hash = (Get-FileHash -LiteralPath $encrypted -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content -LiteralPath $manifest -Encoding ascii -Value @(
        "# format=RSAICDPBK2",
        "# backup_key_id=$(Get-BackupKeyId -Key $Key)",
        "$hash  $(Split-Path -Leaf $encrypted)"
    )
    return @{ Encrypted = $encrypted; Manifest = $manifest; Escrow = $EscrowPath }
}

function Invoke-RecoveryChild([string]$Mode, [hashtable]$Backup, [string]$OutputPath) {
    $quotedScript = '"{0}"' -f $PSCommandPath
    $quotedEscrow = '"{0}"' -f $Backup.Escrow
    $quotedEncrypted = '"{0}"' -f $Backup.Encrypted
    $quotedManifest = '"{0}"' -f $Backup.Manifest
    $quotedOutput = '"{0}"' -f $OutputPath
    $child = Start-Process -FilePath (Get-Command pwsh).Source -PassThru -Wait -NoNewWindow -ArgumentList @(
        "-NoProfile", "-File", $quotedScript,
        "-ProbeMode", $Mode,
        "-EscrowFile", $quotedEscrow,
        "-EncryptedFile", $quotedEncrypted,
        "-ManifestFile", $quotedManifest,
        "-PlaintextOutput", $quotedOutput
    )
    if ($child.ExitCode -ne 0) { throw "Separate-process recovery probe '$Mode' failed with exit code $($child.ExitCode)." }
}

$keyA = New-RandomKey
$keyB = New-RandomKey
$outputA = Join-Path $recoveryRoot "recovered-a.dump"
$outputB = Join-Path $recoveryRoot "recovered-b.dump"
try {
    $escrowA = Join-Path $recoveryRoot "escrow-a.env"
    $escrowB = Join-Path $recoveryRoot "escrow-b.env"
    Write-Escrow $escrowA $keyA
    Write-Escrow $escrowB $keyB
    $backupA = Write-SyntheticBackup "key-a" $keyA $escrowA

    Invoke-RecoveryChild "Recover" $backupA $outputA
    if ([System.IO.File]::ReadAllText($outputA) -cne "synthetic recovery drill payload") {
        throw "Key A recovery output did not match the synthetic backup."
    }
    Remove-Item -LiteralPath $outputA -Force

    $wrongKeyBackup = @{ Encrypted = $backupA.Encrypted; Manifest = $backupA.Manifest; Escrow = $escrowB }
    Invoke-RecoveryChild "RejectWrongKey" $wrongKeyBackup $outputA
    if (Test-Path -LiteralPath $outputA) { throw "Wrong recovery key left plaintext behind." }

    # Rotation encrypts new archives under key B while retaining key A escrow
    # so older archives stay recoverable.
    $backupB = Write-SyntheticBackup "key-b" $keyB $escrowB
    Invoke-RecoveryChild "Recover" $backupB $outputB
    if ([System.IO.File]::ReadAllText($outputB) -cne "synthetic recovery drill payload") {
        throw "Key B recovery output did not match the rotated synthetic backup."
    }
    Remove-Item -LiteralPath $outputB -Force
    Invoke-RecoveryChild "Recover" $backupA $outputA
    if ([System.IO.File]::ReadAllText($outputA) -cne "synthetic recovery drill payload") {
        throw "The prior escrow key could not recover its pre-rotation backup."
    }
    Remove-Item -LiteralPath $outputA -Force
    Write-Output "Backup key recovery and rotation checks passed across separate PowerShell processes; old and new synthetic archives both recovered, and wrong-key rejection produced no plaintext."
}
finally {
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($keyA)
    [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($keyB)
    [Environment]::SetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", $priorBackupKey, "Process")
    [Environment]::SetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", $priorUploadKey, "Process")
    Remove-Item -LiteralPath $recoveryRoot -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Module backup-crypto -ErrorAction SilentlyContinue
}
