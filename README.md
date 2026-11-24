# GitOps Platform with Monitoring

This repository is a small, runnable reference implementation for the Capstone 2. It contains three Python services, a CI pipeline, Kubernetes GitOps manifests, and an observability baseline.

## Architecture

```text
client -> gateway:8080 -> catalog:8080
                     \-> orders:8080

services -- /metrics --> Prometheus --> Grafana dashboards
pods -- structured JSON logs --> Promtail --> Loki
services -- trace_id in logs --> Grafana/Loki (Tempo values included for OTLP)
PrometheusRule --> Alertmanager --> platform-oncall / infrastructure
```

The gateway calls both backend services, so the deployment demonstrates service-to-service communication. All services expose `/healthz` and `/metrics` and emit JSON logs containing `trace_id`.

## Repository layout

```text
app/                         shared service implementation and tests
.github/workflows/ci.yml     lint, test, scan, build, publish, GitOps update
gitops/                      Kustomize base, staging/production overlays, Argo CD
observability/               Helm values, dashboards, rules, Alertmanager config
runbooks/                    response procedures for the five alerts
```

## Local run

```bash
python -m unittest discover -s app -p 'test_*.py' -v
docker compose up --build
curl http://localhost:8080/healthz
curl http://localhost:8080/api/catalog
curl http://localhost:8080/metrics
```

## CI and GitOps

Pushes to any branch run lint, unit tests, and a Trivy filesystem scan. A push to `main` builds three images and pushes them to GHCR, then updates the staging image tag in the GitOps repository. Set `GITOPS_REPOSITORY` and a `GITOPS_TOKEN` secret for the update step; when this repository is used as a single-repository demo, the workflow can update its own `gitops/` directory instead.

Staging is automated with prune and self-heal. Production has no automated sync policy and must be promoted explicitly in Argo CD. Reverting the image-tag commit in the GitOps repository rolls back staging automatically; production rolls back after its next manual sync.

```bash
kubectl apply -f gitops/namespaces.yaml
kubectl apply -f gitops/argocd/staging.yaml
kubectl apply -f gitops/argocd/production.yaml
kubectl apply -k gitops/overlays/staging
```

See [`docs/deployment.md`](docs/deployment.md) for cluster setup, monitoring installation, drift, promotion, and rollback procedures. No credentials are committed; registry and notification secrets are created out of band.
