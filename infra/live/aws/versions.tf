terraform {
  required_version = ">= 1.7.0"

  # Partial config: supply bucket/key/region via `terraform init
  # -backend-config=...` or a backend.hcl file, never commit real values
  # here — this repo has never been applied against real AWS infra.
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
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
