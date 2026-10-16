#!/usr/bin/env bash
# Runs the whole Kubernetes part of the project on a local kind cluster (no AWS needed):
# metrics-server, ingress-nginx, prometheus + grafana, then the careslot chart.
#
#   ./scripts/setup-local-cluster.sh            # deploys the image of the current commit
#   ./scripts/setup-local-cluster.sh <sha>      # or a specific image tag from GHCR
#
# App:      http://careslot.127.0.0.1.nip.io
# Teardown: kind delete cluster --name careslot
set -euo pipefail
cd "$(dirname "$0")/.."

CLUSTER=careslot
CTX=kind-$CLUSTER
TAG=${1:-$(git rev-parse HEAD)}
OWNER=yashukiran

if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --name "$CLUSTER" --config k8s/kind-cluster.yaml
fi

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo update >/dev/null

kubectl --context "$CTX" apply -f k8s/namespace.yaml

# kind's kubelet uses a self-signed cert, hence --kubelet-insecure-tls
helm upgrade --install metrics-server metrics-server/metrics-server --kube-context "$CTX" \
  -n kube-system --set 'args={--kubelet-insecure-tls}' --wait

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --kube-context "$CTX" \
  -n ingress-nginx --create-namespace -f monitoring/ingress-nginx-kind-values.yaml --wait

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack --kube-context "$CTX" \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml --wait --timeout 15m

kubectl --context "$CTX" apply -f monitoring/grafana-dashboard.yaml

helm upgrade --install careslot ./helm/careslot --kube-context "$CTX" \
  -n careslot --create-namespace \
  -f helm/careslot/values-dev.yaml -f helm/careslot/values-local.yaml \
  --set backend.image.repository=ghcr.io/$OWNER/careslot-backend \
  --set frontend.image.repository=ghcr.io/$OWNER/careslot-frontend \
  --set backend.image.tag="$TAG" --set frontend.image.tag="$TAG" \
  --wait --timeout 10m

kubectl --context "$CTX" get pods,svc,ingress,hpa -n careslot
echo
echo "app:        http://careslot.127.0.0.1.nip.io"
echo "prometheus: kubectl --context $CTX -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090"
echo "grafana:    kubectl --context $CTX -n monitoring port-forward svc/kube-prometheus-stack-grafana 3002:80   (admin / careslot-admin)"
