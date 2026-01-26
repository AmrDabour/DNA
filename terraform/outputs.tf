# ============================================================
# GenovaAI - Terraform Outputs
# ============================================================

output "cluster_location" {
  description = "GKE cluster location"
  value       = google_container_cluster.genovaai_cluster.location
}

output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.genovaai_cluster.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.genovaai_cluster.endpoint
  sensitive   = true
}

output "get_credentials_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.genovaai_cluster.name} --region=${var.region} --project=${var.gcp_project_id}"
}
