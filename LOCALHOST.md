# Running Casework on localhost

Use Docker Desktop with Linux containers, Docker Compose 2.24.4 or newer and PowerShell 7.1 or newer. Run each command from the repository root. Initial installation downloads container images and packages. After the build, the web app, API, worker, PostgreSQL, Neo4j and OCR all run locally.

## First installation

1. Start Docker Desktop and wait for the engine to finish starting.
2. Run `pwsh -File scripts/local.ps1 -Action Init`. It generates unique database credentials, role setup codes, encryption keys and a Compose project identity. These go in the Git-ignored `.local/` directory. Keep a private recovery copy. The command reuses a complete configuration and stops if it finds a partial or older installation.
3. Run `pwsh -File scripts/local.ps1 -Action Rebuild`. Wait for the readiness message. The website listens on port 5175 and the API on 8001, both on loopback. The databases stay inside Docker.
4. Run `pwsh -File scripts/local.ps1 -Action CreateInvestigator`. Choose a sign-in email and a password of 12–128 characters. The command provisions the first account through the registration API and reads the setup code privately.
5. Open [Casework](http://localhost:5175/) and choose **Sign in**. Use the same hostname throughout the session. Start with the [guided demonstration](FEATURE_WALKTHROUGH.md).

On a clean install the case list starts empty. The guided vacancy walkthrough creates its fictional case and register entry when you give consent. The tracked files in `demo/` let you submit additional cases through the same intake forms used by investigators.

## Existing installation

| Task | Command |
| --- | --- |
| Reopen the workspace with its cases | `pwsh -File scripts/local.ps1 -Action Start` |
| Check service status | `pwsh -File scripts/local.ps1 -Action Status` |
| Stop the services and retain cases and files | `pwsh -File scripts/local.ps1 -Action Stop` |
| Rebuild after a source update | `pwsh -File scripts/local.ps1 -Action Rebuild` |
| Provision the separate first reviewer, after the investigator exists | `pwsh -File scripts/local.ps1 -Action CreateReviewer` |

Sign in with your existing account. The API accepts each privileged setup code once. The website has a public sample and a sign-in form. Additional analyst accounts can be provisioned through the registration API. Stopping Docker Desktop or putting the computer to sleep takes the website offline.

## Configuration and recovery

The launcher reads `.local/state.json` for the original project identity and `.local/compose.env` for its keys. Case records and uploaded files live in the corresponding Docker volumes. Restoring an existing installation requires the original identity, keys and data. Preserve the complete private configuration and volume backups. Deleting volumes, resetting Docker Desktop or replacing the upload key can make evidence unrecoverable.

[.env.example](.env.example) lists available settings. Local Compose enables configured public employer boards for vacancy checks. For an entirely offline presentation, add `OFFICIAL_JOB_BOARDS=` to the private environment file and rerun Start to apply it. RDAP defaults to disabled. If Docker reports a subnet overlap, select an unused private subnet via `APP_NETWORK_SUBNET` and set `WEB_PROXY_IP` to an available address inside it. A custom `FORWARDED_ALLOW_IPS` must match the web proxy and loopback.

## Back up or recover this installation on Windows

The backup contains PostgreSQL and private uploads. Recovery also requires a private copy of `.local/state.json`, `.local/compose.env` (especially the original `UPLOAD_ENCRYPTION_KEY`), and the separate backup encryption key. Keep the configuration and keys in your private recovery store. Keep the encrypted archive set on storage you can recover if the computer fails.

1. Start the application with `scripts/local.ps1`. Open a fresh PowerShell 7.1+ session in the repository for the recovery commands. The backup scripts use the active Compose project, so select the saved project and its two Compose files first. The following commands only inspect the running services.

   ```powershell
   $ErrorActionPreference = 'Stop'
   $repo = (Resolve-Path .).Path
   $state = Get-Content .local/state.json -Raw | ConvertFrom-Json
   if ($state.project -notmatch '^[a-z0-9][a-z0-9_-]+$') { throw 'Invalid project name.' }
   $env:COMPOSE_PROJECT_NAME = $state.project
   $env:COMPOSE_PATH_SEPARATOR = ';'
   $env:COMPOSE_FILE = "$repo\docker-compose.yml;$repo\compose.local.yaml"
   $env:COMPOSE_ENV_FILES = (Resolve-Path .local/compose.env).Path
   docker compose config --quiet
   if ($LASTEXITCODE) { throw 'Invalid local Compose configuration.' }
   docker compose ps
   if ($LASTEXITCODE) { throw 'Could not inspect the selected installation.' }
   ```

   Confirm that the names belong to the installation in `.local/state.json`, the services are healthy, and the web and API ports are 5175 and 8001. This check matters even when another Compose application uses the same service names.

2. In the same shell, enter your backup key from your private recovery store. It must be canonical base64 for 32 random bytes and must differ from the upload key. For the **first backup only**, you can generate a key in a private PowerShell session with `[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))`. Save the displayed value in your recovery store before using it. On restore, use the key saved for that archive. The input below hides the characters as you type or paste.

   ```powershell
   $env:BACKUP_ENCRYPTION_KEY = Read-Host 'Backup encryption key' -MaskInput
   Import-Module ./scripts/backup-crypto.psm1 -Force
   $validatedKey = Get-BackupEncryptionKey -EnvironmentFile $env:COMPOSE_ENV_FILES
   [Security.Cryptography.CryptographicOperations]::ZeroMemory($validatedKey)
   $backupDirectory = Join-Path $env:LOCALAPPDATA 'RSIACDP\backups'
   ```

3. **To take a backup**, run the command below during a short maintenance window. It stops API and worker writes, encrypts the database dump and upload archive, writes their checksum manifest, then restarts the API and worker. Save the two `.enc` files and the `SHA256SUMS-*.txt` manifest from the same timestamp together.

   ```powershell
   & ./scripts/backup.ps1 -BackupDirectory $backupDirectory
   docker compose ps
   ```

4. **To restore**, first choose the exact archive set and the matching saved configuration. Restoring replaces the selected project's current database and uploaded evidence with the selected snapshot. Take a separate backup first if you need to preserve its current state. If you moved the archives, set `$backupDirectory` to their new directory. Run steps 1 and 2, then run the commands below only when ready to replace this installation.

   ```powershell
   $stamp = Read-Host 'Timestamp from the backup manifest (yyyyMMdd-HHmmss-fff)'
   if ($stamp -notmatch '^\d{8}-\d{6}-\d{3}$') { throw 'Check the timestamp in the manifest filename.' }
   $restore = @{
       PostgresDump          = Join-Path $backupDirectory "postgres-$stamp.dump.enc"
       PrivateUploadsArchive = Join-Path $backupDirectory "private-uploads-$stamp.tar.gz.enc"
       ChecksumManifest      = Join-Path $backupDirectory "SHA256SUMS-$stamp.txt"
   }
   & ./scripts/restore.ps1 @restore -ConfirmRestore
   & ./scripts/local.ps1
   ```

   Restore verifies the checksums, recovery key and encrypted contents, restores PostgreSQL and private files, then rebuilds Neo4j. If it fails after writes have been stopped, inspect the error and retry with the chosen complete backup set before resuming case intake. After a successful restore, open an expected case and check its evidence timeline and report. Close the recovery shell to clear its process variables.

## Troubleshooting and limits

- Missing engine: start Docker Desktop and wait before retrying.
- Port collision: stop the conflicting application; do not start a second copy on the same ports.
- Missing images: use `-Action Rebuild`.
- Disk full or read-only Docker storage: free disk space and restart Docker Desktop before retrying. Do not delete case volumes as a cleanup shortcut.
- Missing bootstrap file: follow configuration recovery above. A new password cannot decrypt uploads encrypted with a lost key.
- Empty local corpus: an unknown identifier yields `no_result` and cannot establish that a job is genuine or fraudulent. Add traceable, reviewed local evidence through the investigator workflow. Synthetic evaluation establishes integration behavior only.

Current verification results and outstanding workflow checks are recorded in BUILD_STATUS.md. Localhost availability alone is not proof that every investigation workflow has been verified.
