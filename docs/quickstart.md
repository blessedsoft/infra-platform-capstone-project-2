# Quick start

This guide runs the platform locally on Windows with Docker Desktop Kubernetes. Commands use Windows Command Prompt syntax.

## Prerequisites

Install and start:

- Docker Desktop with Kubernetes enabled
- Git
- `kubectl`
- Helm 3
- A GitHub repository and GHCR access for Kubernetes image pulls

Confirm the tools and cluster:

```cmd
docker --version
kubectl version --client
helm version
kubectl config current-context
```

The examples below assume the Docker Desktop context:

```cmd
kubectl config use-context docker-desktop
```

## 1. Run locally with Docker Compose

Build and start the three application services:

```cmd
docker-compose up --build -d
```

The gateway normally uses port `8080`. If another local service already owns that port, start the gateway on `8081`:

```cmd
docker-compose run --no-deps -d -p 8081:8080 gateway
```

Verify the local application:

```cmd
curl.exe http://localhost:8081/healthz
curl.exe http://localhost:8081/api/catalog
curl.exe http://localhost:8081/metrics
```

Use port `8080` instead if the Compose gateway successfully owns it.

## 2. Run tests

```cmd
python -m py_compile app\service.py app\test_service.py
python -m unittest discover -s app -p "test_*.py" -v
```

## 3. Configure GitHub and GHCR

The repository uses these image names:

```text
ghcr.io/blessedsoft/capstone-gateway
ghcr.io/blessedsoft/capstone-catalog
ghcr.io/blessedsoft/capstone-orders
```

The GitOps repository URL is:

```text
https://github.com/blessedsoft/infra-platform-capstone-project-2.git
```

Before deploying, confirm there are no unresolved placeholders:

```cmd
findstr /S /N "REPLACE_ IMAGE_TAG PROMOTE_TAG" gitops\*.yaml gitops\*\*.yaml
```

The `main` GitHub Actions workflow builds and publishes the three GHCR images. Its final update step writes the successful commit SHA to the staging overlay.

## 4. Deploy the application to staging Kubernetes

Create the namespaces:

```cmd
kubectl apply -f gitops\namespaces.yaml
```

Apply the staging overlay:

```cmd
kubectl apply -k gitops\overlays\staging
```

If Kubernetes reports that `ServiceMonitor` is unknown, install the monitoring stack in the next section first, then re-run the command.

Verify the application:

```cmd
kubectl -n capstone-staging get deployments,pods,services,endpointslices
kubectl -n capstone-staging rollout status deployment/catalog
kubectl -n capstone-staging rollout status deployment/gateway
kubectl -n capstone-staging rollout status deployment/orders
```

Port-forward the gateway on `8082` to avoid a local port-8080 conflict:

```cmd
kubectl -n capstone-staging port-forward service/gateway 8082:8080
```

In another Command Prompt:

```cmd
curl.exe http://localhost:8082/healthz
curl.exe http://localhost:8082/api/catalog
curl.exe http://localhost:8082/metrics
```

## 5. Install Prometheus, Grafana, and Alertmanager

Add the chart repository and create the observability namespace:

```cmd
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl apply -f observability\namespace.yaml
```

Create the Grafana admin secret. Use a strong local password instead of the example value:

```cmd
kubectl -n observability create secret generic grafana-admin ^
  --from-literal=admin-user=admin ^
  --from-literal=admin-password=ChangeThisStrongPassword123!
```

Install the stack:

```cmd
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack ^
  -n observability ^
  -f observability\prometheus-values.yaml ^
  -f observability\alertmanager-values.yaml ^
  --set nodeExporter.enabled=false
```

The node-exporter is disabled for Docker Desktop because its host-root mount fails with:

```text
path / is mounted on / but it is not a shared or slave mount
```

Use a Linux Kubernetes cluster for complete host filesystem and node-exporter metrics.

Wait for the monitoring components:

```cmd
kubectl -n observability get pods -w
```

Continue when Prometheus, Grafana, Alertmanager, the operator, and kube-state-metrics are `Running` and ready.

## 6. Apply scraping and alert rules

```cmd
kubectl apply -k gitops\overlays\staging
kubectl apply -f observability\alerts.yaml
kubectl -n capstone-staging get servicemonitor
kubectl -n observability get prometheusrules
```

The project defines these alerts:

```text
HighErrorRate
HighLatency
PodCrashLooping
NodeNotReady
DiskSpaceLow
```

## 7. Verify Prometheus and Grafana

Find the service names:

```cmd
kubectl -n observability get services
```

Port-forward Prometheus:

```cmd
kubectl -n observability port-forward service/monitoring-kube-prometheus-prometheus 9090:9090
```

Open `http://localhost:9090/targets` and confirm application targets are `UP`.

Port-forward Grafana:

```cmd
kubectl -n observability port-forward service/monitoring-grafana 3000:80
```

Open `http://localhost:3000`, sign in with the Grafana secret credentials, and import:

```text
observability/dashboards/service-overview.json
observability/dashboards/infrastructure.json
observability/dashboards/logs.json
```

## 8. Optional Argo CD deployment

Install Argo CD separately, then apply the configured applications:

```cmd
kubectl apply -f gitops\argocd\staging.yaml
kubectl apply -f gitops\argocd\production.yaml
kubectl -n argocd get applications
```

Staging is configured for automated sync and self-healing. Production requires an explicit manual sync.

## Troubleshooting

Check application pod events:

```cmd
kubectl -n capstone-staging get events --sort-by=.lastTimestamp
kubectl -n capstone-staging describe pod <pod-name>
```

Check monitoring events:

```cmd
kubectl -n observability get events --sort-by=.lastTimestamp
```

`CreateContainerConfigError` for the application pods usually indicates an image security-context problem. The application image must use a numeric non-root user; this project uses UID `10001` in the Dockerfile.

`Select-String` is a PowerShell command. In Command Prompt, use `findstr` instead:

```cmd
kubectl kustomize gitops\overlays\staging | findstr "image:"
```
