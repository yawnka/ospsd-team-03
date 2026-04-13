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

# ---------- Bootstrap control ----------

variable "enable_service" {
  description = "Set to false on first apply so secrets/IAM are created before Cloud Run. Flip to true after populating secret versions."
  type        = bool
  default     = true
}

# ---------- Container image ----------

variable "image_tag" {
  description = "Docker image tag to deploy (e.g. latest, git SHA)"
  type        = string
}

# ---------- Application env vars (required) ----------
# NOTE: Trello API key/token are managed in Secret Manager, not as Terraform
# variables, so their values never enter Terraform state. Populate them via:
#   echo -n "$VALUE" | gcloud secrets versions add SECRET_ID --data-file=-

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

# otel_exporter_otlp_headers is managed in Secret Manager (secret ID: otel-otlp-headers).
# Populate via: echo -n "$HEADERS" | gcloud secrets versions add otel-otlp-headers --data-file=-

variable "otel_service_name" {
  description = "OpenTelemetry service name."
  type        = string
  default     = "issue-tracker-service"
}
