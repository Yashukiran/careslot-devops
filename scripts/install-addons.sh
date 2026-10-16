#!/usr/bin/env bash
# One-time cluster setup after `terraform apply`:
# storage class, ingress controller, prometheus + grafana, and the dashboard.
set -euo pipefail
cd "$(dirname "$0")/.."

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/storageclass-gp3.yaml

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# monitoring first so the ServiceMonitor CRD exists before the app chart uses it
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/kube-prometheus-stack-values.yaml --wait --timeout 10m

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  -n ingress-nginx --create-namespace \
  -f monitoring/ingress-nginx-values.yaml --wait --timeout 10m

kubectl apply -f monitoring/grafana-dashboard.yaml

echo
echo "ingress load balancer (can take a couple of minutes to get a hostname):"
kubectl get svc ingress-nginx-controller -n ingress-nginx
