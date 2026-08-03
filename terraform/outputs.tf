# ── App Service Outputs ───────────────────────────────────────────────────────

output "app_service_url" {
  description = "Public HTTPS URL of the App Service."
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "app_service_name" {
  description = "App Service resource name."
  value       = azurerm_linux_web_app.main.name
}

output "app_service_principal_id" {
  description = "App Service Managed Identity Principal ID (for DNS role assignment)."
  value       = azurerm_linux_web_app.main.identity[0].principal_id
}

output "app_service_plan_name" {
  description = "App Service Plan name."
  value       = azurerm_service_plan.main.name
}


