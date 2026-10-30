# Secure Inter-Campus Communication Network - Group <GROUP_ID>
Course 1305301 - Secure Communication Protocols - First Semester 2026/2027

Status: **M1 (Analysis, Design & Baseline)**. Later milestones add pki/, crypto/, tls/, ipsec/, auth_protocols/, attacks/, tests/.

## M1 contents
| Deliverable | Path |
|---|---|
| Requirements, Topology/Trust, PKI design, Protocol design, Team plan | docs/M1/*.pdf |
| STRIDE threat model | docs/M1/M1_STRIDE.xlsx |
| Baseline WAN capture (you produce it, see below) | evidence/pcaps/M1_baseline_wan.pcap |
| Lab (written by the group; no starter kit was provided) | lab/ |

## 1. Prepare the lab (Docker Engine + Compose v2, or Docker Desktop with WSL2)
```bash
docker compose version && git --version
cd lab
cp .env.example .env        # edit: GROUP_ID=07 (two digits) and GROUP_NUM=7 (no leading zero)
docker compose up -d --build   # first build needs internet; afterwards the lab is offline
docker compose ps              # all 6 containers must be "running"
docker compose logs gw-hq | tail   # expect: "no swanctl.conf -> ... CLEAR TEXT"
docker compose exec client-br bash # repo is mounted at /work in every container
```
Stop: `docker compose down`.

## 2. Baseline (clear-text WAN)
```bash
docker compose exec client-br ping -c 3 10.${GROUP_NUM}.1.10   # run inside the node: replace G by your number
./scripts/baseline_capture.sh                                   # on the host, from lab/
```
This writes `evidence/pcaps/M1_baseline_wan.pcap` (tcpdump on gw-hq WAN interface) and prints the readable HTTP request and the marker `SCP-BASELINE-KNOWN-PLAINTEXT`. Open the pcap in Wireshark and keep a screenshot **plus** the command output as evidence.

## 3. Regenerate the documents with your own names
```bash
cd docs/tools
GROUP_NUM=7 GROUP_ID=07 M1_NAME="Name (ID)" M2_NAME="-" M3_NAME="-" ./make_docs.sh
```

## 4. Ports used by the lab
TCP 80/443 (web-hq), TCP 8800 (KDC), TCP 8801 (Kerberos service), UDP 500/4500 + ESP (gateways).

## 5. Tag M1
```bash
git add -A && git status        # no .env, no keys, no secrets!
git commit -m "M1: analysis, design, baseline"
git tag -a M1 -m "Milestone 1" && git push origin main --tags
```
