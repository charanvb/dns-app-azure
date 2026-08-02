output "acr_login_server" {
  description = "ACR login server — use as image prefix in deploy.yml."
  value       = azurerm_container_registry.main.login_server
}

output "container_app_fqdn" {
  description = "Public HTTPS URL of the Production Container App."
  value       = "https://${azurerm_container_app.main.ingress[0].fqdn}"
}

output "container_app_name" {
  description = "Production Container App resource name."
  value       = azurerm_container_app.main.name
}

output "container_app_dev_fqdn" {
  description = "Public HTTPS URL of the Development Container App."
  value       = "https://${azurerm_container_app.dev.ingress[0].fqdn}"
}

output "container_app_dev_name" {
  description = "Development Container App resource name."
  value       = azurerm_container_app.dev.name
}

output "container_app_dev_principal_id" {
  description = "Development Container App Managed Identity Principal ID (for DNS role assignment)."
  value       = azurerm_container_app.dev.identity[0].principal_id
}


