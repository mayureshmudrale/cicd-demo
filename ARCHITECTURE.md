# Architecture

## Overview

One app (Idea Board), one Helm chart, one pipeline, and one Terraform
module contract with three backends: **AWS**, **GCP**, and **local** (kind
on OrbStack). AWS and GCP are fully written (real EKS/RDS and GKE/Cloud
SQL resources, not stubs) and contract-tested via `terraform validate`
and `infra/contract_check.py`; they've never been `apply`'d against real
infra (no cloud credentials in this environment) and only would with
`CLOUD=aws|gcp` and real credentials. Day-to-day runs and all fault
simulations use `CLOUD=local`, the one backend actually applied and
exercised live throughout this project.

Five AI features run on Gemini (free-tier key) — RCA, profiling, adaptive
canary routing, drift detection, and test selection; NetworkPolicy
generation was dropped from scope. Core rule: **AI proposes,
deterministic code disposes.** Every AI feature is proven with scripted
fault simulations and a scorecard (see `sim/`).

```text
GitHub (PRs, Actions) ──jobs──▶ Self-hosted runner (Mac)
                                   │  CLOUD=local | aws | gcp
                                   ▼
               infra/live/<cloud>  (thin root, ~30 lines)
                                   │  same inputs / same outputs
           ┌───────────────────────┼────────────────────────┐
     modules/*/aws           modules/*/gcp             modules/*/local
   VPC · EKS · RDS     VPC · GKE · Cloud SQL     kind · Cilium · CloudNativePG
           └───────────────────────┼────────────────────────┘
                                   ▼
       Cloud-neutral platform (Helm): ingress-nginx, Argo Rollouts,
       otel-lgtm, toxiproxy, AI evaluator ──▶ Gemini API (redacted evidence)
                                   ▼
                    Idea Board: frontend → backend → Postgres
```

Everything above the module line knows nothing about the cloud. Cloud
differences are expressed only as **module outputs** (ingress
annotations, storage class, etc.), never as `if cloud == ...` branches in
the chart or pipeline.

## Terraform module contract

Every backend (`aws`, `gcp`, `local`) implements the same
`variables.tf` / `outputs.tf` signature for four modules:

| Module | Inputs | Outputs |
| --- | --- | --- |
| `network` | `name`, `region`, `cidr` | `network_id`, `private_subnet_ids` |
| `cluster` | `name`, `tier`, `network_id`, `private_subnet_ids` | `cluster_name`, `kube_host`, `kube_ca` (sensitive), `kube_token` (sensitive), `ingress_annotations`, `storage_class` |
| `database` | `name`, `tier`, `network_id`, `allowed_from` | `database_url` (sensitive), `host`, `port` |
| `tiers` | `cloud`, `tier` | `node_type`, `node_count`, `db_class`, `db_ha` |

`.github/workflows/iac-contract.yml` enforces this, with two jobs:
- `contract` runs `infra/contract_check.py` — a deterministic, no-AI
  script that parses every backend's `variables.tf`/`outputs.tf` and
  fails if any backend is missing one of the contract names above.
  Verified to actually catch drift, not just pass trivially: renaming an
  output in `cluster/gcp` to prove a false pass was impossible, confirming
  the failure, then reverting.
- `validate` runs `terraform init -backend=false && terraform validate`
  across all 13 module/root paths (every module × backend, plus
  `infra/live/{aws,gcp,local}` and `infra/platform`) — schema/syntax
  checking only, no cloud credentials needed or used.

Inputs a backend doesn't need (e.g. `region` for local) are accepted and
ignored; backend-specific extras beyond the contract table (e.g.
`cluster/aws`'s `kubernetes_version`) are expected and not flagged — only
the names in the table above are enforced identical across all three.

## Invariants

Feature #5 (semantic drift) checks that the prose above still matches
reality — e.g. that the chart has no cloud-conditional logic, and that
the fault-injection surface stays `backend/faults.py`-only. The YAML
block below is what it diffs against; keep it in sync as the chart and
pipeline get built out in later phases.

```yaml
invariants:
  no_cloud_conditionals_in_chart: true
  fault_injection_surface: ["app/backend/faults.py"]
  database_never_public: true
  ai_emits_tier_names_only: true
```
