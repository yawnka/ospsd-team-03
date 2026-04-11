# ---------- GCP project ----------

variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "ospsd-team-03"
}

variable "region" {
  description = "GCP region for Cloud Run and Artifact Registry"
  type        = string
  default     = "us-central1"
}

# ---------- Container image ----------

variable "image_tag" {
  description = "Docker image tag to deploy (e.g. latest, git SHA)"
  type        = string
}

# ---------- Application env vars (required) ----------

variable "trello_api_key" {
  description = "Trello API key"
  type        = string
  sensitive   = true
}

variable "trello_api_token" {
  description = "Trello API token (fallback for unauthenticated requests)"
  type        = string
  sensitive   = true
}

variable "redirect_uri" {
  description = "OAuth callback URL (Cloud Run URL + /auth/callback)"
  type        = string
}

# ---------- Application env vars (optional) ----------

variable "allowed_origin" {
  description = "CORS origin. Empty string means allow all without credentials."
  type        = string
  default     = ""
}

# ---------- Telemetry (Phase 2 / Phase 4) ----------

variable "otel_exporter_otlp_endpoint" {
  description = "Grafana Cloud OTLP endpoint. Empty = telemetry disabled."
  type        = string
  default     = ""
}

variable "otel_exporter_otlp_headers" {
  description = "Grafana Cloud OTLP auth header. Empty = telemetry disabled."
  type        = string
  default     = ""
  sensitive   = true
}

variable "otel_service_name" {
  description = "OpenTelemetry service name."
  type        = string
  default     = "issue-tracker-service"
}
