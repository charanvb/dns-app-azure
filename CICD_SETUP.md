# GitHub Actions CI/CD Setup Guide

Your CI/CD pipeline is **configured and ready**! This guide explains what happens automatically.

---

## 🚀 What Happens on Push

When you push to `main` branch, the workflow automatically:

1. ✅ **Detects changes** in:
   - `app/**` (FastAPI backend)
   - `frontend/**` (React frontend)
   - `dns_engine/**` (DNS logic)
   - `templates/**` (fallback templates)
   - `Dockerfile` (container config)
   - `requirements.txt` (Python deps)

2. ✅ **Builds multi-stage Docker image** in Azure Container Registry:
   - Stage 1: Builds React frontend with Node.js
   - Stage 2: Builds Python dependencies
   - Stage 3: Combines both into runtime image

3. ✅ **Deploys to Container App** with:
   - 0.5 CPU cores
   - 1.0 GB memory (optimized for 12k zones)
   - Environment variables set
   - Managed Identity configured

4. ✅ **Verifies deployment** with health check

---

## 📋 Required GitHub Secrets

Your repository needs these secrets (already configured):

| Secret | Description |
|--------|-------------|
| `AZURE_CLIENT_ID` | Service Principal ID |
| `AZURE_CLIENT_SECRET` | Service Principal password |
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |

### Check if secrets exist:
1. Go to **GitHub repo** → **Settings** → **Secrets and variables** → **Actions**
2. Verify all 4 secrets are listed

### Add missing secrets:
```powershell
# Get Service Principal details
az ad sp list --display-name "your-sp-name" --query "[0].[appId,displayName]" -o tsv

# Create new secret (if needed)
az ad sp create-for-rbac --name "dns-app-deploy" --role contributor --scopes /subscriptions/<sub-id>/resourceGroups/<rg>
```

---

## ⚙️ Required Azure Container App Environment Variables

These must be set in your Container App (the workflow sets some, but these are persistent):

| Variable | Value | Set By |
|----------|-------|--------|
| `DNS_SUBSCRIPTION_ID` | Your Azure subscription ID | **Manual** (see below) |
| `DNS_RESOURCE_GROUP` | Resource group with DNS zones | **Manual** (see below) |
| `APP_NAME` | Azure DNS Portal | Workflow ✅ |
| `APP_VERSION` | 2.0.0 | Workflow ✅ |
| `ENVIRONMENT` | production | Workflow ✅ |

### Set DNS environment variables (one-time setup):

```powershell
az containerapp update \
  --name bnlwe-fs01-n-00000-dns-ca \
  --resource-group bnlwe-fs01-n-00000-cloudbau-rg \
  --set-env-vars \
    "DNS_SUBSCRIPTION_ID=<your-subscription-id>" \
    "DNS_RESOURCE_GROUP=<your-dns-resource-group>"
```

### Verify environment variables:

```powershell
az containerapp show \
  --name bnlwe-fs01-n-00000-dns-ca \
  --resource-group bnlwe-fs01-n-00000-cloudbau-rg \
  --query properties.template.containers[0].env
```

---

## 🎯 How to Deploy

### Automatic Deployment (Recommended)

Just push to `main`:

```bash
git add .
git commit -m "Update DNS portal"
git push origin main
```

**GitHub Actions will:**
- Build the image in ~5-8 minutes
- Deploy to Container App automatically
- Run health check verification

### Manual Deployment (Workflow Dispatch)

Trigger manually without pushing:

1. Go to **GitHub repo** → **Actions** → **Build and Deploy**
2. Click **Run workflow** → Select `main` branch → **Run workflow**

---

## 📊 Monitor Deployment

### View workflow progress:

1. Go to **GitHub repo** → **Actions**
2. Click on the latest workflow run
3. Watch real-time logs for each step

### Check deployment status:

```powershell
# View Container App logs
az containerapp logs show \
  --name bnlwe-fs01-n-00000-dns-ca \
  --resource-group bnlwe-fs01-n-00000-cloudbau-rg \
  --follow

# Check health
curl https://bnlwe-fs01-n-00000-dns-ca.azurecontainerapps.io/api/health
```

---

## 🔧 Workflow Details

### Build Step (ACR Build)

```yaml
- name: Build and push multi-stage image using ACR
  run: |
    az acr build \
      --registry bnlwecloudbauacr01 \
      --image dns-portal:${{ github.sha }} \
      --image dns-portal:latest \
      --file Dockerfile \
      .
```

**Why ACR build?**
- ✅ Faster than local Docker build
- ✅ Better for multi-stage builds (Node.js + Python)
- ✅ No need to install Docker on runner
- ✅ Direct push to ACR (no intermediate registry)

### Deploy Step

```yaml
- name: Deploy to Container Apps
  run: |
    az containerapp update \
      --name bnlwe-fs01-n-00000-dns-ca \
      --resource-group bnlwe-fs01-n-00000-cloudbau-rg \
      --image bnlwecloudbauacr01.azurecr.io/dns-portal:${{ github.sha }} \
      --cpu 0.5 \
      --memory 1.0Gi \
      --set-env-vars \
        "APP_NAME=Azure DNS Portal" \
        "APP_VERSION=2.0.0" \
        "ENVIRONMENT=production"
```

**What it does:**
- ✅ Updates container image to new version
- ✅ Sets CPU to 0.5 cores (sufficient)
- ✅ Sets memory to 1.0 GB (for 12k zones)
- ✅ Updates environment variables

### Verification Step

```yaml
- name: Verify deployment
  run: |
    APP_URL=$(az containerapp show ... | query fqdn)
    curl -sf "https://$APP_URL/api/health"
```

**What it checks:**
- ✅ App is accessible
- ✅ Health endpoint returns 200
- ✅ Deployment succeeded

---

## 🐛 Troubleshooting

### Build fails with "No space left on device"

**Cause:** Large multi-stage build  
**Fix:** Already handled - we use `az acr build` which has more space

### Deploy fails with "Image not found"

**Cause:** ACR image pull failed  
**Fix:** Check Managed Identity has `AcrPull` role:

```powershell
$IDENTITY_ID=$(az containerapp show \
  --name bnlwe-fs01-n-00000-dns-ca \
  --resource-group bnlwe-fs01-n-00000-cloudbau-rg \
  --query identity.principalId -o tsv)

az role assignment create \
  --assignee $IDENTITY_ID \
  --role AcrPull \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.ContainerRegistry/registries/bnlwecloudbauacr01
```

### Health check timeout

**Cause:** App takes >60 seconds to start  
**Fix:** Not a failure - app may still be starting. Check manually after 2 minutes.

### "Error: DNS_SUBSCRIPTION_ID not set"

**Cause:** Missing environment variable  
**Fix:** Set it in Container App (see "Set DNS environment variables" above)

---

## 🔄 Rollback Process

If deployment fails, rollback to previous version:

### Option 1: Via GitHub Actions

1. Go to **Actions** → Find last successful workflow
2. Click **Re-run all jobs**

### Option 2: Via Azure CLI

```powershell
# List available images
az acr repository show-tags \
  --name bnlwecloudbauacr01 \
  --repository dns-portal \
  --orderby time_desc \
  --top 5

# Deploy specific version
az containerapp update \
  --name bnlwe-fs01-n-00000-dns-ca \
  --resource-group bnlwe-fs01-n-00000-cloudbau-rg \
  --image bnlwecloudbauacr01.azurecr.io/dns-portal:<previous-sha>
```

### Option 3: Via Azure Portal

1. **Container Apps** → Your app → **Revision management**
2. Select previous revision → **Activate**

---

## 📈 Deployment Metrics

**Typical deployment timeline:**

| Step | Duration | Status |
|------|----------|--------|
| Checkout code | ~10s | ✅ |
| Azure login | ~5s | ✅ |
| ACR build (multi-stage) | ~5-8 min | ✅ |
| Configure registry | ~3s | ✅ |
| Deploy to Container App | ~30s | ✅ |
| Health check | ~10s | ✅ |
| **Total** | **~6-9 minutes** | ✅ |

---

## 🎓 Best Practices

### 1. Use Pull Requests
```bash
git checkout -b feature/my-changes
git push origin feature/my-changes
# Create PR → Merge to main → Auto-deploy
```

### 2. Tag Releases
```bash
git tag -a v2.0.0 -m "Phase 1 complete"
git push origin v2.0.0
```

### 3. Monitor First Deployment
After first push, watch:
- GitHub Actions logs
- Azure Container App logs
- Health check endpoint

### 4. Test Before Merging
Test locally first:
```bash
docker build -t dns-app:test .
docker run -p 8000:8000 dns-app:test
```

---

## 📚 Additional Resources

- **Workflow file**: `.github/workflows/deploy.yml`
- **Dockerfile**: `Dockerfile` (multi-stage build)
- **Deployment guide**: `AZURE_DEPLOYMENT.md`
- **Quick start**: `QUICK_START.md`

---

## ✅ Pre-Flight Checklist

Before your first push to `main`:

- [ ] GitHub secrets configured (4 secrets)
- [ ] DNS environment variables set in Container App
- [ ] Managed Identity has `AcrPull` role
- [ ] Managed Identity has `DNS Zone Contributor` role
- [ ] Test commit pushed to verify workflow

---

**Ready to deploy? Just push to `main`!** 🚀

```bash
git add .
git commit -m "Deploy Phase 1 - Modern React UI"
git push origin main
```

Then watch the magic happen in GitHub Actions → Build and Deploy
