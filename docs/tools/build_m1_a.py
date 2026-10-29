"""M1 documents A: Requirements, Topology/Trust, PKI Design."""
import os
from m1lib import *

OUT = os.path.join(os.path.dirname(__file__), "..", "M1")
TMP = "/tmp/m1img"; os.makedirs(TMP, exist_ok=True); os.makedirs(OUT, exist_ok=True)


def requirements():
    uc = f"{TMP}/uc.png"; usecase_diagram(uc)
    s = cover("M1 - Requirements Document", "Secure Inter-Campus Communication Network (HQ campus <-> Branch campus)")
    s += [H1("1. Purpose and scope"),
          P(f"The university has an HQ campus (10.{G}.1.0/24) and a Branch campus (10.{G}.2.0/24) joined by an untrusted WAN "
            f"(172.16.{G}.0/24). Group {GID} builds, from scratch, the secure communication layer between them: a two-tier PKI, a TLS portal "
            "with a mutual-TLS staff area, a certificate-authenticated IKEv2/IPsec site-to-site VPN, a Kerberos-style authentication "
            "protocol, and a small cryptographic message tool. The group then attacks its own system from the lab attacker node and "
            "proves with captures and logs that legitimate traffic succeeds and every attack is refused."),
          P("<b>In scope:</b> everything in FR01-FR12 and SR01-SR14 of the project specification (v1.0). <b>Out of scope:</b> implementing "
            "cipher primitives (taken from OpenSSL, strongSwan, pyca/cryptography); OCSP responder (CRL only - OCSP is discussed in the "
            "report); any traffic outside the group's Docker lab; real browser/OS trust-store changes."),
          H1("2. Actors"),
          T([["Actor", "Description", "Trust level"],
             ["Public visitor", "Anyone who opens the public portal pages over HTTPS. No credentials.", "Untrusted, anonymous"],
             ["Staff member", f"Employee at the Branch campus (client-br, 10.{G}.2.10) holding a staff certificate (staff01..03) and a Kerberos principal.", "Authenticated by certificate and by KDC tickets"],
             ["Administrator", "Group member who builds the PKI, issues/revokes certificates, runs tests and attacks. Holds the Root CA passphrase.", "Fully trusted (privileged)"],
             ["Adversary (not a user)", f"Attacker node 172.16.{G}.66 on the WAN: captures, scans, spoofs, replays. Lab only.", "Hostile - modelled in STRIDE"]],
            [3.2, 10.0, 4.2]),
          Spacer(1, 4), IMG(uc, 15.5), P("Figure 1 - Use-case diagram (staff, visitor, administrator).", "cap"),
          H1("3. Use cases"),
          T([["ID", "Use case / actor", "Pre-condition", "Main flow", "Post-condition / alternative flow"],
             ["UC1", "View public portal - visitor", "Lab up; portal certificate issued", f"Visitor opens http://portal.{D}/ -> 301 to https -> TLS 1.3 handshake -> certificate chain verified -> public page shown", "HSTS header received. Alt: TLS 1.0/1.1 or non-AEAD suite -> handshake refused (T6)"],
             ["UC2", "Open /staff/ - staff", "Staff certificate valid, not revoked; CRL current", "Client presents certificate -> nginx verifies chain (depth 2) + CRL -> page shows subject identity", "Identity logged. Alt: no cert / revoked cert -> generic error page, attempt logged (T4)"],
             ["UC3", "Kerberos-style login - staff", "Principal and long-term key registered at KDC", "AS exchange (TGT) -> TGS exchange (service ticket) -> AP exchange with mutual authentication and key confirmation", "Fresh session key on both sides. Alt: wrong password -> generic refusal, nothing revealed (T11); replay -> rejected (T12b)"],
             ["UC4", "Use crypto tool - staff/admin", "scpcrypt.py on client-br", "sign/verify, mac, encrypt/decrypt (AEAD), ecdh", "Any modified byte -> rejected (T2)"],
             ["UC5", "Reach HQ from Branch - staff (transparent)", "IKEv2 SA established", f"Packet 10.{G}.2.10 -> 10.{G}.1.10 enters gw-branch, goes in ESP over WAN, leaves gw-hq", "WAN shows only IKE/ESP (T7). Alt: tunnel down -> traffic dropped, never forwarded in clear (T9)"],
             ["UC6", "Build PKI - admin", "Empty folder, OpenSSL 3", "build_pki.sh creates Root CA (offline, passphrase), Issuing CA, all lab certs, CRL", "Chains verify (T1); inventory written"],
             ["UC7", "Issue certificate - admin", "CSR + profile name", "issue.sh <profile> <name> signs CSR with Issuing CA", "SAN, KU, EKU as profile; random serial; key mode 600"],
             ["UC8", "Revoke + publish CRL - admin", "Certificate issued", "revoke.sh <name> updates index, regenerates issuing.crl, publishes it", "nginx and strongSwan refuse the certificate (T4, T8)"],
             ["UC9", "Run attacks and tests - admin", "Lab up", "tests/run_all.sh runs T1-T13, writes evidence/", "Unified log with expected/actual/PASS-FAIL (SR14)"],
             ["UC10", "Rebuild from scratch - admin", "Clean machine", "Follow README, run scripts in order", "All tests reproduce documented results (T13)"]],
            [1.0, 3.0, 3.0, 5.6, 4.8]),
          PageBreak(), H1("4. Functional requirements and traceability"),
          P("Every requirement has a measurable acceptance criterion, the test that proves it (T-numbers from the specification) and the milestone in which it is delivered."),
          T([["ID", "Requirement", "Acceptance criterion", "Test", "Milestone"],
             ["FR01", "One script builds the complete two-tier PKI from an empty folder, reproducibly", "Run on empty dir twice: same structure; no manual step; all chains verify", "T1, T13", "M2"],
             ["FR02", "Certificates issued from CSRs by named profiles; chains verify", "openssl verify OK for all; rogue-CA cert fails", "T1", "M2"],
             ["FR03", "Revocation: revoke, publish new CRL; nginx AND strongSwan enforce it", "Revoked staff cert refused by nginx after CRL update; revoked gateway cert refused by IKE", "T4, T8", "M2 (nginx), M3 (IKE), M4 (demo)"],
             ["FR04", "Portal HTTPS only, HTTP->HTTPS redirect, HSTS", "curl -I http:// gives 301; HSTS header present; testssl clean", "T6", "M2"],
             ["FR05", "/staff/ needs a valid client certificate and shows the identity", "With cert: 200 + subject shown; without: generic error", "T3, T4", "M2"],
             ["FR06", "IKEv2 tunnel comes up automatically at lab start with certificates", "swanctl --list-sas shows ESTABLISHED/INSTALLED right after docker compose up", "T7", "M3"],
             ["FR07", "Only HQ-LAN <-> Branch-LAN tunnelled, explicit traffic selectors", f"TS = 10.{G}.1.0/24 <=> 10.{G}.2.0/24; WAN-to-other traffic not protected", "T7, T10", "M3"],
             ["FR08", "Crypto tool: sign/verify, MAC, AEAD, key agreement; detects modified byte", "RFC 4231 and RFC 8032 vectors pass; tamper tests rejected", "T2", "M2"],
             ["FR09", "KDC authenticates principal, issues TGT and service ticket", "Right password: TGT+ST; wrong: generic refusal", "T11", "M3"],
             ["FR10", "Client and service mutually authenticate and confirm fresh session key; replay rejected", "Key confirmation messages verify; replayed authenticator rejected and logged", "T11, T12b", "M3"],
             ["FR11", "Whole system rebuildable from README + scripts in order", "Clean machine rebuild reproduces all tests", "T13", "M4"],
             ["FR12", "Weak variants only in attacks/, never in final config", "grep of final configs finds no weak setting/PSK; run_all checks it", "T6, T8, T12a", "M3/M4"]],
            [1.2, 5.0, 6.0, 1.7, 3.5]),
          H1("5. Security requirements (summary)"),
          T([["SR", "Topic", "Verified by", "SR", "Topic", "Verified by"],
             ["SR01", "Algorithms, nonce never reused", "T2, code review", "SR08", "Gateway hardening, fail-closed", "T9, T10"],
             ["SR02", "PKI hierarchy, offline Root", "T1, inventory", "SR09", "Auth protocol design (PROTOCOL.md)", "T11"],
             ["SR03", "CRL enforced (nginx + IKE)", "T4, T8", "SR10", "Weak vs fixed protocol, replay", "T12a/b"],
             ["SR04", "TLS configuration", "T6, testssl", "SR11", "No secrets in Git, scan", "T13"],
             ["SR05", "Mutual TLS, identity logged", "T3, T4", "SR12", "WAN before/after, keylog exercise", "T7"],
             ["SR06", "MITM resistance (rogue CA)", "T5", "SR13", "Downgrade tests", "T6, T8"],
             ["SR07", "IKEv2 certs only, pinned identity, PFS", "T7, T8", "SR14", "Unified test log", "test_log.xlsx"]],
            [1.2, 4.3, 2.6, 1.2, 5.2, 2.9]),
          H1("6. Constraints, assumptions and open points"),
          *B(["Everything (PKI, nginx, strongSwan, KDC, crypto tool, tests) is written by the group; only OpenSSL, nginx, strongSwan and pyca/cryptography are used as tools.",
              "The lab (docker-compose, image, node start-up scripts) was also written by the group, because no Starter Kit was provided. It follows the topology and addressing of the specification exactly and is kept in lab/.",
              "Lab-only names: *.g" + GID + ".scp.lab, resolved through /etc/hosts of each node (no real DNS). The DNS-spoof test (T5) edits the client's /etc/hosts.",
              "Staff clients use ECDSA P-256 certificates; three staff certificates are issued, staff03 is revoked.",
              "No private key, passphrase, PSK, .env or key-log file is ever committed; a secret scan runs before every tag."]),
          ]
    build(f"{OUT}/M1_Requirements.pdf", s, "M1 Requirements")


def topology():
    tp = f"{TMP}/topo.png"; topology_diagram(tp)
    s = cover("M1 - Topology and Trust Diagram", f"Six nodes, three networks, four trust boundaries (group number G = {G})")
    s += [IMG(tp, 17.2), P("Figure 1 - Lab topology with the group's own addresses and trust boundaries TB1-TB4.", "cap"),
          H1("1. Nodes and addresses"),
          T([["Node", "Address(es)", "Role", "Trust boundary"],
             ["gw-hq", f"{WAN}.10 (WAN), {HQ}.1 (HQ LAN)", "HQ VPN gateway, IP forwarding, firewall", "Between TB1 and TB2"],
             ["gw-branch", f"{WAN}.20 (WAN), {BR}.1 (Branch LAN)", "Branch VPN gateway", "Between TB1 and TB3"],
             ["web-hq", f"{HQ}.10", "nginx portal (TLS), CRL distribution point, Kerberos-protected service", "TB2"],
             ["kdc", f"{HQ}.20", "Key Distribution Center", "TB2"],
             ["client-br", f"{BR}.10", "Staff client (curl, crypto tool, Kerberos client)", "TB3"],
             ["attacker", f"{WAN}.66", "Authorised attacker (tests only); reaches Branch LAN via gw-branch, NO route to HQ LAN", "TB1 (hostile)"],
             ["Root CA / Issuing CA", "host (not a lab node)", "pki/ scripts; Root key offline", "TB4 (offline)"]],
            [2.6, 5.0, 6.8, 3.0]),
          H1("2. Names (lab DNS via /etc/hosts)"),
          T([["Name", "Address", "Used for"],
             [f"portal.{D}, pki.{D}", f"{HQ}.10", "HTTPS portal, CRL at http://pki." + D + "/crl/"],
             [f"kdc.{D}", f"{HQ}.20", "Kerberos-style KDC (TCP 8800)"],
             [f"gw-hq.{D} / gw-branch.{D}", f"{WAN}.10 / {WAN}.20", "IKE identities (SAN of the gateway certificates)"],
             [f"attacker.{D}", f"{WAN}.66", "Rogue TLS server, replay and scan source"]],
            [6.0, 4.4, 7.0]),
          H1("3. Ports and protocols"),
          T([["Service", "Port / protocol", "Between", "Protection"],
             ["HTTP (redirect + CRL)", "TCP 80", f"client -> web-hq", "Redirect only; CRL is public and signed"],
             ["HTTPS portal / mTLS /staff/", "TCP 443", "client -> web-hq", "TLS 1.2+/1.3, AEAD+PFS; client cert on /staff/"],
             ["KDC", "TCP 8800", "client -> kdc", "AEAD-protected messages, nonces, timestamps"],
             ["Kerberos service", "TCP 8801", "client -> web-hq", "Service ticket + authenticator, mutual auth"],
             ["IKEv2", "UDP 500 / 4500", "gw-branch <-> gw-hq", "Certificates, pinned identity"],
             ["ESP", "IP protocol 50", "gw-branch <-> gw-hq", "AES-GCM, PFS (ECDH)"]],
            [4.2, 3.2, 4.0, 6.0]),
          PageBreak(), H1("4. Data flows"),
          T([["Flow", "From -> To", "Crosses", "Today (M1)", "Target"],
             ["F1 portal access", "client-br -> web-hq", "TB3 -> TB1 -> TB2", "HTTP in clear (baseline)", "HTTPS inside ESP tunnel"],
             ["F2 staff area", "client-br -> web-hq:443", "TB3 -> TB1 -> TB2", "-", "mTLS inside ESP"],
             ["F3 Kerberos AS/TGS", "client-br -> kdc:8800", "TB3 -> TB1 -> TB2", "-", "AEAD messages inside ESP"],
             ["F4 Kerberos AP", "client-br -> web-hq:8801", "TB3 -> TB1 -> TB2", "-", "AEAD messages inside ESP"],
             ["F5 IKE / ESP", "gw-branch <-> gw-hq", "TB1", "-", "Only IKE and ESP visible"],
             ["F6 CRL fetch", "nginx / strongSwan -> web-hq:80", "TB2 (local)", "-", "Signed CRL, validity window"],
             ["F7 attack traffic", "attacker -> WAN / Branch LAN", "TB1", "Readable traffic visible", "Only IKE/ESP; scans see only UDP 500/4500"]],
            [3.0, 4.2, 3.4, 3.2, 3.6]),
          H1("5. Trust boundaries"),
          T([["ID", "Boundary", "What is trusted inside", "What crosses / control"],
             ["TB1", f"WAN 172.16.{G}.0/24", "Nothing - assumed fully observable and modifiable by an attacker", "Only IKE (UDP 500/4500) and ESP accepted by gateway firewall; everything else dropped"],
             ["TB2", f"HQ LAN {HQ}.0/24", "Hosts are managed by the group, but traffic is still readable inside the LAN", "Gateway firewall; TLS on the portal as defence in depth"],
             ["TB3", f"Branch LAN {BR}.0/24", "Staff client; LAN traffic is clear inside the LAN", "Only HQ<->Branch selectors enter the tunnel"],
             ["TB4", "Offline Root CA", "Only the administrator with the passphrase", "Signs the Issuing CA and root.crl only; key is never mounted in any service container"]],
            [1.2, 3.4, 5.6, 7.2]),
          H1("6. Trust rules"),
          *B([f"gw-hq accepts an IKE peer only if its certificate chains to the group's Root CA, is not revoked, and its identity equals gw-branch.{D} (and symmetrically). A valid staff certificate must be refused as a gateway identity.",
              "The portal accepts only TLS 1.2+ with AEAD/PFS suites; /staff/ accepts only a valid, unrevoked client certificate. A client certificate identifies a key holder, not a person.",
              "The KDC never sends a long-term key; it rejects any authenticator outside the freshness window. The final configuration contains no PSK.",
              "The attacker may capture, scan, spoof and replay only inside 172.16." + str(G) + ".0/24 and 10." + str(G) + ".0.0/16.",
              "CRL behaviour: a CRL protects only parties that download and check it. Group decision: nginx and strongSwan are fail-closed - an expired or missing CRL means client/gateway certificates are refused (see PKI design, section 6)."]),
          H1("7. Data classification of artefacts"),
          T([["Artefact", "Class", "Storage / handling"],
             ["Root CA key + passphrase", "SECRET", "Host only, encrypted key, mode 600, never in Git, never mounted into services"],
             ["Issuing CA key", "SECRET", "Host/pki node, encrypted, mode 600, never in Git"],
             ["Portal, gateway and staff private keys", "SECRET", "Mode 600 owned by the service user; pki/out/ is git-ignored"],
             ["Kerberos long-term keys (KDC database), PSK of weak variants", "SECRET", "Generated at build time; git-ignored; weak PSK only inside attacks/"],
             ["SSLKEYLOGFILE output", "SECRET", "Lab-only exercise; deleted afterwards; git-ignored"],
             ["Real .env, test passwords", "SECRET", "Not committed; .env.example only"],
             ["nginx / swanctl / firewall configuration, scripts", "INTERNAL", "In Git (no keys inside)"],
             ["Logs, pcaps (sanitised)", "INTERNAL", "evidence/ - checked for secrets before commit"],
             ["Certificates (public parts), CRLs, certs_inventory.md", "PUBLIC", "May be committed and published"]],
            [7.0, 2.2, 8.2])]
    build(f"{OUT}/M1_Topology_Trust.pdf", s, "M1 Topology and Trust")


def pki():
    pp = f"{TMP}/pki.png"; pki_diagram(pp)
    s = cover("M1 - PKI Design", "Two-tier PKI: offline Root CA, Issuing CA, certificate profiles and revocation plan")
    s += [IMG(pp, 16.5), P("Figure 1 - Hierarchy of the group's PKI.", "cap"),
          H1("1. Hierarchy and key handling"),
          *B([f"<b>Root CA</b> 'ABU SCP Root CA g{GID}': self-signed, ECDSA P-384, pathlen:1, 5 years. It signs only the Issuing CA certificate and root.crl. Its key is AES-256 encrypted (passphrase), mode 600, kept in pki/ca/root/ on the host, and is never mounted into any container service (offline).",
              f"<b>Issuing CA</b> 'ABU SCP Issuing CA g{GID}': ECDSA P-384, pathlen:0 (cannot create further CAs), 2 years; its certificate carries a CRL Distribution Point http://pki.{D}/crl/issuing.crl. Key encrypted, passphrase supplied from an untracked file/env variable at issue time.",
              "All keys are generated with openssl genpkey / ecparam inside the build scripts; no primitive is implemented by hand. Private keys are created with umask 077 and verified to be mode 600 by the build script.",
              "Serial numbers are random (openssl ca -rand_serial, 128-bit) and unique; index.txt is the revocation database."]),
          H1("2. Certificate profiles"),
          T([["Profile", "Subject / SAN", "Key", "Extensions (all critical where applicable)", "Validity"],
             ["root_ca", f"CN=ABU SCP Root CA g{GID}", "ECDSA P-384", "basicConstraints CA:TRUE, pathlen:1; keyUsage keyCertSign, cRLSign; SKI", "1825 d"],
             ["issuing_ca", f"CN=ABU SCP Issuing CA g{GID}", "ECDSA P-384", "CA:TRUE, pathlen:0; keyUsage keyCertSign, cRLSign; AKI/SKI; CRL DP", "730 d"],
             ["portal", f"DNS:portal.{D}, DNS:pki.{D}", "ECDSA P-256", "CA:FALSE; digitalSignature; EKU serverAuth; CRL DP; AKI/SKI", "398 d"],
             ["gateway (HQ)", f"DNS:gw-hq.{D}, IP:{WAN}.10", "ECDSA P-256", "CA:FALSE; digitalSignature; EKU serverAuth + clientAuth + ipsecIKE (1.3.6.1.5.5.7.3.17); CRL DP", "398 d"],
             ["gateway (Branch)", f"DNS:gw-branch.{D}, IP:{WAN}.20", "ECDSA P-256", "same as gateway (HQ)", "398 d"],
             ["staff", f"CN=staff01..03; email:staffNN@{D}", "ECDSA P-256", "CA:FALSE; digitalSignature; EKU clientAuth only; CRL DP", "365 d"],
             ["rogue CA (attacks only)", f"CN=ABU SCP Root CA g{GID} (imitation, same name)", "any", "Self-signed; lives only in attacks/; never in a trust store", "lab"]],
            [2.4, 4.4, 1.9, 6.7, 2.0]),
          P("<b>Gateway EKU justification:</b> each gateway is both IKE initiator and responder, so it needs serverAuth and clientAuth; ipsecIKE states the purpose explicitly. "
            "The staff profile has clientAuth only. The primary control that refuses a staff certificate as a gateway identity is identity pinning (remote id must equal the peer's gateway FQDN); EKU is defence in depth, and "
            "whether strongSwan 5.9 itself rejects the wrong EKU will be tested and documented in M3 (T8)."),
          H1("3. Naming and layout"),
          CODE("pki/ca/root/      (HOST ONLY)  private/root.key.enc  root.crt  index.txt  crlnumber\n"
               "pki/ca/issuing/                private/issuing.key.enc  issuing.crt  index.txt  crlnumber  newcerts/\n"
               "pki/out/<name>/   key.pem (600)  csr.pem  cert.pem  fullchain.pem        (git-ignored)\n"
               "pki/crl/          issuing.crl  root.crl      (public; served by nginx at /crl/)\n"
               "pki/openssl_root.cnf  pki/openssl_issuing.cnf  (profiles as extension sections)"),
          P("Scripts: <b>build_pki.sh</b> (full build from empty folder), <b>issue.sh &lt;profile&gt; &lt;name&gt;</b> (key + CSR + sign + inventory line), <b>revoke.sh &lt;name&gt;</b> (revoke + new CRL + publish). "
            "<b>certs_inventory.md</b> is regenerated on every issue/revoke."),
          H1("4. Planned certificate inventory"),
          T([["Name", "Profile", "Subject", "SAN", "Issuer", "Status"],
             ["portal", "portal", f"CN=portal.{D}", f"portal.{D}, pki.{D}", "Issuing CA", "valid"],
             ["gw-hq", "gateway", f"CN=gw-hq.{D}", f"gw-hq.{D}, {WAN}.10", "Issuing CA", "valid"],
             ["gw-branch", "gateway", f"CN=gw-branch.{D}", f"gw-branch.{D}, {WAN}.20", "Issuing CA", "valid"],
             ["staff01", "staff", "CN=staff01", f"staff01@{D}", "Issuing CA", "valid"],
             ["staff02", "staff", "CN=staff02", f"staff02@{D}", "Issuing CA", "valid"],
             ["staff03", "staff", "CN=staff03", f"staff03@{D}", "Issuing CA", "REVOKED (test T4)"]],
            [2.0, 1.8, 3.8, 5.0, 2.2, 2.6]),
          P("The final inventory (serial, subject, SAN, issuer, expiry) is generated by the scripts in M2."),
          H1("5. Revocation plan"),
          *B(["<b>Mechanism:</b> CRL (RFC 5280). Issuing CA publishes issuing.crl; the Root CA publishes root.crl (needed because nginx checks the CRL of every CA in the chain).",
              "<b>Validity window:</b> issuing.crl lasts 7 days (nextUpdate), regenerated immediately on every revoke.sh and refreshed daily by a scheduled run; root.crl lasts 365 days and is regenerated offline.",
              "<b>Distribution:</b> http://pki." + D + "/crl/issuing.crl served by nginx on web-hq (HTTP is acceptable: the CRL is public and signed). nginx reads a local copy (ssl_crl); strongSwan loads the CRL from the same location (x509crl directory / crl URI).",
              "<b>Test case:</b> staff03 is issued, used successfully, then revoked; after the CRL update /staff/ must refuse it (T4); a revoked gateway certificate must fail IKE auth (T8).",
              "<b>Rotation (M4):</b> portal certificate replaced and IKE SA rekeyed without service break."]),
          H1("6. CRL versus OCSP, and missing/expired CRL behaviour"),
          P("A CRL is a signed list downloaded periodically: simple, works offline in the lab, but revocation is only as fresh as the last download (up to 7 days here) and the list grows. "
            "OCSP gives per-certificate real-time status but needs an always-on responder and is usually deployed soft-fail by browsers, so an attacker who blocks the responder keeps using a revoked certificate. "
            "We choose CRL because the lab is closed and the trust model is fully under our control; OCSP is discussed in the final report."),
          P("<b>Missing or expired CRL - group decision (fail-closed):</b> nginx with ssl_crl and strongSwan with a configured CRL reject certificates whose issuer CRL is missing, unreadable or past nextUpdate. "
            "This favours security over availability (outage risk accepted and documented). A soft-fail alternative would let a revoked certificate work whenever the CRL cannot be fetched, which an attacker can trigger deliberately. "
            "The behaviour will be tested in M4 by letting a CRL expire in the lab."),
          H1("7. Risks specific to this PKI"),
          *B(["Root key compromise would invalidate the whole hierarchy -> offline, encrypted, not mounted, secret-scan before every tag.",
              "A rogue CA with the same subject name must not be trusted: trust stores contain only the group's Root certificate (compared by key/fingerprint, not by name).",
              "Using one certificate for several roles is forbidden: EKU and SAN are role-specific."])]
    build(f"{OUT}/M1_PKI_Design.pdf", s, "M1 PKI Design")


if __name__ == "__main__":
    requirements(); topology(); pki(); print("A done")
