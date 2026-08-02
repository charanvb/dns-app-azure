# Deployment Guide

## Overview

This project uses **branch-based deployment** to manage two Azure Container Apps:

| Branch | Environment | Container App | URL |
|--------|-------------|---------------|-----|
| `main` | **Production** | `bnlwe-fs01-n-00000-dns-ca` | Set after Terraform apply |
| `develop` | **Development** | `bnlwe-fs01-n-00000-dns-ca-dev` | Set after Terraform apply |

Both apps:
- Share the same Azure Container Registry (`bnlwecloudbauacr01`)
- Share the same Container App Environment
- Use the same DNS subscription and resource group (both are TEST for now)
- Are built from the same Docker image
- Run as completely isolated processes

---

## Prerequisites

1. **Terraform State**: Run `infra.yml` workflow at least once to provision infrastructure
2. **GitHub Secrets**: Ensure these are configured in repository settings:
   - `AZURE_CLIENT_ID`
   - `AZURE_CLIENT_SECRET`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
3. **Develop Branch**: Create `develop` branch from `main`

---

## Initial Setup

### Step 1: Apply Terraform to Create Dev Container App

```bash
# Option 1: Run infra.yml workflow in GitHub Actions
# Navigate to: Actions → Terraform Provision → Run workflow

# Option 2: Run Terraform locally
cd terraform
terraform init
terraform plan
terraform apply
```

**What this creates:**
- ✅ Development Container App (`bnlwe-fs01-n-00000-dns-ca-dev`)
- ✅ Managed Identity for dev app (system-assigned)
- ✅ ACR Pull role assignment for dev app's identity
- ✅ Outputs: Both production and dev URLs

### Step 2: Get Terraform Outputs

After `terraform apply` completes:

```bash
cd terraform
terraform output
```

**Expected output:**
```
container_app_fqdn = "https://bnlwe-fs01-n-00000-dns-ca.yellowmushroom-676d4f40.westeurope.azurecontainerapps.io"
container_app_name = "bnlwe-fs01-n-00000-dns-ca"
container_app_dev_fqdn = "https://bnlwe-fs01-n-00000-dns-ca-dev.yellowmushroom-676d4f40.westeurope.azurecontainerapps.io"
container_app_dev_name = "bnlwe-fs01-n-00000-dns-ca-dev"
container_app_dev_principal_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

**Save these URLs!** You'll need them to access the apps.

### Step 3: Configure DNS Permissions for Dev Container App

The dev container app needs the same DNS permissions as production.

**Option A: Use Azure Portal (Recommended)**

1. Copy the `container_app_dev_principal_id` from Terraform output
2. Navigate to Azure Portal → DNS Resource Group (`bnlwe-cc01-d-00000-mic-rg`)
3. Go to **Access control (IAM)** → **Add role assignment**
4. Role: **DNS Zone Contributor**
5. Assign access to: **Managed Identity**
6. Select: **Container App** → `bnlwe-fs01-n-00000-dns-ca-dev`
7. Click **Review + assign**

**Option B: Use Azure CLI**

```bash
# Get the principal ID from Terraform output
DEV_PRINCIPAL_ID=$(cd terraform && terraform output -raw container_app_dev_principal_id)

# Assign DNS Zone Contributor role
az role assignment create \
  --assignee "$DEV_PRINCIPAL_ID" \
  --role "DNS Zone Contributor" \
  --scope "/subscriptions/f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be/resourceGroups/bnlwe-cc01-d-00000-mic-rg"
```

**Verify the assignment:**
```bash
az role assignment list \
  --assignee "$DEV_PRINCIPAL_ID" \
  --scope "/subscriptions/f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be/resourceGroups/bnlwe-cc01-d-00000-mic-rg" \
  --output table
```

### Step 4: Create Develop Branch

```bash
# Create develop branch from main
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop
```

---

## Deployment Workflow

### Deploy to Production (Main Branch)

```bash
git checkout main
# Make changes
git add .
git commit -m "Your commit message"
git push origin main
```

**Result:**
- ✅ Triggers GitHub Actions workflow
- ✅ Builds Docker image
- ✅ Pushes to ACR
- ✅ Deploys to **production** container app
- ✅ Updates: `bnlwe-fs01-n-00000-dns-ca`
- ✅ Sets `ENVIRONMENT=production`

### Deploy to Development (Develop Branch)

```bash
git checkout develop
# Make changes (or merge from main)
git add .
git commit -m "Your commit message"
git push origin develop
```

**Result:**
- ✅ Triggers GitHub Actions workflow
- ✅ Builds Docker image
- ✅ Pushes to ACR
- ✅ Deploys to **development** container app
- ✅ Updates: `bnlwe-fs01-n-00000-dns-ca-dev`
- ✅ Sets `ENVIRONMENT=development`

---

## Workflow Details

The [deploy.yml](.github/workflows/deploy.yml) workflow:

1. **Detects branch** and sets target container app
2. **Builds** multi-stage Docker image (React + FastAPI)
3. **Pushes** to Azure Container Registry
4. **Configures** ACR identity (if needed)
5. **Deploys** to appropriate container app
6. **Verifies** health check endpoint

**Deployment time:** ~6-8 minutes

---

## Testing Strategy

### Recommended Workflow

1. **Develop features on `develop` branch:**
   ```bash
   git checkout develop
   # Make changes
   git commit -m "Feature: Add new functionality"
   git push origin develop
   # → Deploys to dev app
   # → Test at dev URL
   ```

2. **Test in dev environment:**
   - Access dev URL
   - Test new features
   - Verify nothing breaks
   - Check logs in Azure Portal

3. **Merge to main when ready:**
   ```bash
   git checkout main
   git merge develop
   git push origin main
   # → Deploys to production app
   ```

### Emergency Rollback

If production deployment breaks:

```bash
# Revert the commit
git revert HEAD
git push origin main
# → Deploys previous version to production
```

---

## Environment Differences

Both apps use **SAME DNS backend** (same subscription & resource group):

| Setting | Production | Development |
|---------|------------|-------------|
| Container App | `bnlwe-fs01-n-00000-dns-ca` | `bnlwe-fs01-n-00000-dns-ca-dev` |
| Environment Var | `ENVIRONMENT=production` | `ENVIRONMENT=development` |
| App Version | `2.0.0` | `2.0.0-dev` |
| DNS Subscription | `f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be` | ✅ **SAME** |
| DNS Resource Group | `bnlwe-cc01-d-00000-mic-rg` | ✅ **SAME** |
| ACR | `bnlwecloudbauacr01.azurecr.io` | ✅ **SAME** |
| Container App Env | `bnlwe-fs01-n-00000-dns-cae` | ✅ **SAME** |

⚠️ **WARNING**: Both apps modify the **SAME DNS zones**. Be careful when testing in dev!

**Best practices:**
- Use test records with obvious names (e.g., `test-delete-me`, `dev-experiment`)
- Avoid modifying critical production records in dev
- Always verify changes before applying

---

## Monitoring

### View Deployment Status

- **GitHub Actions**: [Actions tab](../../actions)
- **Azure Portal**: Container Apps → `bnlwe-fs01-n-00000-dns-ca` or `-dev`

### Check App Health

```bash
# Production
curl https://[PROD_URL]/api/health

# Development
curl https://[DEV_URL]/api/health
```

### View Logs

**Azure Portal:**
1. Navigate to Container App
2. **Monitoring** → **Log stream**
3. Or use **Application Insights** if configured

**Azure CLI:**
```bash
# Production logs
az containerapp logs show \
  --name bnlwe-fs01-n-00000-dns-ca \
  --resource-group bnlwe-fs01-n-00000-cloudbau-rg \
  --follow

# Development logs
az containerapp logs show \
  --name bnlwe-fs01-n-00000-dns-ca-dev \
  --resource-group bnlwe-fs01-n-00000-cloudbau-rg \
  --follow
```

---

## Troubleshooting

### Dev Container App Not Found

**Problem:** `az containerapp update` fails with "ResourceNotFound"

**Solution:** Run Terraform apply first:
```bash
cd terraform
terraform apply
```

### Dev App Can't Access DNS

**Problem:** Dev app shows "Access Denied" when managing DNS

**Solution:** Assign DNS Zone Contributor role to dev app's managed identity (see Step 3)

### Both Apps Deploy to Same Container

**Problem:** Pushing to develop deploys to production instead

**Solution:** Check workflow logic in [deploy.yml](.github/workflows/deploy.yml):
```yaml
if [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
  echo "CONTAINER_APP_NAME=bnlwe-fs01-n-00000-dns-ca-dev" >> $GITHUB_ENV
```

### Wrong Branch Selected

**Problem:** Accidentally pushed to wrong branch

**Solution:** 
```bash
# Delete remote branch
git push origin --delete wrong-branch

# Or revert commit on correct branch
git checkout correct-branch
git revert HEAD
git push origin correct-branch
```

---

## Future Improvements

When moving to actual production:

1. **Separate DNS environments:**
   - Production: Real DNS zones
   - Development: Test DNS zones in separate subscription/RG

2. **Environment-specific config:**
   - Different cache TTLs
   - Different logging levels
   - Feature flags

3. **Blue-Green deployment:**
   - Use Container Apps revision mode
   - Traffic splitting for gradual rollouts

4. **Automated testing:**
   - Integration tests before deployment
   - Health checks as deployment gates
