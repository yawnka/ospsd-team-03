# ---------- Artifact Registry ----------

resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  repository_id = "issue-tracker"
  format        = "DOCKER"
  description   = "Docker images for issue-tracker-service"
}

# ---------- Cloud Run service ----------

resource "google_cloud_run_v2_service" "app" {
  name     = "issue-tracker-service"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}/service:${var.image_tag}"

      ports {
        container_port = 8000
      }

      # Required env vars — app crashes without these
      env {
        name  = "TRELLO_API_KEY"
        value = var.trello_api_key
      }
      env {
        name  = "TRELLO_API_TOKEN"
        value = var.trello_api_token
      }
      env {
        name  = "REDIRECT_URI"
        value = var.redirect_uri
      }

      # Optional env vars
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

      # Telemetry env vars (no-op when empty)
      dynamic "env" {
        for_each = var.otel_exporter_otlp_endpoint != "" ? [var.otel_exporter_otlp_endpoint] : []
        content {
          name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
          value = env.value
        }
      }
      dynamic "env" {
        for_each = var.otel_exporter_otlp_headers != "" ? [var.otel_exporter_otlp_headers] : []
        content {
          name  = "OTEL_EXPORTER_OTLP_HEADERS"
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

  depends_on = [google_artifact_registry_repository.docker]
}

# ---------- Public access (allUsers invoker) ----------

resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.app.name
  location = google_cloud_run_v2_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
