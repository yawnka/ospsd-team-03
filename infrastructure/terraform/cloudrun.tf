# ---------- Artifact Registry ----------

resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "issue-tracker"
  format        = "DOCKER"
  description   = "Docker images for issue-tracker-service"
}

# ---------- Secret Manager secrets ----------
# Terraform manages only the secret *containers* — never the secret values.
# Values are populated out-of-band (gcloud / CI) so they never enter state:
#   gcloud secrets versions add trello-api-key   --data-file=-
#   gcloud secrets versions add trello-api-token  --data-file=-
#   gcloud secrets versions add otel-otlp-headers --data-file=-

resource "google_secret_manager_secret" "trello_api_key" {
  secret_id = "trello-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "trello_api_token" {
  secret_id = "trello-api-token"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "otel_otlp_headers" {
  secret_id = "otel-otlp-headers"
  replication {
    auto {}
  }
}

# ---------- Service account ----------
# Cloud Run needs its SA to access Secret Manager.

resource "google_service_account" "cloud_run" {
  account_id   = "issue-tracker-run"
  display_name = "Issue Tracker Cloud Run SA"
}

resource "google_secret_manager_secret_iam_member" "trello_api_key" {
  secret_id = google_secret_manager_secret.trello_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "trello_api_token" {
  secret_id = google_secret_manager_secret.trello_api_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "otel_otlp_headers" {
  secret_id = google_secret_manager_secret.otel_otlp_headers.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ---------- Cloud Run service ----------
# Gated by var.enable_service so that on first bootstrap:
#   1. apply with enable_service=false → creates secrets, SA, IAM
#   2. populate secret versions via gcloud
#   3. apply with enable_service=true  → creates Cloud Run (secrets ready)

resource "google_cloud_run_v2_service" "app" {
  count    = var.enable_service ? 1 : 0
  name     = "issue-tracker-service"
  location = var.region

  template {
    service_account = google_service_account.cloud_run.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}/service:${var.image_tag}"

      ports {
        container_port = 8000
      }

      # Sensitive values — injected from Secret Manager (never plain text in state)
      env {
        name = "TRELLO_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.trello_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "TRELLO_API_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.trello_api_token.secret_id
            version = "latest"
          }
        }
      }

      # Non-sensitive plain env vars
      env {
        name  = "REDIRECT_URI"
        value = var.redirect_uri
      }
      dynamic "env" {
        for_each = var.allowed_origin != "" ? [var.allowed_origin] : []
        content {
          name  = "ALLOWED_ORIGIN"
          value = env.value
        }
      }
      env {
        name  = "ENV"
        value = "production"
      }

      # Telemetry env vars — endpoint is plain (no secret), headers via Secret Manager
      dynamic "env" {
        for_each = var.otel_exporter_otlp_endpoint != "" ? [var.otel_exporter_otlp_endpoint] : []
        content {
          name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
          value = env.value
        }
      }
      dynamic "env" {
        for_each = var.otel_exporter_otlp_endpoint != "" ? [var.otel_service_name] : []
        content {
          name  = "OTEL_SERVICE_NAME"
          value = env.value
        }
      }
      # OTEL_EXPORTER_OTLP_HEADERS injected from Secret Manager when endpoint is set
      dynamic "env" {
        for_each = var.otel_exporter_otlp_endpoint != "" ? [google_secret_manager_secret.otel_otlp_headers.secret_id] : []
        content {
          name = "OTEL_EXPORTER_OTLP_HEADERS"
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }
  }

  depends_on = [
    google_artifact_registry_repository.docker,
    google_secret_manager_secret_iam_member.trello_api_key,
    google_secret_manager_secret_iam_member.trello_api_token,
    google_secret_manager_secret_iam_member.otel_otlp_headers,
  ]
}

# ---------- Public access (allUsers invoker) ----------

resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.enable_service ? 1 : 0
  name     = google_cloud_run_v2_service.app[0].name
  location = google_cloud_run_v2_service.app[0].location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
