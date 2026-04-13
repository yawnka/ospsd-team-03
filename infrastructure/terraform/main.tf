terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Lock file (.terraform.lock.hcl) is committed to pin provider versions
  # for reproducible plans across CI and team members.

  # Local backend for now. Migrate to GCS in Phase 3 (CI integration).
  # backend "gcs" {
  #   bucket = "ospsd-team-03-tfstate"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
