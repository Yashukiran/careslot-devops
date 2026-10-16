#!/usr/bin/env bash
# Generates traffic against the API so the Grafana panels and the HPA have something to show.
#
#   ./scripts/loadtest.sh http://<ingress-hostname> 300 20
#     arg1 = base url, arg2 = duration in seconds, arg3 = parallel workers
#
# Runs inside the cluster instead if no url is given:
#   ./scripts/loadtest.sh
set -euo pipefail

URL=${1:-}
DURATION=${2:-300}
WORKERS=${3:-20}

if [ -z "$URL" ]; then
  echo "no url given, starting an in-cluster load generator (ctrl+c to stop)"
  kubectl run loadgen -n careslot --rm -it --restart=Never --image=busybox:1.36 -- \
    sh -c "end=\$((\$(date +%s)+$DURATION)); while [ \$(date +%s) -lt \$end ]; do
             for i in \$(seq $WORKERS); do wget -q -O- http://careslot-backend:8000/api/stats >/dev/null & done; wait;
           done"
  exit 0
fi

echo "hitting $URL for ${DURATION}s with $WORKERS workers"
end=$(( $(date +%s) + DURATION ))
worker() {
  while [ "$(date +%s)" -lt "$end" ]; do
    curl -s -o /dev/null "$URL/api/stats"
    curl -s -o /dev/null "$URL/api/appointments"
    curl -s -o /dev/null "$URL/api/doctors"
  done
}
for _ in $(seq "$WORKERS"); do worker & done
wait
echo "done - check: kubectl get hpa -n careslot"
