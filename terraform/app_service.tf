# ══════════════════════════════════════════════════════════════════════════════
# Azure App Service for DNS Portal
# 
# This is a new deployment path alongside the existing Container App.
# App Service provides easier VNet integration for PostgreSQL connectivity.
# ══════════════════════════════════════════════════════════════════════════════

# ── App Service Plan ──────────────────────────────────────────────────────────

resource "azurerm_service_plan" "main" {
  name                = "bnlwe-fs01-n-00000-dns-plan"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"  # Basic B1: 1 vCPU, 1.75GB RAM, ~$13/month, includes VNet integration

  # Disable zone redundancy (not needed for dev/test)
  zone_balancing_enabled = false

  lifecycle {
    ignore_changes = [tags]
  }
}

# ── Linux Web App (Docker Container) ──────────────────────────────────────────

resource "azurerm_linux_web_app" "main" {
  name                = "bnlwe-fs01-n-00000-dns-webapp"
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  # System-assigned managed identity (for Blob Storage, DNS access)
  identity {
    type = "SystemAssigned"
  }

  # Application settings (environment variables)
  app_settings = {
    "ENVIRONMENT"                         = "production"
    "DNS_SUBSCRIPTION_ID"                 = var.dns_subscription_id
    "DNS_RESOURCE_GROUP"                  = var.dns_resource_group
    "APP_NAME"                            = "Azure DNS Portal"
    "APP_VERSION"                         = "2.0.0"
    "SCM_DO_BUILD_DURING_DEPLOYMENT"      = "true"  # Build during deployment
    "ENABLE_ORYX_BUILD"                   = "true"  # Enable Oryx build system
  }

  # Python direct deployment configuration (NO Docker!)
  site_config {
    always_on              = true  # Keep app always running (required for B1 tier)
    http2_enabled          = true
    ftps_state             = "Disabled"  # Security: disable FTP
    minimum_tls_version    = "1.2"       # Security: TLS 1.2+
    
    # Python application stack
    application_stack {
      python_version = "3.12"  # Match your Dockerfile version
    }

    # Startup command - Gunicorn with Uvicorn worker for FastAPI
    app_command_line = "gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind=0.0.0.0:8000"

    # Health check configuration
    health_check_path                 = "/api/health"
    health_check_eviction_time_in_min = 10  # Time before unhealthy instance is removed
  }

  # HTTPS only (security best practice)
  https_only = true

  # Logs configuration
  logs {
    application_logs {
      file_system_level = "Information"
    }
    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 35
      }
    }
  }

  lifecycle {
    # Ignore tags managed by organization policy
    ignore_changes = [tags]
  }
}

# ══════════════════════════════════════════════════════════════════════════════
# Notes:
# 
# 1. VNet Integration:
#    After Terraform apply, manually enable VNet integration in Azure Portal:
#    - App Service → Networking → VNet Integration → Add VNet
#    - Or add via Terraform with azurerm_app_service_virtual_network_swift_connection
#
# 2. Scaling:
#    B1 tier: Manual scale (1-3 instances)
#    Upgrade to S1+ for autoscaling
#
# 3. Deployment:
#    Deploy Python code via: az webapp up --runtime "PYTHON:3.12"
#    Or connect to GitHub for automatic deployments
# ══════════════════════════════════════════════════════════════════════════════
