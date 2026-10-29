#!/usr/bin/env bash

# M1 baseline: capture readable HTTP on the WAN side of gw-hq
# while client-br fetches the portal.

set -euo pipefail

cd "$(dirname "$0")/.."
source .env

OUT=/work/evidence/pcaps/M1_baseline_wan.pcap
WAN_IP="172.16.${GROUP_NUM}.10"

# Start packet capture on the WAN interface of gw-hq.
docker compose exec -T gw-hq bash -c "
    IF=\$(ip -o -4 addr show | awk '/${WAN_IP//./\\.}\\// {print \$2}')
    echo \"WAN interface of gw-hq: \$IF\"
    rm -f $OUT
    timeout 12 tcpdump -n -i \$IF -w $OUT
" &

CAPTURE_PID=$!

# Allow tcpdump to start.
sleep 4

# Generate traffic from the branch client to the HQ web server.
docker compose exec -T client-br bash -c "
    ping -c 3 10.${GROUP_NUM}.1.10
    curl -s http://10.${GROUP_NUM}.1.10/ | head -3
"

# Wait for the capture to finish.
wait "$CAPTURE_PID" || true

echo
echo "--- HTTP requests found in the capture ---"

docker compose exec -T gw-hq bash -c "
    tshark -r $OUT \
        -Y http.request \
        -T fields \
        -e ip.src \
        -e ip.dst \
        -e http.request.full_uri \
        2>/dev/null
"

echo
echo "--- Known plaintext marker found in the capture ---"

docker compose exec -T gw-hq bash -c "
    tshark -r $OUT \
        -Y 'frame contains \"SCP-BASELINE-KNOWN-PLAINTEXT\"' \
        -T fields \
        -e frame.number \
        -e ip.src \
        -e ip.dst \
        2>/dev/null
"

echo
echo "Baseline capture verification completed."
