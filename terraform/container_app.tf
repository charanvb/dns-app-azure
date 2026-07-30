resource "azurerm_container_app_environment" "main" {
  name                = var.container_app_env_name
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
}

resource "azurerm_container_app" "main" {
  name                         = var.container_app_name
  resource_group_name          = data.azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  # Use the system-assigned MI to pull images from ACR (no admin credentials).
  registry {
    server   = azurerm_container_registry.main.login_server
    identity = "system"
  }

  template {
    container {
      name   = "dns-portal"
      image  = var.initial_image
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  lifecycle {
    # GitHub Actions owns the image tag; prevent Terraform from reverting it.
    ignore_changes = [
      template[0].container[0].image,
      secret,
    ]
  }
}

# Grant the Container App's managed identity permission to pull images from ACR.
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.main.identity[0].principal_id
}
