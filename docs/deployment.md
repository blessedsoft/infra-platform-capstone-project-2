# Deployment guide

## Prerequisites

Use a Kubernetes cluster with Helm 3, `kubectl`, Argo CD, and the Prometheus Operator CRDs. Make GHCR images readable by the cluster, or create an image pull secret out of band and reference it from the deployments.

## Application and GitOps

Replace `REPLACE_OWNER`, `REPLACE_ORG`, and `REPLACE_REPO` in the manifests. Install Argo CD, then apply:

```bash
kubectl apply -f gitops/namespaces.yaml
kubectl apply -f gitops/argocd/staging.yaml
kubectl apply -f gitops/argocd/production.yaml
```

Staging automatically syncs and self-heals. Production is intentionally manual: select `capstone-production` in Argo CD and click Sync only after staging verification. A Git revert of the staging tag commit is the rollback mechanism.

## Observability

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
kubectl apply -f observability/namespace.yaml
kubectl -n observability create secret generic grafana-admin --from-literal=admin-user=admin --from-literal=admin-password="$(openssl rand -base64 24)"
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack -n observability -f observability/prometheus-values.yaml -f observability/alertmanager-values.yaml
helm upgrade --install loki grafana/loki -n observability -f observability/loki-values.yaml
helm upgrade --install tempo grafana/tempo -n observability -f observability/tempo-values.yaml
helm upgrade --install promtail grafana/promtail -n observability -f observability/promtail-values.yaml
kubectl apply -f observability/alerts.yaml
```

Install Promtail or Grafana Alloy for pod logs, pointing it at the Loki service. Import the three JSON dashboards in `observability/dashboards/`. The Alertmanager URLs are placeholders; replace them with approved channels using a Secret before production.

## Verification

```bash
kubectl -n capstone-staging rollout status deploy/gateway
kubectl -n capstone-staging port-forward svc/gateway 8080:8080
curl http://localhost:8080/healthz
curl http://localhost:8080/api/catalog
kubectl -n observability get prometheusrules,servicemonitors
```

For drift testing, change the live staging replica count with `kubectl`; Argo CD should restore Git state. For an alert test, temporarily lower an alert threshold in a test cluster and confirm the matching Alertmanager receiver.
