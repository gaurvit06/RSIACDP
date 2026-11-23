#requires -Version 7.0
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$local = Join-Path $root '.local'
function ProjectPath($name, $alias) {
    $source = (Resolve-Path (Join-Path $env:USERPROFILE "Downloads/$name/$name")).Path
    $short = Join-Path $env:LOCALAPPDATA $alias
    if (!(Test-Path -LiteralPath $short)) {
        New-Item -ItemType Junction -Path $short -Target $source | Out-Null
    }
    if ((Get-Item -LiteralPath $short).Target -ne $source) { throw "Unexpected local alias $short" }
    return $short
}
function StartReference($name, $port, $python, $directory, $arguments) {
    if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
        Write-Output "Port $port already has a listener; skipping $name."
        return
    }
    Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $directory -WindowStyle Hidden -RedirectStandardOutput "$local/$name.log" -RedirectStandardError "$local/$name.err"
}
$forest = ProjectPath 'Fraud-Detection-in-Job-Postings-using-NLP-and-Machine-Learning-main' 'cw-ref-rf'
$market = ProjectPath 'Fake-Job-Detection-And-Hiring-Market-Analysis-main' 'cw-ref-market'
# Make a local-only copy of the UI with the same prediction code and original saved weights.
$ui = Join-Path $local 'market-local-ui.py'
$source = Get-Content -LiteralPath "$market/app/app.py" -Raw
$pattern = '(?ms)^def load_data\(\):.*?(?=^def prepare_dataset\()'
if ([regex]::Matches($source,$pattern).Count -ne 1) { throw 'Unsupported dashboard source layout.' }
$body = "def load_data():`n    return pd.read_csv('Fake_Job_Postings.csv', low_memory=False), 'Local CSV'`n`n"
[IO.File]::WriteAllText($ui, [regex]::Replace($source,$pattern,$body))
StartReference 'flask-reference' 5176 "$forest/.venv/Scripts/python.exe" $forest '-m flask --app app:app run --host 127.0.0.1 --port 5176 --no-reload --no-debugger'
StartReference 'market-reference' 5177 "$market/.venv/Scripts/python.exe" $market "-m streamlit run `"$ui`" --server.address 127.0.0.1 --server.port 5177 --server.headless true --browser.gatherUsageStats false"
StartReference 'nishant-serve' 5178 "$local/nishant-env/Scripts/python.exe" $root '-u scripts/reference_models/nishant.py'
