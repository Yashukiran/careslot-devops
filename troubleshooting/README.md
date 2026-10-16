# Troubleshooting lab

Two deliberately broken manifests for the live failure demo. Both go into the `careslot` namespace next to the real release.

## Lab 1 – ImagePullBackOff

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n careslot -l app=broken-image
```

The pod sits in `ErrImagePull` and then `ImagePullBackOff`.

**Investigate**

```bash
kubectl describe pod -n careslot -l app=broken-image     # look at the Events section
kubectl get events -n careslot --sort-by=.lastTimestamp | tail
```

The events show `manifest unknown` / `not found` for `careslot-backend:does-not-exist`. The registry is reachable but that tag was never pushed (CI only pushes commit SHA tags).

**Fix**: point the deployment at a tag that exists:

```bash
TAG=$(kubectl get deploy careslot-backend -n careslot -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)
kubectl set image deployment/broken-image api=ghcr.io/yashukiran/careslot-backend:$TAG -n careslot
kubectl get pods -n careslot -l app=broken-image -w
```

It will now pull, but crash because it has no `DATABASE_URL`. That's expected for this lab, the point was the image. Clean up with `kubectl delete -f troubleshooting/broken-image.yaml`.

## Lab 2 – Service with no endpoints

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl run curl -n careslot --rm -it --image=curlimages/curl --restart=Never -- \
    curl -m 5 http://careslot-backend-broken:8000/health
```

The curl times out even though the backend pods are healthy.

**Investigate**

```bash
kubectl get svc careslot-backend-broken -n careslot
kubectl get endpoints careslot-backend-broken -n careslot     # <none>
kubectl get pods -n careslot --show-labels | grep backend
```

A Service only sends traffic to pods whose labels match its selector. The selector says `app.kubernetes.io/name=careslot-api` but the pods are labelled `app.kubernetes.io/name=backend`, so the endpoint list is empty.

**Fix**

```bash
kubectl patch svc careslot-backend-broken -n careslot \
  -p '{"spec":{"selector":{"app.kubernetes.io/name":"backend"}}}'
kubectl get endpoints careslot-backend-broken -n careslot      # now lists 2 pod IPs
```

Run the curl again and it returns `{"status":"UP"}`. Clean up with `kubectl delete -f troubleshooting/broken-service.yaml`.

## Other quick checks

| Symptom | Command |
|---|---|
| Pod restarting | `kubectl logs <pod> -n careslot --previous` |
| Pod not Ready | `kubectl describe pod <pod>`: check the `/ready` probe; usually the DB is down |
| Ingress 404 / 503 | `kubectl describe ingress careslot -n careslot` and `kubectl get endpoints -n careslot` |
| HPA shows `<unknown>` | metrics-server missing: `kubectl top pods -n careslot` |
| PVC Pending | no default StorageClass: `kubectl apply -f k8s/storageclass-gp3.yaml` |
