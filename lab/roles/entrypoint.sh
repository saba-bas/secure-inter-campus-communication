#!/usr/bin/env bash
# Generic node start-up: names, routes, and optional services once the group has written them.
set -u
G="${GROUP_NUM:?}"; ID="${GROUP_ID:?}"; D="g${ID}.scp.lab"
log(){ echo "[$ROLE] $*"; }

# lab "DNS" = /etc/hosts
cat >> /etc/hosts <<HOSTS
10.$G.1.10   portal.$D pki.$D web-hq.$D
10.$G.1.20   kdc.$D
172.16.$G.10 gw-hq.$D
172.16.$G.20 gw-branch.$D
172.16.$G.66 attacker.$D
HOSTS

# routes (internal networks have no default gateway)
case "$ROLE" in
  gw-hq)      ip route replace 10.$G.2.0/24 via 172.16.$G.20 ;;
  gw-branch)  ip route replace 10.$G.1.0/24 via 172.16.$G.10 ;;
  web-hq|kdc) ip route replace 10.$G.2.0/24 via 10.$G.1.1 ;;
  client-br)  ip route replace 10.$G.1.0/24 via 10.$G.2.1; ip route replace 172.16.$G.0/24 via 10.$G.2.1 ;;
  attacker)   ip route replace 10.$G.2.0/24 via 172.16.$G.20 ;;   # NO route to the HQ LAN
esac

# gateways: firewall first (fail-closed), then strongSwan - only when the group has written them
if [[ "$ROLE" == gw-* ]]; then
  SITE="${ROLE#gw-}"
  [[ -x /work/ipsec/hardening/gw_firewall.sh ]] && /work/ipsec/hardening/gw_firewall.sh "$SITE"
  if [[ -f /work/ipsec/$ROLE/swanctl.conf ]]; then
    mkdir -p /etc/swanctl && ln -sf /work/ipsec/$ROLE/swanctl.conf /etc/swanctl/swanctl.conf
    /usr/sbin/charon-systemd >/var/log/charon.log 2>&1 &
    sleep 3; swanctl --load-all || log "swanctl load failed"
  else
    log "no swanctl.conf -> LANs routed over the WAN in CLEAR TEXT (M1 baseline)"
  fi
fi

# web-hq: nginx portal if written, else the plain-HTTP baseline page
if [[ "$ROLE" == web-hq ]]; then
  if [[ -f /work/tls/nginx/portal.conf ]]; then
    ln -sf /work/tls/nginx/portal.conf /etc/nginx/conf.d/portal.conf; rm -f /etc/nginx/sites-enabled/default; nginx
  else
    log "baseline: plain HTTP on :80"
    (cd /work/lab/baseline_html && exec python3 -m http.server 80 --bind 0.0.0.0) &
  fi
fi
log "ready"; exec sleep infinity
