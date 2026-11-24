# High error rate

Check the gateway logs using the alert `trace_id`, then call `/healthz` for gateway, catalog, and orders. Inspect the latest deployment and upstream availability. Roll back the last GitOps image commit if the error started with a release.
