# Script to create Pull Requests for awesome lists
# Requires: GitHub CLI (gh) installed and authenticated

Write-Host "Creating Pull Requests for QakeAPI in awesome lists..." -ForegroundColor Green

# Check if GitHub CLI is installed
$ghInstalled = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghInstalled) {
    Write-Host "GitHub CLI (gh) is not installed." -ForegroundColor Red
    Write-Host "Install it from: https://cli.github.com/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative: Fork repositories manually and create PRs via web interface" -ForegroundColor Yellow
    exit 1
}

# Check if authenticated
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "GitHub CLI is not authenticated. Run: gh auth login" -ForegroundColor Red
    exit 1
}

# Awesome Python
Write-Host "`n=== Awesome Python ===" -ForegroundColor Cyan
Set-Location ../awesome-python

# Fork repository
Write-Host "Forking awesome-python..." -ForegroundColor Yellow
gh repo fork vinta/awesome-python --clone=false

# Get forked repo URL
$forkUrl = gh repo view --json owner,name -q '{owner.login}/{name}'
Write-Host "Forked repo: $forkUrl" -ForegroundColor Green

# Add fork as remote
git remote remove fork 2>$null
git remote add fork "https://github.com/$forkUrl.git"

# Push branch
Write-Host "Pushing branch to fork..." -ForegroundColor Yellow
git push fork add-qakeapi

# Create PR
Write-Host "Creating Pull Request..." -ForegroundColor Yellow
gh pr create --repo vinta/awesome-python --base master --head "$forkUrl:add-qakeapi" `
    --title "Add QakeAPI to Web Frameworks section" `
    --body "Add QakeAPI - Modern asynchronous web framework built from scratch using only Python standard library.

**Key Features:**
- Zero external dependencies for core functionality
- Full ASGI support
- Built-in authentication, CORS, rate limiting
- Automatic OpenAPI documentation
- WebSocket support

**Links:**
- GitHub: https://github.com/Craxti/qakeapi
- PyPI: https://pypi.org/project/qakeapi/

This framework is unique in that all core functionality is implemented independently without external dependencies, making it educational and lightweight."

# Awesome ASGI
Write-Host "`n=== Awesome ASGI ===" -ForegroundColor Cyan
Set-Location ../awesome-asgi

# Fork repository
Write-Host "Forking awesome-asgi..." -ForegroundColor Yellow
gh repo fork florimondmanca/awesome-asgi --clone=false

# Get forked repo URL
$forkUrl = gh repo view --json owner,name -q '{owner.login}/{name}'
Write-Host "Forked repo: $forkUrl" -ForegroundColor Green

# Add fork as remote
git remote remove fork 2>$null
git remote add fork "https://github.com/$forkUrl.git"

# Push branch
Write-Host "Pushing branch to fork..." -ForegroundColor Yellow
git push fork add-qakeapi

# Create PR
Write-Host "Creating Pull Request..." -ForegroundColor Yellow
gh pr create --repo florimondmanca/awesome-asgi --base master --head "$forkUrl:add-qakeapi" `
    --title "Add QakeAPI to Application frameworks section" `
    --body "Add QakeAPI - Modern asynchronous web framework built from scratch using only Python standard library.

**Key Features:**
- Zero dependencies for core functionality
- Full ASGI support
- Built-in authentication, CORS, rate limiting
- Automatic OpenAPI documentation
- WebSocket support
- HTTP and WebSocket protocols

**Links:**
- GitHub: https://github.com/Craxti/qakeapi
- PyPI: https://pypi.org/project/qakeapi/

This framework implements all core functionality independently, making it a great learning resource and lightweight alternative."

Write-Host "`n✅ Done! Pull Requests created." -ForegroundColor Green
Set-Location ../qakeapi

