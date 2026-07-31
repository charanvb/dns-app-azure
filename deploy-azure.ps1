# Quick Azure Deployment Script

# Set your variables
$RG = "your-resource-group"
$ACR = "your-acr-name"
$CONTAINER_APP = "your-container-app-name"
$IMAGE = "dns-app"
$TAG = "v2.0-phase1"

Write-Host "🚀 Deploying DNS App to Azure Container Apps" -ForegroundColor Cyan
Write-Host ""

# Check if logged in
$account = az account show 2>$null
if (-not $account) {
    Write-Host "❌ Not logged in to Azure. Running az login..." -ForegroundColor Red
    az login
}

Write-Host "✅ Logged in to Azure" -ForegroundColor Green
Write-Host ""

# Build and push image using ACR
Write-Host "📦 Building image in Azure Container Registry..." -ForegroundColor Yellow
az acr build --registry $ACR --image "${IMAGE}:${TAG}" --image "${IMAGE}:latest" . --no-logs

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed. Check ACR build logs." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Image built successfully" -ForegroundColor Green
Write-Host ""

# Update Container App
Write-Host "🔄 Updating Container App..." -ForegroundColor Yellow
az containerapp update `
  --name $CONTAINER_APP `
  --resource-group $RG `
  --image "${ACR}.azurecr.io/${IMAGE}:${TAG}" `
  --cpu 0.5 `
  --memory 1.0Gi

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Update failed." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Container App updated" -ForegroundColor Green
Write-Host ""

# Get app URL
$APP_URL = az containerapp show `
  --name $CONTAINER_APP `
  --resource-group $RG `
  --query properties.configuration.ingress.fqdn `
  -o tsv

Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "App URL: https://$APP_URL" -ForegroundColor Cyan
Write-Host "Health Check: https://$APP_URL/api/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Testing health endpoint..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

try {
    $response = Invoke-RestMethod -Uri "https://$APP_URL/api/health"
    Write-Host "✅ Health check passed: $($response.status)" -ForegroundColor Green
    Write-Host "   App: $($response.app_name) v$($response.version)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Health check failed (app may still be starting)" -ForegroundColor Yellow
    Write-Host "   Wait 30 seconds and try: https://$APP_URL/api/health" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Open https://$APP_URL in your browser" -ForegroundColor White
Write-Host "2. Test zone search (min 2 characters)" -ForegroundColor White
Write-Host "3. Monitor logs: az containerapp logs show --name $CONTAINER_APP --resource-group $RG --follow" -ForegroundColor White
