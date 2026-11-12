$script:BackupMagic = [System.Text.Encoding]::ASCII.GetBytes("RSAICDPBK`u{2}")
$script:BackupChunkBytes = 4MB
$script:BackupTagBytes = 16
$script:BackupSaltBytes = 32
$script:BackupNoncePrefixBytes = 4

function Get-BackupEncryptionKey {
    param([string]$EnvironmentFile = (Join-Path $PSScriptRoot "../.env"))

    $encoded = [Environment]::GetEnvironmentVariable("BACKUP_ENCRYPTION_KEY", "Process")
    if ([string]::IsNullOrWhiteSpace($encoded) -and (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf)) {
        foreach ($line in Get-Content -LiteralPath $EnvironmentFile) {
            if ($line -match '^\s*#' -or $line -notmatch '^\s*BACKUP_ENCRYPTION_KEY=(.*)$') { continue }
            $encoded = $Matches[1]
            break
        }
    }
    if ([string]::IsNullOrWhiteSpace($encoded)) {
        throw "Set BACKUP_ENCRYPTION_KEY in the environment or $EnvironmentFile before backing up or restoring."
    }

    try { $key = [Convert]::FromBase64String($encoded) }
    catch { throw "BACKUP_ENCRYPTION_KEY must be canonical base64 for exactly 32 random bytes." }
    if ($key.Length -ne 32 -or [Convert]::ToBase64String($key) -cne $encoded) {
        throw "BACKUP_ENCRYPTION_KEY must be canonical base64 for exactly 32 random bytes."
    }
    $uploadKeyEncoded = [Environment]::GetEnvironmentVariable("UPLOAD_ENCRYPTION_KEY", "Process")
    if ([string]::IsNullOrWhiteSpace($uploadKeyEncoded) -and (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf)) {
        foreach ($line in Get-Content -LiteralPath $EnvironmentFile) {
            if ($line -match '^\s*#' -or $line -notmatch '^\s*UPLOAD_ENCRYPTION_KEY=(.*)$') { continue }
            $uploadKeyEncoded = $Matches[1]
            break
        }
    }
    if ($uploadKeyEncoded -and $uploadKeyEncoded -ceq $encoded) {
        throw "Use a separate random key for BACKUP_ENCRYPTION_KEY and UPLOAD_ENCRYPTION_KEY."
    }
    return ,$key
}

function Get-BackupKeyId {
    param([Parameter(Mandatory = $true)][byte[]]$Key)
    if ($Key.Length -ne 32) { throw "Backup encryption key must contain exactly 32 bytes." }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return ([Convert]::ToHexString($sha.ComputeHash($Key))).ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Read-ExactBytes {
    param([System.IO.Stream]$Stream, [int]$Count)
    $buffer = [byte[]]::new($Count)
    $offset = 0
    while ($offset -lt $Count) {
        $read = $Stream.Read($buffer, $offset, $Count - $offset)
        if ($read -eq 0) { throw "Encrypted backup is truncated or malformed." }
        $offset += $read
    }
    return ,$buffer
}

function ConvertTo-BigEndianUInt32 {
    param([uint32]$Value)
    $bytes = [BitConverter]::GetBytes($Value)
    if ([BitConverter]::IsLittleEndian) { [Array]::Reverse($bytes) }
    return ,$bytes
}

function ConvertTo-BigEndianUInt64 {
    param([uint64]$Value)
    $bytes = [BitConverter]::GetBytes($Value)
    if ([BitConverter]::IsLittleEndian) { [Array]::Reverse($bytes) }
    return ,$bytes
}

function New-BackupNonce {
    param([byte[]]$Prefix, [uint64]$Index)
    $nonce = [byte[]]::new(12)
    [Array]::Copy($Prefix, 0, $nonce, 0, $Prefix.Length)
    $counter = ConvertTo-BigEndianUInt64 $Index
    [Array]::Copy($counter, 0, $nonce, $Prefix.Length, $counter.Length)
    return ,$nonce
}

function New-BackupFileKey {
    param([byte[]]$MasterKey, [byte[]]$Salt, [string]$Context)
    $extract = $null; $expand = $null; $pseudorandomKey = $null
    try {
        $extract = [System.Security.Cryptography.HMACSHA256]::new($Salt)
        $pseudorandomKey = $extract.ComputeHash($MasterKey)
        $expand = [System.Security.Cryptography.HMACSHA256]::new($pseudorandomKey)
        $info = [System.Text.Encoding]::ASCII.GetBytes("RSAICDPBackupFileKeyV2`0$Context`0`u{1}")
        return ,$expand.ComputeHash($info)
    }
    finally {
        if ($extract) { $extract.Dispose() }
        if ($expand) { $expand.Dispose() }
        if ($pseudorandomKey) { [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($pseudorandomKey) }
    }
}

function New-BackupAssociatedData {
    param([byte[]]$Salt, [byte[]]$Prefix, [string]$Context, [uint64]$Index, [byte]$Flag, [uint32]$Length)
    $contextBytes = [System.Text.Encoding]::UTF8.GetBytes($Context)
    $indexBytes = ConvertTo-BigEndianUInt64 $Index
    $lengthBytes = ConvertTo-BigEndianUInt32 $Length
    $aad = [byte[]]::new($script:BackupMagic.Length + $Salt.Length + $Prefix.Length + $contextBytes.Length + 1 + $indexBytes.Length + 1 + $lengthBytes.Length)
    $offset = 0
    [Array]::Copy($script:BackupMagic, 0, $aad, $offset, $script:BackupMagic.Length); $offset += $script:BackupMagic.Length
    [Array]::Copy($Salt, 0, $aad, $offset, $Salt.Length); $offset += $Salt.Length
    [Array]::Copy($Prefix, 0, $aad, $offset, $Prefix.Length); $offset += $Prefix.Length
    [Array]::Copy($contextBytes, 0, $aad, $offset, $contextBytes.Length); $offset += $contextBytes.Length
    $aad[$offset] = 0; $offset++
    [Array]::Copy($indexBytes, 0, $aad, $offset, $indexBytes.Length); $offset += $indexBytes.Length
    $aad[$offset] = $Flag; $offset++
    [Array]::Copy($lengthBytes, 0, $aad, $offset, $lengthBytes.Length)
    return ,$aad
}

function Protect-BackupFile {
    param(
        [Parameter(Mandatory = $true)][string]$InputPath,
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [Parameter(Mandatory = $true)][ValidateSet("postgres", "uploads")][string]$Context,
        [Parameter(Mandatory = $true)][byte[]]$Key
    )
    if ($Key.Length -ne 32) { throw "Backup encryption key must contain exactly 32 bytes." }
    $sourcePath = [System.IO.Path]::GetFullPath($InputPath)
    $destinationPath = [System.IO.Path]::GetFullPath($OutputPath)
    if ($sourcePath -eq $destinationPath) { throw "Encrypted backup output must differ from its plaintext input." }
    if (Test-Path -LiteralPath $destinationPath) { throw "Encrypted backup output already exists: $destinationPath" }
    $input = $null; $output = $null; $aes = $null; $fileKey = $null; $success = $false
    try {
        $input = [System.IO.File]::OpenRead($sourcePath)
        $output = [System.IO.File]::Open($destinationPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        $salt = [byte[]]::new($script:BackupSaltBytes)
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($salt)
        $prefix = [byte[]]::new($script:BackupNoncePrefixBytes)
        [System.Security.Cryptography.RandomNumberGenerator]::Fill($prefix)
        $output.Write($script:BackupMagic, 0, $script:BackupMagic.Length)
        $output.Write($salt, 0, $salt.Length)
        $output.Write($prefix, 0, $prefix.Length)
        $fileKey = New-BackupFileKey $Key $salt $Context
        $aes = [System.Security.Cryptography.AesGcm]::new($fileKey, $script:BackupTagBytes)
        $buffer = [byte[]]::new($script:BackupChunkBytes)
        [uint64]$index = 0
        while (($length = $input.Read($buffer, 0, $buffer.Length)) -gt 0) {
            if ($index -eq [uint64]::MaxValue) { throw "Backup file exceeds the supported encrypted chunk count." }
            $plain = [byte[]]::new($length); [Array]::Copy($buffer, 0, $plain, 0, $length)
            $lengthBytes = ConvertTo-BigEndianUInt32 ([uint32]$length)
            $frame = [byte[]]::new(5); $frame[0] = 0; [Array]::Copy($lengthBytes, 0, $frame, 1, 4)
            $cipher = [byte[]]::new($length); $tag = [byte[]]::new($script:BackupTagBytes)
            $nonce = New-BackupNonce $prefix $index
            $aad = New-BackupAssociatedData $salt $prefix $Context $index 0 ([uint32]$length)
            $aes.Encrypt($nonce, $plain, $cipher, $tag, $aad)
            $output.Write($frame, 0, $frame.Length); $output.Write($cipher, 0, $cipher.Length); $output.Write($tag, 0, $tag.Length)
            $index++
        }
        $finalFrame = [byte[]]::new(5); $finalFrame[0] = 1
        $finalTag = [byte[]]::new($script:BackupTagBytes)
        $finalNonce = New-BackupNonce $prefix $index
        $finalAad = New-BackupAssociatedData $salt $prefix $Context $index 1 0
        $aes.Encrypt($finalNonce, [byte[]]::new(0), [byte[]]::new(0), $finalTag, $finalAad)
        $output.Write($finalFrame, 0, $finalFrame.Length); $output.Write($finalTag, 0, $finalTag.Length)
        $output.Flush($true)
        $success = $true
    }
    catch {
        throw
    }
    finally {
        if ($aes) { $aes.Dispose() }
        if ($input) { $input.Dispose() }
        if ($output) { $output.Dispose() }
        if ($fileKey) { [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($fileKey) }
        if (-not $success -and (Test-Path -LiteralPath $destinationPath)) { Remove-Item -LiteralPath $destinationPath -Force -ErrorAction SilentlyContinue }
    }
}

function Unprotect-BackupFile {
    param(
        [Parameter(Mandatory = $true)][string]$InputPath,
        [Parameter(Mandatory = $true)][string]$OutputPath,
        [Parameter(Mandatory = $true)][ValidateSet("postgres", "uploads")][string]$Context,
        [Parameter(Mandatory = $true)][byte[]]$Key
    )
    if ($Key.Length -ne 32) { throw "Backup encryption key must contain exactly 32 bytes." }
    $sourcePath = [System.IO.Path]::GetFullPath($InputPath)
    $destinationPath = [System.IO.Path]::GetFullPath($OutputPath)
    if ($sourcePath -eq $destinationPath) { throw "Decrypted output must differ from the encrypted backup input." }
    if (Test-Path -LiteralPath $destinationPath) { throw "Decrypted output already exists: $destinationPath" }
    $input = $null; $output = $null; $aes = $null; $fileKey = $null; $success = $false
    try {
        $input = [System.IO.File]::OpenRead($sourcePath)
        $magic = Read-ExactBytes $input $script:BackupMagic.Length
        if (-not [System.Linq.Enumerable]::SequenceEqual[byte]($magic, $script:BackupMagic)) { throw "Encrypted backup format is invalid." }
        $salt = Read-ExactBytes $input $script:BackupSaltBytes
        $prefix = Read-ExactBytes $input $script:BackupNoncePrefixBytes
        $output = [System.IO.File]::Open($destinationPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        $fileKey = New-BackupFileKey $Key $salt $Context
        $aes = [System.Security.Cryptography.AesGcm]::new($fileKey, $script:BackupTagBytes)
        [uint64]$index = 0
        $sawFinal = $false
        while ($input.Position -lt $input.Length) {
            $frame = Read-ExactBytes $input 5
            $flag = $frame[0]
            $lengthBytes = [byte[]]::new(4); [Array]::Copy($frame, 1, $lengthBytes, 0, 4)
            if ([BitConverter]::IsLittleEndian) { [Array]::Reverse($lengthBytes) }
            $length = [BitConverter]::ToUInt32($lengthBytes, 0)
            if ($flag -eq 0) {
                if ($length -lt 1 -or $length -gt $script:BackupChunkBytes) { throw "Encrypted backup frame length is invalid." }
            } elseif ($flag -eq 1) {
                if ($length -ne 0) { throw "Encrypted backup final frame is invalid." }
                $sawFinal = $true
            } else { throw "Encrypted backup frame type is invalid." }
            $cipher = Read-ExactBytes $input ([int]$length)
            $tag = Read-ExactBytes $input $script:BackupTagBytes
            $plain = [byte[]]::new([int]$length)
            $nonce = New-BackupNonce $prefix $index
            $aad = New-BackupAssociatedData $salt $prefix $Context $index $flag $length
            $aes.Decrypt($nonce, $cipher, $tag, $plain, $aad)
            if ($length -gt 0) { $output.Write($plain, 0, $plain.Length) }
            $index++
            if ($sawFinal) {
                if ($input.Position -ne $input.Length) { throw "Encrypted backup has trailing data." }
                break
            }
        }
        if (-not $sawFinal) { throw "Encrypted backup is missing its authenticated final frame." }
        $output.Flush($true)
        $success = $true
    }
    catch {
        throw
    }
    finally {
        if ($aes) { $aes.Dispose() }
        if ($input) { $input.Dispose() }
        if ($output) { $output.Dispose() }
        if ($fileKey) { [System.Security.Cryptography.CryptographicOperations]::ZeroMemory($fileKey) }
        if (-not $success -and (Test-Path -LiteralPath $destinationPath)) { Remove-Item -LiteralPath $destinationPath -Force -ErrorAction SilentlyContinue }
    }
}

Export-ModuleMember -Function Get-BackupEncryptionKey, Get-BackupKeyId, Protect-BackupFile, Unprotect-BackupFile
