provider "google" {
  project = var.project
  region  = var.region
}

# Both providers' configs reference module.cluster's own outputs directly
# — same pattern as live/aws, standard for GKE/EKS alike.
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
