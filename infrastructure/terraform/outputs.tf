output "service_url" {
  description = "Public URL of the Cloud Run service"
  value       = var.enable_service ? google_cloud_run_v2_service.app[0].uri : null
}

output "artifact_registry_url" {
  description = "Artifact Registry Docker repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}

output "discord_bot_ip" {
  description = "External IP of the Discord bot GCE instance"
  value       = var.enable_discord_bot ? google_compute_instance.discord_bot[0].network_interface[0].access_config[0].nat_ip : null
}
