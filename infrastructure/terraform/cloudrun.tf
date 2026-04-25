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
#   gcloud secrets versions add trello-api-key    --data-file=-
#   gcloud secrets versions add trello-api-token   --data-file=-
#   gcloud secrets versions add otel-otlp-headers  --data-file=-
#   gcloud secrets versions add discord-bot-token  --data-file=-

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

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "discord_bot_token" {
  secret_id = "discord-bot-token"
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

resource "google_secret_manager_secret_iam_member" "openai_api_key" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "discord_bot_token" {
  secret_id = google_secret_manager_secret.discord_bot_token.id
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

      # OpenAI API key — injected from Secret Manager
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }

      # Discord bot token — injected from Secret Manager when Discord is configured
      dynamic "env" {
        for_each = var.discord_guild_id != "" ? [google_secret_manager_secret.discord_bot_token.secret_id] : []
        content {
          name = "DISCORD_BOT_TOKEN"
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
      dynamic "env" {
        for_each = var.discord_guild_id != "" ? [var.discord_guild_id] : []
        content {
          name  = "DISCORD_GUILD_ID"
          value = env.value
        }
      }
      dynamic "env" {
        for_each = var.discord_notify_channel_id != "" ? [var.discord_notify_channel_id] : []
        content {
          name  = "DISCORD_NOTIFY_CHANNEL_ID"
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

  depends_on = [
    google_artifact_registry_repository.docker,
    google_secret_manager_secret_iam_member.trello_api_key,
    google_secret_manager_secret_iam_member.trello_api_token,
    google_secret_manager_secret_iam_member.otel_otlp_headers,
    google_secret_manager_secret_iam_member.openai_api_key,
    google_secret_manager_secret_iam_member.discord_bot_token,
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

# ---------- Discord bot (GCE) ----------

resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_service_account" "discord_bot" {
  account_id   = "discord-bot"
  display_name = "Discord Bot GCE SA"
}

# Bot SA → Secret Manager access (4 secrets)

resource "google_secret_manager_secret_iam_member" "bot_discord_bot_token" {
  secret_id = google_secret_manager_secret.discord_bot_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "bot_trello_api_key" {
  secret_id = google_secret_manager_secret.trello_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "bot_trello_api_token" {
  secret_id = google_secret_manager_secret.trello_api_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

resource "google_secret_manager_secret_iam_member" "bot_openai_api_key" {
  secret_id = google_secret_manager_secret.openai_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.discord_bot.email}"
}

# Bot SA → Artifact Registry reader (to pull bot Docker image)

resource "google_artifact_registry_repository_iam_member" "bot_reader" {
  location   = google_artifact_registry_repository.docker.location
  repository = google_artifact_registry_repository.docker.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.discord_bot.email}"
}

# GCE instance — Container-Optimized OS, fetches secrets via metadata server + curl

resource "google_compute_instance" "discord_bot" {
  count        = var.enable_discord_bot ? 1 : 0
  name         = "discord-bot"
  machine_type = "e2-micro"
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "projects/cos-cloud/global/images/family/cos-stable"
    }
  }

  network_interface {
    network = "default"
    access_config {} # External IP for Discord gateway + Artifact Registry
  }

  service_account {
    email  = google_service_account.discord_bot.email
    scopes = ["cloud-platform"]
  }

  metadata_startup_script = <<-SCRIPT
    #!/bin/bash
    set -euo pipefail

    PROJECT="${var.project_id}"
    REGION="${var.region}"
    IMAGE="$${REGION}-docker.pkg.dev/$${PROJECT}/${google_artifact_registry_repository.docker.repository_id}/discord-bot:${var.bot_image_tag}"

    # --- Authenticate Docker to Artifact Registry via metadata server ---
    ACCESS_TOKEN=$(curl -sf -H "Metadata-Flavor: Google" \
      "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \
      | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')

    echo "$${ACCESS_TOKEN}" | docker login -u oauth2accesstoken --password-stdin "https://$${REGION}-docker.pkg.dev"

    # --- Fetch secrets from Secret Manager REST API ---
    fetch_secret() {
      curl -sf \
        -H "Authorization: Bearer $${ACCESS_TOKEN}" \
        "https://secretmanager.googleapis.com/v1/projects/$${PROJECT}/secrets/$1/versions/latest:access" \
        | sed -n 's/.*"data":"\([^"]*\)".*/\1/p' \
        | base64 -d
    }

    DISCORD_BOT_TOKEN=$(fetch_secret discord-bot-token)
    TRELLO_API_KEY=$(fetch_secret trello-api-key)
    TRELLO_API_TOKEN=$(fetch_secret trello-api-token)
    OPENAI_API_KEY=$(fetch_secret openai-api-key)

    # --- Run bot container (idempotent: safe on reboot) ---
    docker rm -f discord-bot 2>/dev/null || true
    docker pull "$${IMAGE}"
    docker run -d --restart=always --name=discord-bot \
      -e DISCORD_BOT_TOKEN="$${DISCORD_BOT_TOKEN}" \
      -e DISCORD_GUILD_ID="${var.discord_guild_id}" \
      -e TRELLO_API_KEY="$${TRELLO_API_KEY}" \
      -e TRELLO_API_TOKEN="$${TRELLO_API_TOKEN}" \
      -e OPENAI_API_KEY="$${OPENAI_API_KEY}" \
      "$${IMAGE}"
  SCRIPT

  depends_on = [
    google_project_service.compute,
    google_secret_manager_secret_iam_member.bot_discord_bot_token,
    google_secret_manager_secret_iam_member.bot_trello_api_key,
    google_secret_manager_secret_iam_member.bot_trello_api_token,
    google_secret_manager_secret_iam_member.bot_openai_api_key,
    google_artifact_registry_repository_iam_member.bot_reader,
  ]
}
