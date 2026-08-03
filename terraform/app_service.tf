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

  # System-assigned managed identity (for ACR, Blob Storage, DNS access)
  identity {
    type = "SystemAssigned"
  }

  # Application settings (environment variables)
  app_settings = {
    "WEBSITES_PORT"                       = "8000"  # FastAPI runs on port 8000
    "DOCKER_ENABLE_CI"                    = "true"
    "ENVIRONMENT"                         = "production"
    "DNS_SUBSCRIPTION_ID"                 = var.dns_subscription_id
    "DNS_RESOURCE_GROUP"                  = var.dns_resource_group
    "APP_NAME"                            = "Azure DNS Portal"
    "APP_VERSION"                         = "2.0.0"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
  }
  
  # Docker registry authentication using managed identity (configured separately)
  # Azure App Service automatically uses the managed identity to authenticate to ACR

  # Docker configuration
  site_config {
    always_on              = true  # Keep app always running (required for B1 tier)
    http2_enabled          = true
    ftps_state             = "Disabled"  # Security: disable FTP
    minimum_tls_version    = "1.2"       # Security: TLS 1.2+
    
    # Container settings
    # When using managed identity for ACR authentication, only specify docker_image_name
    # The registry URL is automatically handled via the role assignment
    application_stack {
      docker_image_name   = "${azurerm_container_registry.main.login_server}/dns-portal:latest"
    }

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
    # GitHub Actions will update the docker image
    ignore_changes = [
      site_config[0].application_stack[0].docker_image_name,
      tags,
    ]
  }
}

# ── ACR Pull Permission ───────────────────────────────────────────────────────

# Grant App Service managed identity permission to pull images from ACR
resource "azurerm_role_assignment" "webapp_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.main.identity[0].principal_id
}

# ── Deployment Slot (Optional - Commented Out) ────────────────────────────────

# Deployment slots require Standard (S1) tier or higher
# Uncomment when ready to use blue-green deployments
#
# resource "azurerm_linux_web_app_slot" "staging" {
#   name           = "staging"
#   app_service_id = azurerm_linux_web_app.main.id
#
#   site_config {
#     always_on = true
#     application_stack {
#       docker_image_name   = "${azurerm_container_registry.main.login_server}/dns-portal:latest"
#       docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
#     }
#   }
# }

# ══════════════════════════════════════════════════════════════════════════════
# Notes:
# 
# 1. VNet Integration:
#    After Terraform apply, manually enable VNet integration in Azure Portal:
#    - App Service → Networking → VNet Integration → Add VNet
#    - Or add via Terraform with azurerm_app_service_virtual_network_swift_connection
#
# 2. ACR Authentication:
#    App Service uses managed identity to pull images from ACR (no password needed)
#
# 3. Scaling:
#    B1 tier: Manual scale (1-3 instances)
#    Upgrade to S1+ for autoscaling
#
# 4. Deployment:
#    GitHub Actions will update docker_image_name via:
#    az webapp config container set --docker-custom-image-name ...
# ══════════════════════════════════════════════════════════════════════════════
