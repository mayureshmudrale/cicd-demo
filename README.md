# Idea Board Platform

AI-enhanced, cloud-agnostic CI/CD platform. One app, one Helm chart, one
pipeline, one Terraform module contract with three backends (AWS, GCP,
local). See the full plan for architecture, phases, and rationale.

## Status: Phase 2 (app + delivery) mostly done

What's here so far:

- `infra/modules/{network,cluster,database,tiers}/local` — the local
  (kind-on-OrbStack) Terraform backend.
- `infra/live/local` — thin root that stands up two kind clusters,
  `cloud-a` (full stack) and `cloud-b` (app-only), each with Cilium and a
  CloudNativePG Postgres cluster. Verified working end to end — the one
  backend actually `apply`'d and exercised live throughout this project.
- `infra/modules/{network,cluster,database}/{aws,gcp}` — real EKS/RDS
  and GKE/Cloud SQL Terraform, matching the exact same
  `variables.tf`/`outputs.tf` contract as `local` (see `ARCHITECTURE.md`).
  Security defaults throughout, not just for the sake of the
  `database_never_public` invariant: EKS/GKE clusters are private-subnet-
  only (`enable_private_nodes`/no public node IPs), RDS/Cloud SQL get no
  public IP at all (`publicly_accessible = false` / `ipv4_enabled =
  false`), master passwords are generated via `random_password`, never
  literals. `infra/live/{aws,gcp}` are the matching thin roots (network →
  cluster → database → the same cloud-neutral `infra/platform` module
  `local` already uses, wired via each cloud's own short-lived auth token
  — `aws_eks_cluster_auth`/`google_client_config`, the standard
  Terraform pattern for both, not a stored credential). **Never
  `apply`'d against real infra** (no cloud credentials in this
  environment) — verified instead via `terraform validate` (schema/syntax
  only, needs provider plugins but no credentials) across all 13
  module/root paths, all passing.
- `infra/contract_check.py` + `.github/workflows/iac-contract.yml` —
  deterministic (no AI) proof that the three backends actually match the
  documented contract, not just by assertion. Verified it really catches
  drift: deliberately renamed an output in `cluster/gcp`, confirmed the
  check failed with the exact right message, then reverted and confirmed
  it passed again.
- `infra/platform` — cloud-neutral Helm releases wired from each `live`
  root: `ingress-nginx`, Argo Rollouts, and `otel-lgtm` (Grafana + Tempo +
  Loki + Mimir, all-in-one) on `cloud-a`; `ingress-nginx` only on `cloud-b`
  (app-only). Verified: traces from a real request are queryable in Tempo
  via Grafana's API.
- `ai/llm` — the shared Gemini client: schema-validated responses via
  Pydantic, cassette record/replay, secret redaction, call budget, 429
  backoff, and a `GeminiUnavailable` escape hatch for deterministic
  fallbacks.
- `app/backend` — FastAPI + Postgres (SQLAlchemy) + OpenTelemetry. Routes:
  `GET/POST /ideas`, `POST /ideas/{id}/upvote`, `GET /healthz` (never
  subject to fault injection). `faults.py` holds every fault mode
  (`panic`, `error500`, `slow`, `leak`, `cpu_burn`, `n_plus_one`), switched
  on by `FAULT_MODE` — the canary track sets it, the stable track never
  does. Tested against both sqlite (unit tests) and the real CNPG Postgres
  on `cloud-a`.
- `app/frontend` — React + Vite. List ideas, add one, upvote. Dev server
  proxies `/api` to the backend; the chart's ingress does the same
  path-based routing in-cluster.
- `deploy/helm/idea-board` — one chart, both components. The backend is an
  Argo `Rollout` (not a plain Deployment) with static canary steps
  (`25% → pause → 50% → pause → 100%`). Verified live: a real canary
  progressed through all steps on `cloud-a`, including with a fault
  (`FAULT_MODE=slow`) active at partial and full traffic.
- `ai/routing` + `ai/evaluator` — feature #4 (adaptive canary routing),
  shadow mode, now on **real metrics**. `app/backend/otel.py` exports
  Prometheus-style metrics (`http_requests_total`, `http_request_duration`)
  to otel-lgtm's Mimir, each one labeled `pod_template_hash` (set via the
  Rollout's downward API) so canary and stable traffic are distinguishable.
  Argo's `AnalysisTemplate` passes the canary's live hash in via
  `valueFrom.podTemplateHashValue: Latest` (no Kubernetes API client
  needed); `ai/evaluator/metrics.py` queries Mimir for that track's error
  rate and p95/p99 over the last minute and feeds them to
  `ai/routing/decide.py`, which has a hard guard (error rate / p99 past a
  fixed threshold is an instant rollback, never put to Gemini) and falls
  back to `advance` on `GeminiUnavailable`. In shadow mode the evaluator
  always reports `advance` to Argo regardless of its real verdict — so it
  can never block yet — but logs the real one. Verified live end to end:
  ran a real canary with `FAULT_MODE=error500`, confirmed Mimir held the
  real per-track request/error/latency series, confirmed the evaluator
  computed a genuine `error_rate=0.83` from them and the hard guard fired a
  real `rollback` verdict off that live number (while still reporting
  `advance` to Argo, per shadow mode), then reran clean (`FAULT_MODE=none`)
  and confirmed a healthy canary's real `error_rate`/`p99_ms` stay under the
  hard guard, so it falls through to Gemini as designed — and, with no
  Gemini key configured in this environment, correctly hits the documented
  `GeminiUnavailable` fallback rather than erroring. Mechanically complete:
  real metrics in, real hard-guard decisions out. A configured Gemini key
  is the only thing between this and a real Gemini-sourced verdict instead
  of the fallback; `AI_MODE_ROUTING=enforce` is a one-line flip once this
  has run in shadow mode long enough to trust.
- `ai/rca` — feature #1 (root cause analysis). `ai/rca/tempo.py` pulls real
  error evidence from Tempo via Grafana's datasource proxy (fixed `uid`
  "tempo", no auth needed in this dev image): it fetches each candidate
  trace in full and keeps only spans Tempo itself marked
  `STATUS_CODE_ERROR`, with whatever real exception (type/message/last few
  stacktrace lines) OTel attached. `ai/rca/analyze.py` feeds that evidence
  to Gemini for a root-cause hypothesis that must cite real trace IDs; on
  `GeminiUnavailable` it never invents a cause — it surfaces the raw cited
  evidence at `confidence: "low"` instead. Runnable now via
  `python -m ai.rca --service idea-board-backend --minutes 5` (not yet
  wired into a pipeline step — that lands with the sim harness). Verified
  live: triggered `FAULT_MODE=panic`, confirmed real `RuntimeError`
  exceptions with real stacktraces showed up in Tempo, and RCA correctly
  cited 12 real (deduplicated) trace IDs for them. **Known gap, flagged
  honestly**: otel-lgtm's bundled Tempo only keeps a short "recent" search
  window in this all-in-one dev image (traces from ~3+ minutes back
  stopped matching `/api/search` in testing) and newly-ingested multi-span
  traces took up to ~60s to become searchable at all — fine for RCA run
  shortly after an incident (the intended use), not for forensics on
  older windows.
- `ai/testsel` — feature #6 (test selection), **the first AI feature that
  actually runs as a CI pipeline step**, not just something provable via
  kubectl. `ai/testsel/select.py` takes a PR's changed files and the
  available test files; a deterministic floor always includes any test
  whose name directly maps to a changed file (`foo.py` → `test_foo.py`,
  never left to the AI), Gemini is asked only for *indirect* impact (e.g.
  a shared module affecting tests that don't share its name), and its
  output is validated against the real test file list before use (a
  hallucinated filename is dropped, not trusted). The unsafe failure mode
  here is skipping a test that mattered, not running an extra one, so
  `GeminiUnavailable` falls back to running every test, not none.
  `ai/testsel/__main__.py` (`python -m ai.testsel --base <ref> --head
  <ref>`) computes the real `git diff` and is wired into `ci.yml`'s new
  `test-select` job, which the `backend` job's pytest step consumes —
  skipped (falls back to running everything) on a plain push, since
  there's no PR base to diff against. Verified with a synthetic repo (this
  repo itself has no commits yet, see below): a hand-crafted cassette
  showed the AI correctly adding an indirectly-affected test
  (`test_faults.py`, because the changed `main.py` wires in fault
  injection) beyond the deterministic direct match, while leaving out an
  unrelated one. **Known gap, flagged honestly**: this repo has zero
  commits, so the `ci.yml` wiring itself (the real `git diff` call) has
  only been proven in an isolated scratch repo, not against this repo's
  own history — that needs an initial commit, which wasn't this session's
  call to make.
- `ai/gatekeeper` — **Pre-Deployment Blast Radius & Migration Gatekeeper**,
  a new feature beyond the original six, scoped to this single-app POC (no
  multi-service dependency graph — there's only one service here). Three
  independent deterministic analyzers, each real static analysis with no
  AI involved:
  - `terraform_risk.py` — walks a real `terraform show -json` plan,
    flagging destructive actions (delete/replace) and overly-broad access
    (public `0.0.0.0/0` CIDRs, wildcard RBAC/IAM grants). Checks both the
    resource's Terraform `type` *and* its `address`, because a CRD applied
    via a generic `kubectl_manifest` type — exactly how this repo's own
    CloudNativePG `Cluster` is applied — never reveals what it actually
    manages through `type` alone. Caught by a real test failure against
    this repo's own plan, not a hypothetical.
  - `migration_risk.py` — regex-based SQL analysis for the classic
    Postgres footguns: a `NOT NULL` column added with no `DEFAULT`
    (exclusive-lock rewrite of every row), `CREATE INDEX` without
    `CONCURRENTLY` (table-wide lock), a foreign key with no supporting
    index.
  - `api_contract.py` — diffs two OpenAPI schemas for breaking changes:
    removed routes, removed fields, newly-required fields.

  `gate.py` combines their findings into one verdict — **computed
  entirely deterministically from finding severity, never by Gemini**.
  Gemini's only role is turning the findings into a human summary and,
  when approval is required, a concrete zero-downtime remediation plan
  (e.g. "split into add-nullable, backfill, then enforce NOT NULL");
  `GeminiUnavailable` never blocks the verdict, only the prose.
  `python -m ai.gatekeeper` is wired into `ci.yml` as a new `blast-radius`
  job for the SQL and API-contract analyzers (`terraform_risk` isn't
  wired there — see below). Verified live against **real** evidence: a
  genuinely destructive Terraform plan against this repo's actual
  `infra/live/local` state (via a safe `-replace`, never applied) was
  correctly flagged `high`/`requires_approval`, with a hand-crafted
  cassette demo producing a real remediation plan; the OpenAPI diff was
  run against the real schema `app.openapi()` generates today, with three
  injected breaking changes all correctly caught. **Known gaps, flagged
  honestly**: (1) `terraform_risk` isn't wired into `ci.yml` — this
  backend's Terraform state lives wherever it was applied, not in CI, so
  a fresh GitHub Actions runner has nothing to plan against without a
  remote state backend (out of scope for this POC); it's proven real
  above, just not as a pipeline step. (2) Same zero-commits gap as test
  selection: the `blast-radius` job's real git-diff/base-ref logic
  degrades gracefully (verified — it doesn't crash) but hasn't been
  exercised against a real PR base yet.
- `ai/reviewmem` — **review memory**: a PR-review bot grounded in past
  human review comments, built after specifically steering away from
  retrieval-gated commenting ("only comment when there's a close
  historical match") toward genuine independent review — retrieval is
  *context* for Gemini's own judgment call, never the gate on whether a
  hunk gets reviewed. Pipeline: `diffsplit.py` splits a unified diff into
  hunks (deterministic text parsing) → `retrieve.py` embeds each hunk via
  `ai/llm/embeddings.py` (a new shared Gemini embeddings client,
  cassette-backed like `generate()`, with a deterministic hashed
  bag-of-words fallback — much lower quality, but retrieval degrades to
  "worse recall," never to "broken") and finds similar entries in
  `data/golden_comments.json` (a hand-seeded corpus, grounded in this
  codebase's own actually-enforced review standards, since this repo has
  no real PR history to mine yet — see below for how a real one would be
  built from the GitHub API) → `review.py` sends the hunk *plus* any
  similar past comments to Gemini and asks it to decide independently:
  is there a real issue here, and does a past comment genuinely apply
  (`grounded_in`) or is this a new observation (`null`)? →
  `gate.py` deterministically caps how many findings actually get
  surfaced, highest severity first. Verified live: a 3-hunk demo diff
  showed all three shapes working — a finding grounded in real historical
  precedent, a second independent grounded finding, and a third
  genuinely new finding (an off-by-one index error) where Gemini
  correctly set `grounded_in: null` despite retrieval surfacing two
  spurious historical "matches" that didn't actually fit. **A real bug
  this caught in its own fallback path**: without a live Gemini key, the
  fallback originally trusted retrieval's top match unconditionally,
  which surfaced a wrong historical citation on completely unrelated code
  (no judgment step to catch a bad match). Fixed with a second, much
  stricter similarity bar (`confident_match`) used only by the
  no-Gemini fallback — silence beats a wrong citation when nothing can
  double-check it. `python -m ai.reviewmem` (reads a unified diff from
  stdin or `--diff`) is wired into `ci.yml`'s `review-memory` job, which
  **does post a real PR comment** via `ai/reviewmem/post.py` (one
  consolidated comment via the `gh` CLI) when there's something to
  report — the intended workflow end to end: a PR opens, this runs
  automatically and comments, and a human reviewer still has the final
  say before merge; the comment itself says so explicitly. Never posts on
  a clean PR (no noise), and `post.py` is the *only* place in this
  feature that writes to GitHub — everything upstream only decides what
  to say. **Known limitation, left as-is rather than papered over**: the
  `pull_request` trigger gives `GITHUB_TOKEN` read-only access for PRs
  from forks, so posting fails there; the fix (`pull_request_target`)
  runs the workflow with write-token access while still checking out the
  fork's own code — a well-known GitHub Actions security footgun — so
  it's not done here without also splitting "run untrusted code" from
  "post with write access" into separate jobs.
- `ai/selfheal` — **self-healing CI**, the most autonomous feature here,
  built with the matching amount of caution: it never touches the
  caller's real working tree or current branch, only disposable `git
  worktree`s, and it never merges anything. Pipeline: `capture.py`
  deterministically parses a failing command's real output for the file(s)
  it implicates (handles both grep-style linter output and ruff's current
  default arrow-pointer format — the second one only surfaced by actually
  running real `ruff` output through it) → `heal.py` asks Gemini for a
  full-file rewrite fix (not a diff — LLMs reliably get unified-diff line
  numbers wrong, a full rewrite sidesteps that failure mode entirely) →
  `apply.py` is the actual gate: applies the proposal in a disposable
  worktree and **re-runs both the original failing command and a broader
  safety-net command for real** — a proposal is never trusted on Gemini's
  word alone, and a fix that "works" but breaks something else is
  rejected the same as one that doesn't fix anything. Only a verified fix
  gets committed (`commit.py`, also worktree-isolated) to a new branch,
  which only then can be opened as a draft PR (`post.py`) against the
  *failing PR's own branch* — "here's a fix for your branch" — never
  `main`, never auto-merged. Verified live end to end against a disposable
  scratch repo (never this one) with a real `ruff` F401 violation: the
  full CLI detected the real failure, proposed a real fix via a
  hand-crafted cassette, verified it by actually re-running `ruff` in an
  isolated worktree, committed it to a new branch — then confirmed
  directly that the scratch repo's checked-out branch and working tree
  were completely unmodified throughout, and that checking out the new
  branch and re-running `ruff` on it for real passed cleanly. Also wired
  into `ci.yml` as `self-heal` (`needs: [backend]`, `if: failure()`) and
  verified against a real (throwaway, immediately-deleted) lint failure
  in this actual repo via `act`: it correctly detected the failure,
  correctly identified the broken file, and — with no live Gemini key
  available locally — honestly reported "needs a human" and exited
  non-zero rather than claiming a fix that was never verified; confirmed
  no branch, commit, or worktree was left behind.
- `.github/workflows/ci.yml` — lint, pytest, `helm lint`, image build,
  Trivy scan, AI-driven test selection, the blast-radius gatekeeper,
  review memory, and self-healing CI on PRs. Fully testable locally via
  `act` (see below); all jobs pass.

### Retrieving real PR review comments (for a production version of `ai/reviewmem`)

This repo's `golden_comments.json` is a seed corpus, not mined data. A
real corpus would come from GitHub's API:

- **REST** `GET /repos/{owner}/{repo}/pulls/{pr}/comments` — line-anchored
  review comments, each with a `diff_hunk` (the code context) and `body`
  (the comment). This is the per-PR backfill source.
- **GraphQL** — the same data, but can traverse *all* PRs and their review
  threads in far fewer calls, and exposes `isResolved`/`isOutdated` on
  threads, which matters for filtering (see below). Use this for bulk
  historical mining; REST alone hits rate limits fast at scale (5000
  req/hr authenticated).
- **Webhooks** (`pull_request_review_comment`) — for keeping the corpus
  fresh going forward, one comment at a time, not for backfill.
- **Filtering matters as much as fetching**: drop bot comments, pure
  "LGTM"/"+1", comments on threads marked `isOutdated` (the code changed
  again afterward, so the comment may no longer apply), and comments
  whose thread was never `isResolved` (often means it was ignored or
  overruled) — otherwise the corpus teaches the model to repeat advice
  that was actually rejected.

AWS/GCP modules, `deploy.yml`, and three features beyond the original
six (blast-radius gatekeeper, review-memory, self-heal) are built and
covered elsewhere in this README. Not yet built: the sim/fault-injection
harness, and two of the five original AI features (profiling, drift
detection) — RCA (#1), adaptive canary routing (#4), and test selection
(#6) are done, see above. NetworkPolicy generation (#3) was dropped
from scope.

### Prerequisites

- OrbStack (or Docker Desktop) running, with `kind`, `kubectl`, `helm`,
  and Terraform ≥ 1.7 on PATH.
- A free-tier Gemini API key — optional. Every AI feature has a
  deterministic fallback and works without one; set it to see the real
  model output instead of the fallback path.

### 1. Bring up the cluster

```sh
make apply-local
```

This creates `cloud-a` (and `cloud-b`, unless you pass `-var
enable_cloud_b=false` to save RAM) kind clusters, installs Cilium,
CloudNativePG (a single-instance Postgres cluster per backend), and the
cloud-neutral platform layer — `ingress-nginx`, Argo Rollouts,
`otel-lgtm` (Grafana/Tempo/Mimir/Loki in one container), and the
`ai-evaluator` service.

All `kubectl`/`helm` commands below target `cloud-a` through its own
kubeconfig file, kept separate from your default `~/.kube/config` on
purpose:

```sh
export KUBECONFIG=infra/live/local/.kubeconfig-cloud-a
```

### 2. Build the app images and load them into the cluster

`kind` clusters don't pull from a registry for local dev — images load
directly from your Docker daemon:

```sh
docker build -t idea-board-backend:local app/backend
docker build -t idea-board-frontend:local app/frontend
kind load docker-image idea-board-backend:local --name cloud-a
kind load docker-image idea-board-frontend:local --name cloud-a
```

### 3. Deploy the app

```sh
helm install idea-board deploy/helm/idea-board \
  --namespace ideaboard --create-namespace \
  -f deploy/helm/idea-board/values-local.yaml
```

`values-local.yaml` sets `pullPolicy: Never` (use whatever's already
loaded, never attempt a registry pull) and trims resource requests to
fit a laptop. Watch it come up:

```sh
kubectl -n ideaboard get pods -w
```

### 4. Reach the app

Simplest path — port-forward straight to the services, bypassing
ingress entirely:

```sh
kubectl -n ideaboard port-forward svc/idea-board-frontend 8080:80 &
kubectl -n ideaboard port-forward svc/idea-board-backend 8000:8000 &
```

Then:

```sh
open http://localhost:8080/                      # the UI
curl http://localhost:8000/healthz                # {"status":"ok"}
curl -X POST http://localhost:8000/ideas \
  -H "Content-Type: application/json" \
  -d '{"text":"my first idea"}'
curl http://localhost:8000/ideas                  # lists it back
```

(The chart also renders two `Ingress` objects for `idea-board.local`,
matching the real cloud deploys — but kind's ingress controller has no
external IP locally, so port-forwarding is the reliable path for local
dev.)

### 5. Tear down

```sh
make destroy-local
```

### Record/replay the first Gemini call

```sh
GEMINI_API_KEY=... LIVE=1 make smoke-ai   # records ai/evals/cassettes/smoke/*.json
make smoke-ai                             # replays it, no network, no key needed
```

### Run the app locally (without the cluster)

```sh
cd app/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
DATABASE_URL="sqlite:///./dev.db" pytest tests/       # unit tests
DATABASE_URL="sqlite:///./dev.db" uvicorn main:app --port 8000

cd app/frontend
npm install
npm run dev   # proxies /api to localhost:8000
```

### Run `ci.yml` locally

```sh
act pull_request              # whole workflow
act pull_request -j backend   # one job
```

No GitHub repo, no push, no runner registration needed — `.actrc` points
`act` at a fuller runner image than its default. Note: this repo's `act`
install may be behind; check `act --version` against the [releases
page](https://github.com/nektos/act/releases) for known CVEs before relying
on it for anything beyond local dev.

### Open questions (from the plan, still unresolved)

- Mac RAM available — decides whether `cloud-b` runs the full stack or
  just the app.
- Submission deadline.
- Slack webhook, or GitHub comments only, for AI feature output?
- Public or private repo?
- Public link needed for reviewers, or recordings enough?
