# Scholarport Backend - Fresh EC2 Deployment Script# Scholarport Backend - Fresh EC2 Deployment Script

param(# Run this from Windows PowerShell in your project directory

    [Parameter(Mandatory=$true)]

    [string]$EC2_IP,param(

    [string]$KeyFile = "scholarport-backend.pem"    [Parameter(Mandatory=$true)]

)    [string]$EC2_IP,



$ErrorActionPreference = "Stop"    [string]$KeyFile = "scholarport-backend.pem"

)

Write-Host "`n================================================" -ForegroundColor Cyan

Write-Host "   Scholarport Backend - Fresh Deployment" -ForegroundColor Cyan$ErrorActionPreference = "Stop"

Write-Host "================================================`n" -ForegroundColor Cyan

Write-Host "`n================================================" -ForegroundColor Cyan

if (!(Test-Path $KeyFile)) {Write-Host "   Scholarport Backend - Fresh Deployment" -ForegroundColor Cyan

    Write-Host "[ERROR] SSH key file not found: $KeyFile" -ForegroundColor RedWrite-Host "================================================`n" -ForegroundColor Cyan

    exit 1

}# Validate key file exists

if (!(Test-Path $KeyFile)) {

$EC2_HOST = "ubuntu@$EC2_IP"    Write-Host "ERROR: SSH key file not found" -ForegroundColor Red

    exit 1

Write-Host "[1/6] Creating deployment package..." -ForegroundColor Yellow}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$packageName = "scholarport-deploy-$timestamp.tar.gz"$EC2_HOST = "ubuntu@$EC2_IP"



Write-Host "  - Packaging files..." -ForegroundColor GrayWrite-Host "[1/6] Creating deployment package..." -ForegroundColor Yellow

tar -czf $packageName --exclude=venv --exclude=__pycache__ --exclude=*.pyc --exclude=.git --exclude=db.sqlite3 --exclude=staticfiles --exclude=*.md --exclude=test_*.py --exclude=*_test.py --exclude=debug_*.py --exclude=download_*.py --exclude=check_*.py --exclude=simple_*.py --exclude=detailed_*.py --exclude=demo_*.py --exclude=*.xlsx --exclude=*.html --exclude=firebase_data_*.json --exclude=*.sh --exclude=deploy*.ps1 --exclude=fresh-deploy*.ps1 * 2>$null$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$packageName = "scholarport-deploy-$timestamp.tar.gz"

if ($LASTEXITCODE -ne 0) {

    Write-Host "[ERROR] Failed to create package" -ForegroundColor Red# Create tar package (excluding unnecessary files)

    exit 1Write-Host "  - Packaging files..." -ForegroundColor Gray

}tar -czf $packageName `

    --exclude=venv `

Write-Host "  [OK] Package created: $packageName" -ForegroundColor Green    --exclude=__pycache__ `

    --exclude=*.pyc `

Write-Host "`n[2/6] Uploading files to EC2..." -ForegroundColor Yellow    --exclude=.git `

    --exclude=db.sqlite3 `

Write-Host "  - Uploading code package..." -ForegroundColor Gray    --exclude=staticfiles `

scp -i $KeyFile $packageName ${EC2_HOST}:/tmp/    --exclude=*.md `

if ($LASTEXITCODE -ne 0) {    --exclude=test_*.py `

    Write-Host "[ERROR] Failed to upload package" -ForegroundColor Red    --exclude=*_test.py `

    exit 1    --exclude=debug_*.py `

}    --exclude=download_*.py `

    --exclude=check_*.py `

Write-Host "  - Uploading .env file..." -ForegroundColor Gray    --exclude=simple_*.py `

scp -i $KeyFile .env.production ${EC2_HOST}:/tmp/.env    --exclude=detailed_*.py `

if ($LASTEXITCODE -ne 0) {    --exclude=demo_*.py `

    Write-Host "[ERROR] Failed to upload .env file" -ForegroundColor Red    --exclude=*.xlsx `

    exit 1    --exclude=*.html `

}    --exclude=firebase_data_*.json `

    --exclude=*.sh `

Write-Host "  - Uploading Firebase credentials..." -ForegroundColor Gray    --exclude=deploy*.ps1 `

scp -i $KeyFile scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json ${EC2_HOST}:/tmp/    --exclude=fresh-deploy*.ps1 `

if ($LASTEXITCODE -ne 0) {    * 2>$null

    Write-Host "[ERROR] Failed to upload Firebase credentials" -ForegroundColor Red

    exit 1if ($LASTEXITCODE -ne 0) {

}    Write-Host "ERROR: Failed to create package" -ForegroundColor Red

    exit 1

Write-Host "  - Uploading server setup script..." -ForegroundColor Gray}

scp -i $KeyFile server-commands.sh ${EC2_HOST}:/tmp/

if ($LASTEXITCODE -ne 0) {Write-Host "  ✓ Package created: $packageName" -ForegroundColor Green

    Write-Host "[ERROR] Failed to upload server script" -ForegroundColor Red

    exit 1Write-Host "`n[2/6] Uploading files to EC2..." -ForegroundColor Yellow

}

# Upload deployment package

Write-Host "  [OK] All files uploaded" -ForegroundColor GreenWrite-Host "  - Uploading code package..." -ForegroundColor Gray

scp -i $KeyFile $packageName ${EC2_HOST}:/tmp/

Write-Host "`n[3/6] Setting up directory structure on EC2..." -ForegroundColor Yellowif ($LASTEXITCODE -ne 0) {

ssh -i $KeyFile $EC2_HOST "mkdir -p ~/scholarport-backend ~/backups"    Write-Host "ERROR: Failed to upload package" -ForegroundColor Red

Write-Host "  [OK] Directories created" -ForegroundColor Green    exit 1

}

Write-Host "`n[4/6] Extracting files on EC2..." -ForegroundColor Yellow

$extractCmd = "cd ~/scholarport-backend && tar -xzf /tmp/$packageName && mv /tmp/.env .env && mv /tmp/scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json . && mv /tmp/server-commands.sh . && chmod +x server-commands.sh docker-entrypoint.sh && rm /tmp/$packageName"# Upload sensitive files separately

ssh -i $KeyFile $EC2_HOST $extractCmdWrite-Host "  - Uploading .env file..." -ForegroundColor Gray

scp -i $KeyFile .env.production ${EC2_HOST}:/tmp/.env

if ($LASTEXITCODE -ne 0) {if ($LASTEXITCODE -ne 0) {

    Write-Host "[ERROR] Failed to extract files" -ForegroundColor Red    Write-Host "ERROR: Failed to upload .env file" -ForegroundColor Red

    exit 1    exit 1

}}



Write-Host "  [OK] Files extracted and configured" -ForegroundColor GreenWrite-Host "  - Uploading Firebase credentials..." -ForegroundColor Gray

scp -i $KeyFile scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json ${EC2_HOST}:/tmp/

Write-Host "`n[5/6] Configuration ready..." -ForegroundColor Yellowif ($LASTEXITCODE -ne 0) {

Write-Host "  [OK] Using .env.production settings" -ForegroundColor Green    Write-Host "ERROR: Failed to upload Firebase credentials" -ForegroundColor Red

    exit 1

Remove-Item $packageName -Force}



Write-Host "`n[6/6] Deployment complete!" -ForegroundColor GreenWrite-Host "  - Uploading server setup script..." -ForegroundColor Gray

scp -i $KeyFile server-commands.sh ${EC2_HOST}:/tmp/

Write-Host "`n================================================" -ForegroundColor Cyanif ($LASTEXITCODE -ne 0) {

Write-Host "   DEPLOYMENT UPLOADED SUCCESSFULLY!" -ForegroundColor Green    Write-Host "ERROR: Failed to upload server script" -ForegroundColor Red

Write-Host "================================================`n" -ForegroundColor Cyan    exit 1

}

Write-Host "Next Steps:" -ForegroundColor Yellow

Write-Host "1. Connect to EC2:" -ForegroundColor WhiteWrite-Host "  ✓ All files uploaded" -ForegroundColor Green

Write-Host "   ssh -i $KeyFile $EC2_HOST" -ForegroundColor Cyan

Write-Host ""Write-Host "`n[3/6] Setting up directory structure on EC2..." -ForegroundColor Yellow

Write-Host "2. Run server setup script:" -ForegroundColor Whitessh -i $KeyFile $EC2_HOST "mkdir -p ~/scholarport-backend ~/backups"

Write-Host "   cd ~/scholarport-backend" -ForegroundColor CyanWrite-Host "  ✓ Directories created" -ForegroundColor Green

Write-Host "   ./server-commands.sh" -ForegroundColor Cyan

Write-Host ""Write-Host "`n[4/6] Extracting files on EC2..." -ForegroundColor Yellow

Write-Host "3. Select these options:" -ForegroundColor White$extractCmd = "cd ~/scholarport-backend && tar -xzf /tmp/$packageName && mv /tmp/.env .env && mv /tmp/scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json . && mv /tmp/server-commands.sh . && chmod +x server-commands.sh docker-entrypoint.sh && rm /tmp/$packageName"

Write-Host "   1 - Initial Setup (installs Docker)" -ForegroundColor Cyanssh -i $KeyFile $EC2_HOST $extractCmd

Write-Host "   [EXIT and SSH back in after option 1]" -ForegroundColor Magenta

Write-Host "   2 - Start Services" -ForegroundColor Cyanif ($LASTEXITCODE -ne 0) {

Write-Host "   3 - Setup Database" -ForegroundColor Cyan    Write-Host "ERROR: Failed to extract files" -ForegroundColor Red

Write-Host "   4 - Create Superuser" -ForegroundColor Cyan    exit 1

Write-Host "   8 - Health Check" -ForegroundColor Cyan}

Write-Host ""

Write-Host "API: http://$EC2_IP/api/chat/health/" -ForegroundColor GreenWrite-Host "  ✓ Files extracted and configured" -ForegroundColor Green

Write-Host "Admin: http://$EC2_IP/admin/" -ForegroundColor Green

Write-Host ""Write-Host "`n[5/6] Updating .env with EC2 IP..." -ForegroundColor Yellow

Write-Host "  [OK] Configuration already set in .env.production" -ForegroundColor Green

# Clean up local package
Remove-Item $packageName -Force

Write-Host "`n[6/6] Deployment package ready!" -ForegroundColor Green

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   📦 DEPLOYMENT UPLOADED SUCCESSFULLY!" -ForegroundColor Green
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
Write-Host "6. Select option 6 to verify health check" -ForegroundColor White
Write-Host ""
Write-Host "API will be available at: http://$EC2_IP/api/chat/health/" -ForegroundColor Green
Write-Host "Admin panel at: http://$EC2_IP/admin/" -ForegroundColor Green
Write-Host ""

Write-Host "To create superuser after deployment:" -ForegroundColor Yellow
Write-Host "   docker-compose exec backend python manage.py createsuperuser" -ForegroundColor Cyan
Write-Host ""
