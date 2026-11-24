# Pod crash looping

Run `kubectl -n capstone-staging describe pod POD` and inspect `kubectl logs POD --previous`. Correct configuration or image issues, then deploy through Git. Do not edit the live Deployment because Argo CD will self-heal it.
