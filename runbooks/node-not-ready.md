# Node not ready

Check `kubectl get nodes` and `kubectl describe node NODE`. Confirm capacity, kubelet health, and cloud-provider events. Cordon/drain only under the cluster operator procedure and verify workloads reschedule.
