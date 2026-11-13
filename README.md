# Idea Board Platform

A small idea-sharing app, deployed through a cloud-agnostic, AI-enhanced
CI/CD pipeline. One app, one Helm chart, one Terraform module contract
across AWS, GCP, and local (kind) — and six real Gemini-powered checks
built into the pipeline itself.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full system design, and
this [architecture diagram](https://claude.ai/artifact/7Am93e6oVs9REdTuma8qYL)
for how each AI feature calls Gemini and falls back when it can't.

## The app

- **Backend**: FastAPI + PostgreSQL (SQLAlchemy). `GET/POST /ideas`,
  `POST /ideas/{id}/upvote`, `GET /healthz`.
- **Frontend**: React + Vite. List ideas, add one, upvote.
- **Database**: Postgres — CloudNativePG locally, RDS on AWS, Cloud SQL
  on GCP, all through the same Terraform interface.

## Quick start — Docker Compose

The fastest way to run the whole stack:

```sh
docker compose up --build
```

- Frontend: http://localhost:5173/
- Backend: http://localhost:8000/healthz

```sh
curl http://localhost:8000/ideas
curl -X POST http://localhost:8000/ideas -H "Content-Type: application/json" -d '{"text":"my first idea"}'
```

Stop it with `docker compose down`.

## Running on Kubernetes (local)

For something closer to the real cloud deploys — same Helm chart, same
canary rollout, same AI evaluator — bring up a local `kind` cluster
through Terraform instead:

```sh
make apply-local                                    # creates the kind cluster + platform layer
export KUBECONFIG=infra/live/local/.kubeconfig-cloud-a

docker build -t idea-board-backend:local app/backend
docker build -t idea-board-frontend:local app/frontend
kind load docker-image idea-board-backend:local --name cloud-a
kind load docker-image idea-board-frontend:local --name cloud-a

helm install idea-board deploy/helm/idea-board \
  --namespace ideaboard --create-namespace \
  -f deploy/helm/idea-board/values-local.yaml

kubectl -n ideaboard port-forward svc/idea-board-frontend 8080:80 &
kubectl -n ideaboard port-forward svc/idea-board-backend 8000:8000 &
```

Visit `http://localhost:8080/`. Tear down with `make destroy-local`.

## Deploying to the cloud

Terraform provisions the same four pieces — network, Kubernetes cluster,
database, and platform layer — identically on AWS and GCP, differing
only in which real resources back them (EKS/RDS vs. GKE/Cloud SQL). See
`infra/modules/*/{aws,gcp,local}` and the contract table in
`ARCHITECTURE.md`.

To actually deploy: open this repo's **Actions** tab → **deploy** →
**Run workflow**, choose `aws` or `gcp`. It authenticates via OIDC (no
stored cloud keys), builds and pushes images, runs `terraform apply`,
installs the app with Helm, and prints the public URL in the run's
summary.

## The AI features

Six features call Gemini through one shared client
(`ai/llm/client.py`) — schema-validated responses, a fixed call budget,
and a `GeminiUnavailable` escape hatch every feature falls back from
differently:

| Feature | Where it runs | What Gemini decides | On fallback |
|---|---|---|---|
| **Test selection** | CI, every PR | which extra tests to run beyond a guaranteed direct-match floor | runs every test |
| **Blast-radius gatekeeper** | CI, every PR | writes the summary/remediation plan only — the pass/fail gate is pure Python | shows the raw findings instead of prose |
| **Review memory** | CI, every PR | judges each diff hunk on its own merits, grounding in past review comments only when it genuinely fits | cites a past comment only above a strict confidence bar, else stays silent |
| **Self-heal** | CI, on test/lint failure | proposes a full-file fix for a failing command | none — reports "needs a human," the one feature with no safe guess |
| **RCA** | on demand, against live traces | writes a root-cause hypothesis, citing only real trace IDs it was given | surfaces the raw evidence at low confidence |
| **Adaptive canary routing** | live, during a rollout | advance / hold / rollback, only once a hard guard (error rate, latency) is already clean | always advances — never blocks |

Every feature has been run against real Gemini calls, not just its
fallback path — including live fault injection (a real crash in a
canary pod) and a real GitHub PR where review-memory caught a
deliberately planted SQL injection.

Two features from the original plan — profiling and drift detection —
were never built; NetworkPolicy generation was dropped from scope.

## Cloud-agnostic design

Every backend (`aws`, `gcp`, `local`) implements the exact same
`variables.tf`/`outputs.tf` shape for the `network`, `cluster`, and
`database` modules. Nothing above that line — the Helm chart, the
pipeline — ever branches on which cloud it's running on; cloud
differences only ever show up as module outputs (ingress annotations,
storage class). `infra/contract_check.py` enforces this on every PR that
touches `infra/`, and it's been proven to actually catch drift, not just
pass by default.

## Repository layout

```
app/              FastAPI backend, React frontend
deploy/helm/      One Helm chart, used locally and in every cloud
infra/            Terraform: modules/ (aws/gcp/local), live/ (thin roots), platform/
ai/               The six AI features + the shared Gemini client
.github/workflows/  ci.yml (every PR), deploy.yml (manual cloud deploy), iac-contract.yml
```
