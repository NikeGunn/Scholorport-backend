# Scholarport Backend - Fresh EC2 Deployment Script
# Run this from Windows PowerShell in your project directory

param(
    [Parameter(Mandatory = $true)]
    [string]$EC2_IP,

    [string]$KeyFile = "scholarport-backend.pem"
)

$ErrorActionPreference = "Stop"

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   Scholarport Backend - Fresh Deployment" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Validate key file exists
if (!(Test-Path $KeyFile)) {
    Write-Host "ERROR: SSH key file not found: $KeyFile" -ForegroundColor Red
    exit 1
}

$EC2_HOST = "ubuntu@$EC2_IP"

Write-Host "[1/6] Creating deployment package..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$packageName = "scholarport-deploy-$timestamp.tar.gz"

# Create tar package (excluding unnecessary files)
Write-Host "  - Packaging files..." -ForegroundColor Gray
tar -czf $packageName --exclude=venv --exclude=__pycache__ --exclude=*.pyc --exclude=.git --exclude=db.sqlite3 --exclude=staticfiles --exclude=test_*.py --exclude=*_test.py --exclude=debug_*.py --exclude=download_*.py --exclude=check_*.py --exclude=simple_*.py --exclude=detailed_*.py --exclude=demo_*.py --exclude=*.xlsx --exclude=*.html --exclude=firebase_data_*.json --exclude=deploy*.ps1 --exclude=fresh-deploy*.ps1 --exclude=*.tar.gz * 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create package" -ForegroundColor Red
    exit 1
}

Write-Host "  Package created: $packageName" -ForegroundColor Green

Write-Host "`n[2/6] Uploading files to EC2..." -ForegroundColor Yellow

# Upload deployment package
Write-Host "  - Uploading code package..." -ForegroundColor Gray
scp -i $KeyFile $packageName ${EC2_HOST}:/tmp/
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to upload package" -ForegroundColor Red
    exit 1
}

# Upload sensitive files separately
Write-Host "  - Uploading .env file..." -ForegroundColor Gray
scp -i $KeyFile .env.production ${EC2_HOST}:/tmp/.env
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to upload .env file" -ForegroundColor Red
    exit 1
}

Write-Host "  - Uploading Firebase credentials..." -ForegroundColor Gray
scp -i $KeyFile scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json ${EC2_HOST}:/tmp/
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to upload Firebase credentials" -ForegroundColor Red
    exit 1
}

Write-Host "  - Uploading server setup script..." -ForegroundColor Gray
scp -i $KeyFile server-commands.sh ${EC2_HOST}:/tmp/
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to upload server script" -ForegroundColor Red
    exit 1
}

Write-Host "  All files uploaded" -ForegroundColor Green

Write-Host "`n[3/6] Setting up directory structure on EC2..." -ForegroundColor Yellow
ssh -i $KeyFile -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=30 $EC2_HOST "mkdir -p ~/scholarport-backend ~/backups"
Write-Host "  Directories created" -ForegroundColor Green

Write-Host "`n[4/6] Extracting files on EC2..." -ForegroundColor Yellow
$extractCmd = "cd ~/scholarport-backend && tar -xzf /tmp/$packageName && mv /tmp/.env .env && mv /tmp/scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json . && mv /tmp/server-commands.sh . && chmod +x server-commands.sh docker-entrypoint.sh && rm /tmp/$packageName"
ssh -i $KeyFile -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=30 $EC2_HOST $extractCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to extract files" -ForegroundColor Red
    exit 1
}

Write-Host "  Files extracted and configured" -ForegroundColor Green

Write-Host "`n[5/6] Configuration ready..." -ForegroundColor Yellow
Write-Host "  Using .env.production settings" -ForegroundColor Green

# Clean up local package
Remove-Item $packageName -Force

Write-Host "`n[6/6] Deployment package ready!" -ForegroundColor Green

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   DEPLOYMENT UPLOADED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "================================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Connect to EC2:" -ForegroundColor White
Write-Host "   ssh -i $KeyFile $EC2_HOST" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Run server setup script:" -ForegroundColor White
Write-Host "   cd ~/scholarport-backend" -ForegroundColor Cyan
Write-Host "   ./server-commands.sh" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Select option 1 for initial setup (installs Docker)" -ForegroundColor White
Write-Host "4. Log out and back in after Docker installation" -ForegroundColor White
Write-Host "5. Run ./server-commands.sh again and select option 2 to start services" -ForegroundColor White
Write-Host "6. Select option 3 to setup database and load data" -ForegroundColor White
Write-Host "7. Select option 8 to verify health check" -ForegroundColor White
Write-Host ""
Write-Host "API Endpoints after deployment:" -ForegroundColor Yellow
Write-Host "   Health: http://$EC2_IP/api/chat/health/" -ForegroundColor Green
Write-Host "   Admin:  http://$EC2_IP/admin/" -ForegroundColor Green
Write-Host "   Swagger UI: http://$EC2_IP/api/docs/" -ForegroundColor Green
Write-Host "   ReDoc: http://$EC2_IP/api/redoc/" -ForegroundColor Green
Write-Host ""
