param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$EnvironmentFile = (Join-Path $PSScriptRoot "../.env"),
    [string]$PdfPath = "",
    [string]$ComposeProjectName = "",
    [switch]$ExerciseNeo4jOutage,
    [switch]$AllowSyntheticWrites
)

$ErrorActionPreference = "Stop"

if (-not $AllowSyntheticWrites) {
    throw "This script creates synthetic accounts, cases, and a correction request. Pass -AllowSyntheticWrites only against a disposable verification database."
}

$base = [Uri]$BaseUrl
if ($base.Scheme -ne "http" -or $base.Host -notin @("localhost", "127.0.0.1", "::1")) {
    throw "Synthetic writes are restricted to a loopback HTTP API."
}
$environment = @{}
if (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf) {
    foreach ($line in Get-Content -LiteralPath $EnvironmentFile) {
        if ($line -match '^\s*#' -or $line -notmatch '^\s*([^=\s]+)=(.*)$') { continue }
        $environment[$Matches[1]] = $Matches[2]
    }
}
$setupCode = $environment["INITIAL_INVESTIGATOR_CODE"]
if ([string]::IsNullOrWhiteSpace($setupCode)) { $setupCode = $env:INITIAL_INVESTIGATOR_CODE }
if ([string]::IsNullOrWhiteSpace($setupCode)) {
    throw "Set INITIAL_INVESTIGATOR_CODE in the environment or provide an environment file containing it."
}

function Invoke-JsonApi([string]$Method, [string]$Path, [object]$Body = $null) {
    $parameters = @{
        Method = $Method
        Uri = "$($base.AbsoluteUri.TrimEnd('/'))$Path"
        Headers = $headers
        ContentType = "application/json"
    }
    if ($null -ne $Body) {
        $parameters.Body = [System.Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Depth 10 -Compress))
    }
    Invoke-RestMethod @parameters
}

function Invoke-DisposableCompose([string[]]$Arguments) {
    $composeArguments = @()
    if (-not [string]::IsNullOrWhiteSpace($ComposeProjectName)) {
        $composeArguments += @("--project-name", $ComposeProjectName)
    }
    if (Test-Path -LiteralPath $EnvironmentFile -PathType Leaf) {
        $composeArguments += @("--env-file", (Resolve-Path -LiteralPath $EnvironmentFile).Path)
    }
    $composeArguments += $Arguments
    & docker compose @composeArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Disposable Compose command failed: docker compose $($Arguments -join ' ')"
    }
}

function Invoke-SyntheticPdfUpload([string]$Path, [string]$Title, [string]$ConsentVersion) {
    $resolvedPath = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
    $client = [System.Net.Http.HttpClient]::new()
    $content = [System.Net.Http.MultipartFormDataContent]::new()
    $stream = [System.IO.File]::OpenRead($resolvedPath)
    $fileContent = [System.Net.Http.StreamContent]::new($stream)
    try {
        $token = ([string]$headers.Authorization) -replace '^Bearer\s+', ''
        $client.DefaultRequestHeaders.Authorization = [System.Net.Http.Headers.AuthenticationHeaderValue]::new("Bearer", $token)
        foreach ($field in @{
            title = $Title
            consent_version = $ConsentVersion
            consent = "true"
            rdap_consent = "false"
        }.GetEnumerator()) {
            $fieldContent = [System.Net.Http.StringContent]::new([string]$field.Value, [System.Text.Encoding]::UTF8)
            $content.Add($fieldContent, [string]$field.Key)
        }
        $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/pdf")
        $content.Add($fileContent, "file", [System.IO.Path]::GetFileName($resolvedPath))
        $response = $client.PostAsync("$($base.AbsoluteUri.TrimEnd('/'))/api/cases/upload", $content).GetAwaiter().GetResult()
        $responseBody = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            throw "Synthetic PDF upload failed with HTTP $([int]$response.StatusCode): $responseBody"
        }
        $responseBody | ConvertFrom-Json
    }
    finally {
        if ($response) { $response.Dispose() }
        $fileContent.Dispose()
        $stream.Dispose()
        $content.Dispose()
        $client.Dispose()
    }
}

$policy = Invoke-RestMethod -Method Get -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/policy"
if ($policy.rdap_enabled) { throw "This local synthetic check requires RDAP to be disabled." }
$runId = [guid]::NewGuid().ToString("N").Substring(0, 10)
$testEmail = "recruiter-$runId@example.com"
$testPassword = [Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(24))
$account = Invoke-RestMethod -Method Post `
    -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/auth/register" `
    -ContentType "application/json" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes((@{
        email = "investigator-$runId@example.com"
        password = $testPassword
        setup_code = $setupCode
    } | ConvertTo-Json -Compress)))
if ($account.user.role -ne "investigator") { throw "First synthetic account did not receive the investigator role." }
$headers = @{ Authorization = "Bearer $($account.access_token)" }
$me = Invoke-JsonApi "Get" "/api/auth/me"
if ($me.role -ne "investigator") { throw "Authenticated role check failed." }

$syntheticText = "Synthetic local verification material. Claimed recruiter email: $testEmail. This fabricated input does not describe a real person or company."
$cases = @()
foreach ($number in 1..2) {
    $case = Invoke-JsonApi "Post" "/api/cases" @{
        title = "Synthetic container verification case $number ($runId)"
        input_kind = "text"
        submitted_text = $syntheticText
        consent_version = $policy.consent_version
        consent = $true
        rdap_consent = $false
    }
    $cases += $case
}

foreach ($case in $cases) {
    $completed = $false
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        $detail = Invoke-JsonApi "Get" "/api/cases/$($case.id)"
        if ($detail.status -eq "completed" -and $detail.processing.status -eq "completed") {
            $completed = $true
            break
        }
        if ($detail.status -eq "failed" -or $detail.processing.status -eq "failed") {
            throw "Synthetic case $($case.case_ref) processing failed."
        }
        Start-Sleep -Seconds 1
    }
    if (-not $completed) { throw "Synthetic case $($case.case_ref) did not complete within 90 seconds." }
    if ($detail.assessment -ne "Insufficient evidence") {
        throw "A fresh local-corpus case must remain Insufficient evidence; got $($detail.assessment)."
    }
    $entity = @($detail.entities | Where-Object { $_.type -eq "email" -and $_.normalized -eq $testEmail }) | Select-Object -First 1
    if (-not $entity) { throw "Expected deterministic email extraction was not persisted." }
    if ($entity.source_location -ne "submitted_text" -or $null -eq $entity.source_start_char -or $entity.source_end_char -le $entity.source_start_char) {
        throw "Extracted email is missing its submitted-text source span."
    }
    $emptyCheck = @($detail.evidence | Where-Object { $_.outcome -eq "no_result" }) | Select-Object -First 1
    if (-not $emptyCheck) { throw "Expected a neutral local evidence-corpus no_result record." }
    Invoke-JsonApi "Post" "/api/cases/$($case.id)/entities/$($entity.id)/review" @{
        status = "confirmed"
        rationale = "Synthetic integration test confirmed this fabricated identifier for link-rule verification."
    } | Out-Null
}

$pdfCase = $null
if (-not [string]::IsNullOrWhiteSpace($PdfPath)) {
    $pdfCase = Invoke-SyntheticPdfUpload $PdfPath "Synthetic PDF upload case ($runId)" $policy.consent_version
    $pdfCompleted = $false
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        $pdfDetail = Invoke-JsonApi "Get" "/api/cases/$($pdfCase.id)"
        if ($pdfDetail.status -eq "completed" -and $pdfDetail.processing.status -eq "completed") {
            $pdfCompleted = $true
            break
        }
        if ($pdfDetail.status -eq "failed" -or $pdfDetail.processing.status -eq "failed") {
            throw "Synthetic PDF case $($pdfCase.case_ref) processing failed."
        }
        Start-Sleep -Seconds 1
    }
    if (-not $pdfCompleted) { throw "Synthetic PDF case $($pdfCase.case_ref) did not complete within 90 seconds." }
    $pdfEntity = @($pdfDetail.entities | Where-Object { $_.type -eq "email" -and $_.value -eq "pdf-case@example.com" }) | Select-Object -First 1
    if (-not $pdfEntity -or $pdfEntity.source_location -ne "pdf_page_1" -or $null -eq $pdfEntity.source_start_char -or $pdfEntity.source_end_char -le $pdfEntity.source_start_char) {
        throw "Synthetic PDF email extraction is missing its page and character-span provenance."
    }
    $uploadEvidence = @($pdfDetail.evidence | Where-Object { $_.source_type -eq "uploaded_file" }) | Select-Object -First 1
    if (-not $uploadEvidence -or $uploadEvidence.details.stored_name -notmatch '^[a-f0-9]{48}\.pdf$') {
        throw "PDF upload was not stored with an opaque private object name."
    }
    if ($pdfDetail.assessment -ne "Insufficient evidence") { throw "Synthetic PDF assessment must remain Insufficient evidence." }
    $pdfReport = Invoke-WebRequest -Method Get -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/cases/$($pdfCase.id)/report?format=markdown" -Headers $headers
    if ($pdfReport.Content.Contains("pdf-case@example.com") -or -not $pdfReport.Content.Contains('pdf\_page\_1') -or $pdfReport.Content -notmatch "Insufficient evidence") {
        throw "PDF report did not preserve escaped page provenance, mask the address, and retain the neutral assessment."
    }
}

$linkResult = Invoke-JsonApi "Post" "/api/cases/$($cases[1].id)/link/refresh"
$link = @($linkResult.links | Where-Object {
    ($_.left_case_id -eq $cases[0].id -and $_.right_case_id -eq $cases[1].id) -or
    ($_.left_case_id -eq $cases[1].id -and $_.right_case_id -eq $cases[0].id)
}) | Select-Object -First 1
if (-not $link -or $link.strength -lt $policy.campaign_link_threshold -or $link.review_status -ne "proposed") {
    throw "Deterministic repeated-email link did not produce a reviewable proposed campaign lead."
}

$campaignGroups = Invoke-JsonApi "Get" "/api/campaigns"
$group = @($campaignGroups | Where-Object {
    $_.case_count -ge 2 -and @($_.cases.id) -contains $cases[0].id -and @($_.cases.id) -contains $cases[1].id
}) | Select-Object -First 1
if (-not $group -or $group.note -notmatch "does not establish wrongdoing") {
    throw "Campaign API did not expose both linked cases with the investigative-lead warning."
}

$graph = $null
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    $graph = Invoke-JsonApi "Get" "/api/graph"
    if ($graph.projection -eq "neo4j") { break }
    Start-Sleep -Seconds 1
}
if ($graph.projection -ne "neo4j") { throw "Neo4j projection did not become current within 60 seconds." }
$emailNode = @($graph.nodes | Where-Object { $_.type -eq "email" }) | Select-Object -First 1
if (-not $emailNode -or $emailNode.label -eq $testEmail) {
    throw "Neo4j graph projection is missing the email node or failed to mask its identifier."
}

if ($ExerciseNeo4jOutage) {
    $stoppedNeo4j = $false
    try {
        Invoke-DisposableCompose @("stop", "neo4j") | Out-Null
        $stoppedNeo4j = $true
        $readyWhileNeo4jStopped = $false
        for ($attempt = 0; $attempt -lt 15; $attempt++) {
            try {
                $ready = Invoke-WebRequest -UseBasicParsing -Method Get -Uri "$($base.AbsoluteUri.TrimEnd('/'))/health/ready" -TimeoutSec 3
                if ($ready.StatusCode -eq 200) { $readyWhileNeo4jStopped = $true; break }
            }
            catch { Start-Sleep -Seconds 1 }
        }
        if (-not $readyWhileNeo4jStopped) { throw "API readiness did not remain healthy while Neo4j was stopped." }
        $fallbackGraph = Invoke-JsonApi "Get" "/api/graph"
        if ($fallbackGraph.projection -ne "postgresql-derived") {
            throw "Graph endpoint did not use its PostgreSQL fallback while Neo4j was stopped."
        }
        foreach ($case in $cases) {
            if (-not (@($fallbackGraph.nodes | Where-Object { $_.type -eq "case" -and $_.case_id -eq $case.id } | Measure-Object).Count)) {
                throw "PostgreSQL fallback graph omitted synthetic case $($case.case_ref)."
            }
        }
    }
    finally {
        if ($stoppedNeo4j) { Invoke-DisposableCompose @("start", "neo4j") | Out-Null }
    }

    $recoveredGraph = $null
    for ($attempt = 0; $attempt -lt 90; $attempt++) {
        try {
            $recoveredGraph = Invoke-JsonApi "Get" "/api/graph"
            if ($recoveredGraph.projection -eq "neo4j") { break }
        }
        catch { }
        Start-Sleep -Seconds 1
    }
    if (-not $recoveredGraph -or $recoveredGraph.projection -ne "neo4j") {
        throw "Neo4j did not recover to the current projection after restart."
    }
    foreach ($case in $cases) {
        if (-not (@($recoveredGraph.nodes | Where-Object { $_.type -eq "case" -and $_.case_id -eq $case.id } | Measure-Object).Count)) {
            throw "Recovered Neo4j projection omitted synthetic case $($case.case_ref)."
        }
    }
    $graph = $recoveredGraph
}

$report = Invoke-WebRequest -Method Get `
    -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/cases/$($cases[0].id)/report?format=markdown" `
    -Headers $headers
if ($report.Content -notmatch "Insufficient evidence" -or $report.Content.Contains($testEmail)) {
    throw "Markdown report did not preserve the neutral finding and mask the synthetic email."
}

$correction = Invoke-RestMethod -Method Post `
    -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/corrections" `
    -ContentType "application/json" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes((@{
        case_ref = $cases[0].case_ref
        requester_email = "correction-$runId@example.com"
        description = "Synthetic test request to verify the correction intake and status workflow."
    } | ConvertTo-Json -Compress)))
$received = Invoke-RestMethod -Method Post `
    -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/corrections/$($correction.request_ref)/status" `
    -ContentType "application/json" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes((@{ status_token = $correction.status_token } | ConvertTo-Json -Compress)))
if ($received.status -ne "received" -or $received.PSObject.Properties.Name -contains "resolution") {
    throw "Public correction status did not stay token-protected and privacy-limited."
}
Invoke-JsonApi "Patch" "/api/corrections/$($correction.request_ref)" @{
    status = "investigating"
    resolution = "Synthetic integration review started; no case edit was requested or made."
} | Out-Null
$investigating = Invoke-RestMethod -Method Post `
    -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/corrections/$($correction.request_ref)/status" `
    -ContentType "application/json" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes((@{ status_token = $correction.status_token } | ConvertTo-Json -Compress)))
if ($investigating.status -ne "investigating") { throw "Public correction status did not reflect the persisted investigator transition." }
$correctedValue = "corrected-$runId@example.com"
$caseBeforeCorrection = Invoke-JsonApi "Get" "/api/cases/$($cases[0].id)"
$entityToCorrect = @($caseBeforeCorrection.entities | Where-Object { $_.type -eq "email" -and $_.normalized -eq $testEmail }) | Select-Object -First 1
if (-not $entityToCorrect) { throw "Correction E2E could not find the confirmed synthetic email entity." }
$appliedCorrection = Invoke-JsonApi "Post" "/api/corrections/$($correction.request_ref)/apply" @{
    entity_id = $entityToCorrect.id
    entity_action = "correct"
    corrected_value = $correctedValue
    resolution = "Synthetic E2E correction changed a fabricated email identifier and verified link recalculation."
}
if ($appliedCorrection.status -ne "resolved") { throw "Applying the synthetic correction did not resolve the request." }
$resolved = Invoke-RestMethod -Method Post `
    -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/corrections/$($correction.request_ref)/status" `
    -ContentType "application/json" `
    -Body ([System.Text.Encoding]::UTF8.GetBytes((@{ status_token = $correction.status_token } | ConvertTo-Json -Compress)))
if ($resolved.status -ne "resolved" -or $resolved.PSObject.Properties.Name -contains "resolution") {
    throw "Token-protected public correction status did not reflect resolution without disclosing investigator notes."
}
$correctedDetail = Invoke-JsonApi "Get" "/api/cases/$($cases[0].id)"
$correctedEntity = @($correctedDetail.entities | Where-Object { $_.id -eq $entityToCorrect.id }) | Select-Object -First 1
if (-not $correctedEntity -or $correctedEntity.normalized -ne $correctedValue -or $correctedEntity.review_status -ne "confirmed") {
    throw "Correction did not persist the corrected normalized email as a confirmed entity."
}
if (-not (@($correctedDetail.timeline | Where-Object { $_.action -eq "correction_applied" }).Count) -or
    -not (@($correctedDetail.timeline | Where-Object { $_.action -eq "system_findings_recomputed" }).Count)) {
    throw "Correction application and findings recalculation were not recorded in the case timeline."
}
$correctedReport = Invoke-RestMethod -Method Get -Uri "$($base.AbsoluteUri.TrimEnd('/'))/api/cases/$($cases[0].id)/report" -Headers $headers
if (($correctedReport | ConvertTo-Json -Depth 30 -Compress).Contains($testEmail) -or
    ($correctedReport | ConvertTo-Json -Depth 30 -Compress).Contains($correctedValue)) {
    throw "Corrected report exposed a raw synthetic email identifier."
}
$correctedGraph = $null
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    $correctedGraph = Invoke-JsonApi "Get" "/api/graph"
    $relatedEdge = @($correctedGraph.edges | Where-Object {
        $_.kind -eq "proposed_campaign_link" -and
        (($_.from -eq "case:$($cases[0].id)" -and $_.to -eq "case:$($cases[1].id)") -or
         ($_.from -eq "case:$($cases[1].id)" -and $_.to -eq "case:$($cases[0].id)"))
    }) | Select-Object -First 1
    if ($correctedGraph.projection -eq "neo4j" -and $relatedEdge -and
        $relatedEdge.review_status -eq "low_signal" -and $relatedEdge.strength -lt $policy.campaign_link_threshold) { break }
    Start-Sleep -Seconds 1
}
if ($correctedGraph.projection -ne "neo4j" -or -not $relatedEdge -or
    $relatedEdge.review_status -ne "low_signal" -or $relatedEdge.strength -ge $policy.campaign_link_threshold) {
    throw "Neo4j did not receive the below-threshold domain-only link after the exact email identifier was corrected."
}

Write-Output "Compose end-to-end verification passed: investigator registration/auth, consented PostgreSQL case intake, worker processing, source-span extraction, neutral local evidence, deterministic exact-email campaign lead, current Neo4j projection with masked identifier, redacted Markdown report, token-protected correction status, actual entity correction, finding recalculation, audit timeline, and below-threshold link recalculation in Neo4j."
Write-Output "Synthetic case references: $($cases[0].case_ref), $($cases[1].case_ref); campaign rule: $($link.rule_version); link strength: $($link.strength); graph projection: $($graph.projection)."
if ($pdfCase) { Write-Output "Synthetic private PDF case reference: $($pdfCase.case_ref); PDF page/span provenance and report redaction verified." }
if ($ExerciseNeo4jOutage) { Write-Output "Synthetic Neo4j outage/recovery verification passed: PostgreSQL-backed readiness and graph fallback stayed available, then Neo4j returned with both synthetic cases." }
