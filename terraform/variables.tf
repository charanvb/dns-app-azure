variable "subscription_id" {
  description = "Azure subscription ID for Foundation Services-01."
  type        = string
}

variable "resource_group_name" {
  description = "Existing resource group where all resources are created."
  type        = string
  default     = "bnlwe-fs01-n-00000-cloudbau-rg"
}

variable "dns_subscription_id" {
  description = "Subscription ID containing the DNS zones."
  type        = string
  default     = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"
}

variable "dns_resource_group" {
  description = "Resource group containing the DNS zones."
  type        = string
  default     = "bnlwe-cc01-d-00000-mic-rg"
}

variable "environment" {
  description = "App environment label. Controls the login page badge and whether startup.sh seeds local test users (skipped when set to 'production'). Flip to 'production' once SSO (Phase 5) goes live."
  type        = string
  default     = "development"
}

variable "database_url" {
  description = "SQLAlchemy connection string for the isolated dns_selfservice Postgres database. Supplied via CI secret (TF_VAR_database_url) — never committed."
  type        = string
  sensitive   = true
}

variable "session_secret_key" {
  description = "Random secret signing the local-auth session cookie. Supplied via CI secret (TF_VAR_session_secret_key) — never committed."
  type        = string
  sensitive   = true
}

variable "logic_app_email_url" {
  description = "Logic App HTTP trigger URL used to send email notifications. Supplied via CI secret (TF_VAR_logic_app_email_url) — never committed."
  type        = string
  sensitive   = true
}
