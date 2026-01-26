# ============================================================
# GenovaAI - Terraform Variables
# ============================================================

variable "gcp_project_id" {
  type        = string
  description = "The GCP project ID"
}

variable "name" {
  type        = string
  description = "Name of the GKE cluster"
  default     = "genovaai-cluster"
}

variable "region" {
  type        = string
  description = "Region of the GKE cluster"
  default     = "us-central1"
}

variable "namespace" {
  type        = string
  description = "Kubernetes namespace"
  default     = "genovaai"
}

variable "filepath_manifest" {
  type        = string
  description = "Path to Kubernetes manifests"
  default     = "../kubernetes-manifests"
}

variable "app_image" {
  type        = string
  description = "Docker image for GenovaAI app"
  default     = "amrdabour/genovaai:latest"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
  default     = "prod"
}
