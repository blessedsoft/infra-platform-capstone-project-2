# Design decisions

- Python standard library keeps the sample build fast and dependency-free.
- One small container image is configured as three services, reducing duplicated code while preserving independent Deployments and Service DNS names.
- Kustomize overlays separate staging and production image tags and replica policy.
- Argo CD owns Kubernetes state. Staging has automated prune/self-heal; production requires an explicit sync.
- Prometheus Operator resources are used for scraping and alerting because they are native to kube-prometheus-stack.
- Secrets and notification endpoints are deliberately created out of band.
