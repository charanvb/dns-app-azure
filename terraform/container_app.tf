resource "azurerm_container_app_environment" "main" {
  name                = var.container_app_env_name
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location

  lifecycle {
    ignore_changes = [tags]
  }
}

resource "azurerm_container_app" "main" {
  name                         = var.container_app_name
  resource_group_name          = data.azurerm_resource_group.main.name
  container_app_environment_id = azurerm_container_app_environment.main.id
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
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

      env {
        name  = "DNS_SUBSCRIPTION_ID"
        value = var.dns_subscription_id
      }

      env {
        name  = "DNS_RESOURCE_GROUP"
        value = var.dns_resource_group
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
    # CI owns the image; org policy owns tags; deploy.yml owns registry config.
    ignore_changes = [
      template[0].container[0].image,
      secret,
      tags,
      registry,
    ]
  }
}

# Grant the Container App's managed identity permission to pull images from ACR.
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_container_app.main.identity[0].principal_id
}
