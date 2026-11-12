terraform {
  required_version = ">= 1.7.0"

  # Partial config: supply bucket/prefix via `terraform init
  # -backend-config=...` or a backend.hcl file, never commit real values
  # here — this repo has never been applied against real GCP infra.
  backend "gcs" {}

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.14"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
