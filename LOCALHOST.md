# Running on localhost

Hosted deployment is outside the current scope. Use Docker Desktop (Linux containers), Compose 2.24.4 or newer (supports `!override`), and PowerShell 7. The frontend, API, worker, PostgreSQL and Neo4j run locally; no LLM, cloud account or paid provider is required.

## This computer

The previous application's configuration was recovered from its existing containers on 22 November 2026. Accounts, cases and encrypted uploads remain in the same Docker volumes. Configuration is now in `.local/compose.env` and the Compose project identity is in `.local/state.json`. Both are ignored by Git. Keep these private and preserve the upload encryption key; this workspace is under OneDrive, so its filesystem sync/access settings also apply to these files.

1. Open Docker Desktop and wait for the engine to be running.
2. Open PowerShell 7 in this repository.
3. Run `pwsh -File scripts/local.ps1`.
4. Open <http://localhost:5175/>. Keep using the same hostname when signing in.

The script verifies container health, database readiness, the website, and the website's API proxy. It reuses built images and does not download updates during normal startup.

- Stop without deleting data: `pwsh -File scripts/local.ps1 -Action Stop`
- Inspect services: `pwsh -File scripts/local.ps1 -Action Status`
- Rebuild after code changes: `pwsh -File scripts/local.ps1 -Action Rebuild` (requires image/package downloads when not cached).

Containers restart with Docker unless explicitly stopped. If Docker Desktop is closed or the computer sleeps, the website is unavailable. Ports 5175 and 8001 bind only to this computer. Database and graph ports are internal to the app's Docker network.

## Accounts

Open http://localhost:5175/#home for the public Casework dashboard. Visitors can explore the fictional example without an account. Choose **Sign in** for private cases. The Casework logo returns to the public dashboard. The registration form was removed from the website. Existing accounts still work. For account provisioning, the registration API accepts a JSON POST to `/api/auth/register` with `email`, `password` and an optional `setup_code`. For an empty database, create the first account using the `INITIAL_INVESTIGATOR_CODE` value in `.local/compose.env`. Create a separate reviewer account using `INITIAL_REVIEWER_CODE` after the investigator exists. These bootstrap codes cannot be reused to create more accounts with those roles. Subsequent registrations without a code receive the analyst role. Never post the configuration or codes in Git or public messages.

## Configuration recovery and fresh installations

Do not regenerate keys or change the project identity when recovering existing data. Restore `.local/compose.env` and `.local/state.json` from your private recovery copy. If those copies are lost but the containers still exist, an operator can recover their environment without printing secret values. Deleting Docker volumes or resetting Docker Desktop destroys local data.

For a genuinely new installation, follow the README's `.env.example` instructions, save the configured file as `.local/compose.env`, and create `.local/state.json` containing `{"project":"rsiacdp-local"}`. Set `WEB_ORIGIN=http://localhost:5175`, choose an unused `APP_NETWORK_SUBNET` and matching proxy IPs, and run `-Action Rebuild`. Generate unique secrets; do not copy another installation's secrets. Never run the disposable backup/restore verification script against your working case database.

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
