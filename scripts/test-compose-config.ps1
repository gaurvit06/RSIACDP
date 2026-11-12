$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$composePath = Join-Path $repoRoot "docker-compose.yml"
$examplePath = Join-Path $repoRoot ".env.example"

if (-not (Test-Path -LiteralPath $composePath -PathType Leaf)) { throw "Compose file is missing: $composePath" }
if (-not (Test-Path -LiteralPath $examplePath -PathType Leaf)) { throw "Environment example is missing: $examplePath" }

$exampleLines = Get-Content -LiteralPath $examplePath
if ($exampleLines | Where-Object { $_ -match '^\s*DATABASE_URL\s*=' }) {
    throw ".env.example must leave DATABASE_URL unset so Compose can derive it from POSTGRES_* values."
}
if (-not ($exampleLines | Where-Object { $_ -match '^\s*BACKUP_ENCRYPTION_KEY\s*=' })) {
    throw ".env.example must document the separate key required to encrypt backups."
}

$probeValues = @{
    POSTGRES_DB = "compose_config_test"
    POSTGRES_USER = "compose_config_user"
    POSTGRES_PASSWORD = "synthetic-compose-password-123"
    NEO4J_PASSWORD = "synthetic-neo4j-compose-password-456"
    JWT_SECRET = "synthetic-only-jwt-secret-not-a-real-deployment-key"
    UPLOAD_ENCRYPTION_KEY = "Y2ktb25seS11cGxvYWQtZW5jcnlwdGlvbi1rZXktMzI="
    INITIAL_INVESTIGATOR_CODE = "synthetic-investigator-compose-setup-code-123456"
    INITIAL_REVIEWER_CODE = "synthetic-reviewer-compose-setup-code-abcdef"
    DATABASE_URL = ""
    CORRECTION_MAX_REQUESTS = "7"
    CORRECTION_WINDOW_SECONDS = "321"
    CORRECTION_LOCKOUT_SECONDS = "654"
    CADDY_PROXY_IP = "172.30.0.42"
    WEB_PROXY_IP = "172.30.0.43"
    FORWARDED_ALLOW_IPS = ""
    VITE_API_URL = ""
    MAX_UPLOAD_BYTES = "2097152"
}
$previousValues = @{}
foreach ($name in $probeValues.Keys) {
    $previousValues[$name] = [System.Environment]::GetEnvironmentVariable($name, "Process")
}

try {
    $emptyEnvPath = Join-Path ([System.IO.Path]::GetTempPath()) ("rsaicdp-empty-compose-env-" + [guid]::NewGuid().ToString("N"))
    Set-Content -LiteralPath $emptyEnvPath -Value "" -NoNewline
    foreach ($name in @("POSTGRES_PASSWORD", "NEO4J_PASSWORD", "JWT_SECRET", "UPLOAD_ENCRYPTION_KEY", "INITIAL_INVESTIGATOR_CODE", "INITIAL_REVIEWER_CODE")) {
        [System.Environment]::SetEnvironmentVariable($name, "", "Process")
    }
    $missingSecretOutput = & docker compose --env-file $emptyEnvPath -f $composePath config --quiet 2>&1
    $missingSecretExit = $LASTEXITCODE
    $missingSecretText = $missingSecretOutput -join "`n"
    $reportedRequiredSecret = $false
    foreach ($requiredSecret in @("POSTGRES_PASSWORD", "NEO4J_PASSWORD", "JWT_SECRET", "UPLOAD_ENCRYPTION_KEY", "INITIAL_INVESTIGATOR_CODE", "INITIAL_REVIEWER_CODE")) {
        if ($missingSecretText -match [regex]::Escape($requiredSecret)) {
            $reportedRequiredSecret = $true
            break
        }
    }
    if ($missingSecretExit -eq 0 -or -not $reportedRequiredSecret) {
        throw "Compose must reject a configuration that omits required application secrets."
    }
    foreach ($name in $probeValues.Keys) {
        [System.Environment]::SetEnvironmentVariable($name, $probeValues[$name], "Process")
    }
    foreach ($requiredSecret in @("POSTGRES_PASSWORD", "NEO4J_PASSWORD", "JWT_SECRET", "UPLOAD_ENCRYPTION_KEY", "INITIAL_INVESTIGATOR_CODE", "INITIAL_REVIEWER_CODE")) {
        [System.Environment]::SetEnvironmentVariable($requiredSecret, "", "Process")
        $missingSecretOutput = & docker compose --env-file $emptyEnvPath -f $composePath config --quiet 2>&1
        $missingSecretExit = $LASTEXITCODE
        if ($missingSecretExit -eq 0 -or ($missingSecretOutput -join "`n") -notmatch [regex]::Escape($requiredSecret)) {
            throw "Compose must reject a configuration that omits $requiredSecret. Output: $($missingSecretOutput -join ' ')"
        }
        [System.Environment]::SetEnvironmentVariable($requiredSecret, $probeValues[$requiredSecret], "Process")
    }
    $rendered = & docker compose -f $composePath --profile production config --format json
    if ($LASTEXITCODE -ne 0) { throw "docker compose config failed with exit code $LASTEXITCODE" }
    $config = ($rendered -join "`n") | ConvertFrom-Json

    $expectedDatabaseUrl = "postgresql+psycopg://compose_config_user:synthetic-compose-password-123@db:5432/compose_config_test"
    foreach ($serviceName in @("api", "worker")) {
        $actualDatabaseUrl = $config.services.$serviceName.environment.DATABASE_URL
        if ($actualDatabaseUrl -ne $expectedDatabaseUrl) {
            throw "$serviceName DATABASE_URL did not derive from the synthetic POSTGRES_* values."
        }
        if ($config.services.$serviceName.environment.UPLOAD_ENCRYPTION_KEY -ne $probeValues.UPLOAD_ENCRYPTION_KEY) {
            throw "$serviceName did not receive the configured private upload encryption key."
        }
    }

    $apiEnvironment = $config.services.api.environment
    $neo4jHealthCommand = $config.services.neo4j.healthcheck.test[1]
    if ($config.services.neo4j.environment.NEO4J_AUTH -ne "neo4j/$($probeValues.NEO4J_PASSWORD)" -or
        -not $neo4jHealthCommand.Contains('$$NEO4J_AUTH') -or
        -not $neo4jHealthCommand.Contains('$${auth#*/}')) {
        throw "Neo4j health check must derive its login from the configured NEO4J_AUTH credentials."
    }
    if ($config.services.neo4j.image -ne "rsaicdp-neo4j:2026.10.2" -or
        $config.services.neo4j.build.dockerfile -ne "deployment/neo4j/Dockerfile") {
        throw "Compose and hosted Render must use the same versioned Neo4j image definition."
    }
    $expectedThrottleSettings = @{
        CORRECTION_MAX_REQUESTS = "7"
        CORRECTION_WINDOW_SECONDS = "321"
        CORRECTION_LOCKOUT_SECONDS = "654"
    }
    foreach ($setting in $expectedThrottleSettings.Keys) {
        if ($apiEnvironment.$setting -ne $expectedThrottleSettings[$setting]) {
            throw "API container did not receive the configured $setting value."
        }
    }

    $trustedProxyIps = $apiEnvironment.FORWARDED_ALLOW_IPS
    foreach ($address in @("172.30.0.42", "172.30.0.43")) {
        if ($trustedProxyIps -notmatch [regex]::Escape($address)) {
            throw "API forwarded-header trust list does not include configured proxy address $address."
        }
    }
    if ($config.services.web.networks.casework.ipv4_address -ne "172.30.0.43") {
        throw "Web proxy did not receive its configured stable address."
    }
    if ($config.services.caddy.networks.casework.ipv4_address -ne "172.30.0.42") {
        throw "Caddy proxy did not receive its configured stable address."
    }
    if (-not $config.services.web.healthcheck) {
        throw "Web service is missing its health check."
    }
    if ($config.services.web.environment.MAX_UPLOAD_BYTES -ne "2097152") {
        throw "Web proxy did not receive the configured upload limit."
    }
    if ($config.services.web.build.args.VITE_API_URL -ne "") {
        throw "Compose frontend build must default to same-origin API requests."
    }

    $nginxConfig = Get-Content -LiteralPath (Join-Path $repoRoot "frontend/nginx.conf.template") -Raw
    $securityHeaders = Get-Content -LiteralPath (Join-Path $repoRoot "frontend/security-headers.conf") -Raw
    $viteConfig = Get-Content -LiteralPath (Join-Path $repoRoot "frontend/vite.config.ts") -Raw
    $appSource = Get-Content -LiteralPath (Join-Path $repoRoot "frontend/src/App.tsx") -Raw
    $backendDockerIgnore = Get-Content -LiteralPath (Join-Path $repoRoot "backend/.dockerignore")
    $frontendDockerIgnore = Get-Content -LiteralPath (Join-Path $repoRoot "frontend/.dockerignore")
    foreach ($pattern in @(".env", ".venv/", ".pydeps/", "*.db", "private_uploads/")) {
        if ($backendDockerIgnore -notcontains $pattern) { throw "Backend Docker context does not exclude $pattern." }
    }
    foreach ($pattern in @(".env", "node_modules/", "dist/")) {
        if ($frontendDockerIgnore -notcontains $pattern) { throw "Frontend Docker context does not exclude $pattern." }
    }
    if ($nginxConfig -notmatch 'location /api/' -or $nginxConfig -notmatch 'proxy_pass http://\$api_upstream') {
        throw "Nginx is missing the same-origin API proxy route."
    }
    if ($nginxConfig -notmatch 'client_max_body_size \$\{MAX_REQUEST_BODY_KIB\}k' -or
        (Get-Content -LiteralPath (Join-Path $repoRoot "frontend/nginx-entrypoint.sh") -Raw) -notmatch 'value \+ 65536') {
        throw "Nginx request-body limit is not derived from the configured file limit plus bounded multipart overhead."
    }
    if ($viteConfig -notmatch "proxy:\s*\{\s*'/api'" -or $appSource -notmatch "const API = import\.meta\.env\.VITE_API_URL \?\? ''") {
        throw "Frontend default and Vite dev server must use same-origin API requests."
    }
    foreach ($header in @("Content-Security-Policy", "Permissions-Policy", "X-Content-Type-Options", "Referrer-Policy", "X-Frame-Options")) {
        if ($securityHeaders -notmatch [regex]::Escape($header)) { throw "Nginx security header is missing: $header" }
    }
    $caddyConfig = Get-Content -LiteralPath (Join-Path $repoRoot "Caddyfile") -Raw
    if ($caddyConfig -notmatch 'Permissions-Policy' -or $caddyConfig -notmatch 'connect-src ''self''') {
        throw "Caddy is missing the browser security policy headers."
    }

    Write-Output "Compose configuration passed: database URLs, upload encryption key wiring, Neo4j authenticated health, correction throttles, proxy trust, upload limits, web health, same-origin routes, browser headers, and private Docker build contexts are configured."
}
catch {
    $line = $_.InvocationInfo.ScriptLineNumber
    Write-Output "::error title=Compose config check failed::An assertion failed at scripts/test-compose-config.ps1 line $line."
    throw
}
finally {
    if ($emptyEnvPath -and (Test-Path -LiteralPath $emptyEnvPath)) {
        Remove-Item -LiteralPath $emptyEnvPath -Force
    }
    foreach ($name in $previousValues.Keys) {
        [System.Environment]::SetEnvironmentVariable($name, $previousValues[$name], "Process")
    }
}
