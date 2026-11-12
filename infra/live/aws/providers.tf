provider "aws" {
  region = var.region
}

# Both providers' configs reference module.cluster's own outputs directly
# — the standard, documented Terraform pattern for EKS/GKE (no eager
# file-read at provider-config time the way the local/kind backend has to
# work around; Terraform just waits for the cluster to exist first).
provider "kubernetes" {
  host                   = module.cluster.kube_host
  cluster_ca_certificate = base64decode(module.cluster.kube_ca)
  token                  = module.cluster.kube_token
}

provider "helm" {
  kubernetes {
    host                   = module.cluster.kube_host
    cluster_ca_certificate = base64decode(module.cluster.kube_ca)
    token                  = module.cluster.kube_token
  }
}
