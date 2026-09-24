# ============================================================
# Pre-deployment verification script - Naukri CRM HCP Module
# Run this from the repo root: D:\naukri-crm-hcp
#   powershell -ExecutionPolicy Bypass -File .\verify-before-deploy.ps1
# ============================================================

$ErrorActionPreference = "Continue"
$results = @()

if ($PSScriptRoot) {
    $repoRoot = $PSScriptRoot
} else {
    $repoRoot = (Get-Location).Path
}

if (-not (Test-Path "$repoRoot\backend") -or -not (Test-Path "$repoRoot\frontend")) {
    Write-Host "ERROR: Run this from D:\naukri-crm-hcp (repo root) - backend\ and frontend\ not found under $repoRoot" -ForegroundColor Red
    exit 1
}

function Add-Result($name, $passed, $detail = "") {
    $script:results += [PSCustomObject]@{
        Check  = $name
        Status = if ($passed) { "PASS" } else { "FAIL" }
        Detail = $detail
    }
}

function Write-Section($title) {
    Write-Host ""
    Write-Host "==================================================" -ForegroundColor Cyan
    Write-Host " $title" -ForegroundColor Cyan
    Write-Host "==================================================" -ForegroundColor Cyan
}

# ------------------------------------------------------------
# BACKEND CHECKS
# ------------------------------------------------------------
Write-Section "BACKEND"

Set-Location "$repoRoot\backend"

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Add-Result "Backend venv exists" $true
} else {
    Add-Result "Backend venv exists" $false "venv folder not found in backend\"
}

. .\venv\Scripts\Activate.ps1

Write-Host "`nRunning pip check..." -ForegroundColor Yellow
$pipCheckOutput = pip check 2>&1
if ($LASTEXITCODE -eq 0) {
    Add-Result "pip dependency conflicts" $true
} else {
    Add-Result "pip dependency conflicts" $false ($pipCheckOutput -join "; ")
}

$requiredEnvKeys = @(
    "DATABASE_URL", "JWT_SECRET_KEY", "JWT_REFRESH_SECRET", "GROQ_API_KEY"
)
if (Test-Path ".\.env") {
    $envContent = Get-Content ".\.env" -Raw
    $missingKeys = @()
    foreach ($key in $requiredEnvKeys) {
        if ($envContent -notmatch "(?m)^\s*$key\s*=") {
            $missingKeys += $key
        }
    }
    if ($missingKeys.Count -eq 0) {
        Add-Result "backend\.env has required keys" $true
    } else {
        Add-Result "backend\.env has required keys" $false "Missing: $($missingKeys -join ', ')"
    }
} else {
    Add-Result "backend\.env exists" $false "No .env file found in backend\"
}

Write-Host "`nChecking app imports cleanly..." -ForegroundColor Yellow
$importCheck = python -c "from app.main import app; print('IMPORT_OK')" 2>&1
if ($importCheck -match "IMPORT_OK") {
    Add-Result "Backend app imports cleanly" $true
} else {
    Add-Result "Backend app imports cleanly" $false ($importCheck -join "; ")
}

Write-Host "`nRunning pytest -v (this may take a bit)..." -ForegroundColor Yellow
$pytestOutput = pytest -v 2>&1
$pytestOutput | Out-File "$repoRoot\pytest-last-run.log"
if ($LASTEXITCODE -eq 0) {
    $summaryLine = ($pytestOutput | Select-String "passed").ToString()
    Add-Result "Backend test suite (pytest)" $true $summaryLine
} else {
    Add-Result "Backend test suite (pytest)" $false "See pytest-last-run.log for full output"
}

deactivate

# ------------------------------------------------------------
# FRONTEND CHECKS
# ------------------------------------------------------------
Write-Section "FRONTEND"

Set-Location "$repoRoot\frontend"

if (Test-Path ".\node_modules") {
    Add-Result "Frontend dependencies installed" $true
} else {
    Add-Result "Frontend dependencies installed" $false "Run 'npm install' in frontend\ first"
}

Write-Host "`nRunning npm run build..." -ForegroundColor Yellow
$buildOutput = npm run build 2>&1
$buildOutput | Out-File "$repoRoot\frontend-build-last-run.log"
if ($LASTEXITCODE -eq 0) {
    Add-Result "Frontend production build" $true
} else {
    Add-Result "Frontend production build" $false "See frontend-build-last-run.log for full output"
}

$pkgJson = Get-Content ".\package.json" -Raw | ConvertFrom-Json
if ($pkgJson.scripts.PSObject.Properties.Name -contains "lint") {
    Write-Host "`nRunning npm run lint..." -ForegroundColor Yellow
    $lintOutput = npm run lint 2>&1
    if ($LASTEXITCODE -eq 0) {
        Add-Result "Frontend lint" $true
    } else {
        Add-Result "Frontend lint" $false (($lintOutput | Select-Object -Last 10) -join "; ")
    }
} else {
    Add-Result "Frontend lint" $true "No lint script defined - skipped"
}

# ------------------------------------------------------------
# GIT / SECRETS HYGIENE CHECKS
# ------------------------------------------------------------
Write-Section "GIT / SECRETS HYGIENE"

Set-Location $repoRoot

$trackedEnvFiles = git ls-files 2>&1 | Select-String "\.env$"
if ($trackedEnvFiles) {
    Add-Result ".env files not committed to git" $false "Tracked: $($trackedEnvFiles -join ', ')"
} else {
    Add-Result ".env files not committed to git" $true
}

if (Test-Path ".\.gitignore") {
    $gitignore = Get-Content ".\.gitignore" -Raw
    $requiredIgnores = @("venv", ".env", "node_modules")
    $missingIgnores = $requiredIgnores | Where-Object { $gitignore -notmatch [regex]::Escape($_) }
    if ($missingIgnores.Count -eq 0) {
        Add-Result ".gitignore covers secrets/deps" $true
    } else {
        Add-Result ".gitignore covers secrets/deps" $false "Missing patterns for: $($missingIgnores -join ', ')"
    }
} else {
    Add-Result ".gitignore exists" $false "No .gitignore found at repo root"
}

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------
Write-Section "SUMMARY"

$results | ForEach-Object {
    $color = if ($_.Status -eq "PASS") { "Green" } else { "Red" }
    Write-Host ("[{0}] {1}" -f $_.Status, $_.Check) -ForegroundColor $color
    if ($_.Detail -and $_.Status -eq "FAIL") {
        Write-Host ("        -> {0}" -f $_.Detail) -ForegroundColor DarkYellow
    }
}

$failCount = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
Write-Host ""
if ($failCount -eq 0) {
    Write-Host "All $($results.Count) automated checks passed." -ForegroundColor Green
} else {
    Write-Host "$failCount of $($results.Count) checks FAILED - fix these before deploying." -ForegroundColor Red
}

Write-Host ""
Write-Host "NOTE: This script cannot catch every bug - specifically, a JS function" -ForegroundColor DarkYellow
Write-Host "that's called but doesn't exist on an object only shows up when that" -ForegroundColor DarkYellow
Write-Host "exact button is clicked. Manually click through login, HCP list, log" -ForegroundColor DarkYellow
Write-Host "interaction (with and without follow-up), and interaction history" -ForegroundColor DarkYellow
Write-Host "at least once before going live." -ForegroundColor DarkYellow

Set-Location $repoRoot