output "acr_login_server" {
  description = "ACR login server — use as image prefix in deploy.yml."
  value       = azurerm_container_registry.main.login_server
}

output "container_app_fqdn" {
  description = "Public HTTPS URL of the Container App."
  value       = "https://${azurerm_container_app.main.ingress[0].fqdn}"
}

output "container_app_name" {
  description = "Container App resource name — matches CONTAINER_APP_NAME in deploy.yml."
  value       = azurerm_container_app.main.name
}


