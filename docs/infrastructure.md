# Terraform & Cloud Run

All cloud resources are defined in `infrastructure/terraform/` and managed exclusively through Terraform. No manual `gcloud` commands are used for resource provisioning.

Added in **HW3 (Second Submission)**.

## Resources Managed

| Resource | Terraform Type | Purpose |
|----------|---------------|---------|
| Artifact Registry | `google_artifact_registry_repository` | Docker image storage |
| Secret Manager secrets | `google_secret_manager_secret` ×4 | Trello key/token, OTLP headers, OpenAI key |
| Service account | `google_service_account` | Cloud Run runtime identity |
| Secret IAM bindings | `google_secret_manager_secret_iam_member` | Least-privilege secret access |
| Cloud Run service | `google_cloud_run_v2_service` | Application container |
| Public IAM | `google_cloud_run_v2_service_iam_member` | Allow unauthenticated invocations |

## State Management

Terraform state is stored in a GCS bucket (`ospsd-team-03-tfstate`), enabling shared state across local development and CI without committing sensitive state files.

## Bootstrap Process

The `enable_service` variable (default `false`) supports a two-phase bootstrap to avoid a chicken-and-egg problem where Cloud Run needs secrets that don't yet exist:

**Phase 1** — create secrets and IAM first:
```bash
terraform apply -var="enable_service=false"
```

**Phase 2** — populate secret versions:
```bash
gcloud secrets versions add trello-api-key --data-file=-  <<< "$TRELLO_API_KEY"
gcloud secrets versions add trello-api-token --data-file=-  <<< "$TRELLO_API_TOKEN"
gcloud secrets versions add otel-otlp-headers --data-file=-  <<< "$OTEL_HEADERS"
gcloud secrets versions add openai-api-key --data-file=-  <<< "$OPENAI_API_KEY"
```

**Phase 3** — deploy the service:
```bash
terraform apply -var="enable_service=true" -var="image_tag=$IMAGE_TAG"
```

CI always runs phase 3 only because secrets are already populated.

## Environment Variables (Cloud Run)

Sensitive values are injected via `secret_key_ref` — they never appear in Terraform state as plaintext.

| Variable | Source |
|----------|--------|
| `TRELLO_API_KEY` | Secret Manager |
| `TRELLO_API_TOKEN` | Secret Manager |
| `OTEL_EXPORTER_OTLP_HEADERS` | Secret Manager |
| `OPENAI_API_KEY` | Secret Manager |
| `REDIRECT_URI` | Terraform variable |
| `ENV` | Hardcoded `production` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Terraform variable |
| `OTEL_SERVICE_NAME` | Terraform variable |

## Cloud Run Configuration

- **Scaling**: 0–1 instances (scales to zero between requests)
- **CPU / Memory**: 1 vCPU, 512 MiB
- **Health probe**: `GET /health` — 5s initial delay, 10s period
- **Access**: Public (`allUsers` invoker)

## Local Terraform Commands

```bash
cd infrastructure/terraform

# Preview changes
terraform plan -var="image_tag=latest"

# Apply
terraform apply -var="image_tag=latest" -var="enable_service=true"

# Destroy (careful — deletes all resources)
terraform destroy
```
