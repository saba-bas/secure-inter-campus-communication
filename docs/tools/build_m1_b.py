"""M1 documents B: Protocol design, STRIDE workbook, Team plan."""
import os
from m1lib import *

OUT = os.path.join(os.path.dirname(__file__), "..", "M1")
TMP = "/tmp/m1img"; os.makedirs(TMP, exist_ok=True)


def protocol():
    tls, ike, krb = f"{TMP}/tls.png", f"{TMP}/ike.png", f"{TMP}/krb.png"
    seq_diagram(tls, ["client-br (curl)", f"web-hq (nginx) portal.{D}"], [
        ("client-br (curl)", f"web-hq (nginx) portal.{D}", "ClientHello: supported_versions 1.3/1.2, key_share(X25519), SNI, sig_algs"),
        (f"web-hq (nginx) portal.{D}", "client-br (curl)", "ServerHello: key_share(X25519)  [keys derived: all further messages encrypted]"),
        (f"web-hq (nginx) portal.{D}", "client-br (curl)", "{EncryptedExtensions}  {CertificateRequest}  (optional client auth)"),
        (f"web-hq (nginx) portal.{D}", "client-br (curl)", "{Certificate: portal + Issuing CA chain}  {CertificateVerify}  {Finished}"),
        ("note", "client verifies chain to Root CA, EKU serverAuth, SAN = portal name, validity, CRL"),
        ("client-br (curl)", f"web-hq (nginx) portal.{D}", "{Certificate: staffNN}  {CertificateVerify}  {Finished}   (only for /staff/)"),
        ("note", "server verifies client chain (depth 2) + CRL (issuing.crl, root.crl); logs subject as identity"),
        ("client-br (curl)", f"web-hq (nginx) portal.{D}", "[application data] GET /staff/  + Strict-Transport-Security on reply"),
        (f"web-hq (nginx) portal.{D}", "client-br (curl)", "200 OK (identity shown)  or  generic error page if cert missing/revoked"),
    ], title="TLS 1.3 handshake as used by the portal (mutual TLS on /staff/)", width=10, step=0.55)
    seq_diagram(ike, ["gw-branch (initiator)", "gw-hq (responder)"], [
        ("sep", "IKE_SA_INIT  (unencrypted)"),
        ("gw-branch (initiator)", "gw-hq (responder)", "HDR, SAi1 (aes256gcm16-prfsha384-ecp384), KEi, Ni"),
        ("gw-hq (responder)", "gw-branch (initiator)", "HDR, SAr1, KEr, Nr, [CERTREQ]"),
        ("note", "both sides compute SKEYSEED = prf(Ni|Nr, g^ir) -> SK_ei/er, SK_ai/ar, SK_d, SK_pi/pr"),
        ("sep", "IKE_AUTH  (encrypted with SK_e)"),
        ("gw-branch (initiator)", "gw-hq (responder)", f"HDR, SK{{IDi=gw-branch.{D}, CERT, CERTREQ, AUTH, SAi2, TSi, TSr}}"),
        ("note", "gw-hq: chain -> Root CA, CRL, IDi == pinned gw-branch FQDN, signature over init message"),
        ("gw-hq (responder)", "gw-branch (initiator)", f"HDR, SK{{IDr=gw-hq.{D}, CERT, AUTH, SAr2, TSi, TSr}}"),
        ("note", f"Traffic selectors: {BR[:-2]}.2.0/24 <=> {HQ}.0/24 ; CHILD_SA = ESP aes256gcm16 + ecp384 (PFS)"),
        ("sep", "Maintenance"),
        ("gw-branch (initiator)", "gw-hq (responder)", "CREATE_CHILD_SA: SK{SA, Ni, KEi, TSi, TSr}  (CHILD rekey with fresh DH = PFS)"),
        ("gw-hq (responder)", "gw-branch (initiator)", "INFORMATIONAL (DPD): SK{} - peer must answer or SA is torn down / restarted"),
    ], title="IKEv2 between the campus gateways (RFC 7296)", width=10, step=0.55)
    seq_diagram(krb, ["C (client-br)", "K (KDC)", "S (service web-hq)"], [
        ("sep", "AS exchange (login)"),
        ("C (client-br)", "K (KDC)", "1. C, TGS, N1, {T1}Kc"),
        ("K (KDC)", "C (client-br)", "2. {Kc,tgs, N1, TGS, Texp}Kc , TGT"),
        ("sep", "TGS exchange"),
        ("C (client-br)", "K (KDC)", "3. S, N2, TGT, {C, T2}Kc,tgs"),
        ("K (KDC)", "C (client-br)", "4. {Kc,s, N2, S, Texp}Kc,tgs , ST"),
        ("sep", "AP exchange (mutual authentication + key confirmation)"),
        ("C (client-br)", "S (service web-hq)", "5. ST, {C, T3, Nc}Kc,s"),
        ("S (service web-hq)", "C (client-br)", "6. {Nc, Ns, T3}Kc,s"),
        ("C (client-br)", "S (service web-hq)", "7. {Ns}Ksess  with Ksess = HKDF(Kc,s, Nc|Ns)"),
        ("S (service web-hq)", "C (client-br)", "8. {OK, Nc}Ksess"),
    ], title="Kerberos-style protocol (draft 1)", width=9.5, step=0.55)
    s = cover("M1 - Protocol Design", "TLS 1.3 handshake, IKEv2 exchanges and the group's Kerberos-style protocol (draft 1)")
    s += [H1("1. TLS 1.3 handshake as used (RFC 8446)"), IMG(tls, 17.2),
          P("Figure 1 - Handshake for portal access. nginx requests a client certificate with ssl_verify_client optional so that public pages work for anyone; /staff/ then enforces "
            "$ssl_client_verify = SUCCESS and otherwise returns one generic error page (SR05). TLS 1.2 stays enabled only with ECDHE+AEAD suites; TLS 1.3 is preferred.", "cap"),
          T([["Setting (design)", "Value", "Reason"],
             ["Protocols", "TLSv1.2, TLSv1.3", "SR04: minimum 1.2; 1.3 enabled; 1.0/1.1 refused (T6)"],
             ["TLS 1.2 suites", "ECDHE-ECDSA-AES256-GCM-SHA384, ECDHE-ECDSA-AES128-GCM-SHA256, ECDHE-ECDSA-CHACHA20-POLY1305", "AEAD + forward secrecy only (leaf keys are ECDSA)"],
             ["TLS 1.3 suites", "TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256, TLS_AES_128_GCM_SHA256", "all AEAD"],
             ["Groups", "X25519, secp256r1, secp384r1", "ECDHE only"],
             ["Chain / HSTS", "ssl_certificate = leaf + Issuing CA; HSTS max-age 31536000", "Full chain sent; FR04"],
             ["Client auth", "ssl_client_certificate = Root+Issuing; verify_depth 2; ssl_crl = issuing.crl + root.crl", "SR03/SR05; nginx checks the CRL of every CA in the chain"],
             ["Other", "ssl_session_tickets off; no OCSP stapling (CRL only)", "Keeps forward secrecy simple; matches revocation plan"]],
            [3.2, 8.2, 6.0]),
          PageBreak(), H1("2. IKEv2 (RFC 7296) between gw-branch and gw-hq"), IMG(ike, 17.2),
          P("Figure 2 - IKE_SA_INIT, IKE_AUTH and maintenance exchanges.", "cap"),
          T([["Parameter (draft for swanctl.conf)", "Value"],
             ["IKE proposal", "aes256gcm16-prfsha384-ecp384 (single explicit proposal; no fallback)"],
             ["ESP proposal", "aes256gcm16-ecp384 (ECDH in the CHILD_SA gives PFS)"],
             ["Authentication", f"local/remote auth = pubkey; certs from pki/out; local id = own FQDN; remote id pinned = peer FQDN (gw-branch.{D} / gw-hq.{D}); no PSK"],
             ["Traffic selectors", f"local_ts = {BR}.0/24 (branch) / {HQ}.0/24 (hq); remote_ts = the other LAN. Nothing else is tunnelled"],
             ["Lifetimes / DPD", "rekey_time IKE 4h, CHILD 1h (shortened for demos); dpd_delay = 10s; start_action = start; close_action = restart"],
             ["Revocation", "strongSwan loads issuing.crl and root.crl; strict CRL policy (fail-closed)"]],
            [5.0, 12.4]),
          PageBreak(), H1("3. Kerberos-style protocol - draft 1"),
          P("Goal: a staff client C authenticates to a service S through a KDC K, independently of the network layer. The design follows Kerberos V5 (RFC 4120) but is simplified and uses modern primitives. "
            "Notation: <b>{m}k</b> = AES-256-GCM(k, nonce, m, AAD) (authenticated encryption; AAD binds the message type and the names); N = nonce; T = timestamp; || = concatenation."),
          *B(["<b>Long-term keys:</b> Kc = scrypt(password, salt = realm||C) (derived on the client, never sent); Ks (service) and Ktgs (KDC internal) are random 256-bit keys. The KDC stores Kc, Ks, Ktgs.",
              "<b>Session keys:</b> Kc,tgs and Kc,s are fresh random keys from os.urandom generated by K; the final session key is Ksess = HKDF-SHA256(Kc,s, salt = Nc||Ns, info = 'scp-krb-session'||C||S).",
              "<b>Freshness:</b> every authenticator carries a timestamp T checked in a window of +/-60 s and a random nonce; K and S keep a replay cache of (principal, authenticator hash) for 120 s. Ticket lifetimes: TGT 10 min, service ticket 5 min.",
              "<b>Pre-authentication:</b> message 1 carries {T1}Kc, so an attacker cannot request material encrypted under Kc to guess the password offline. A wrong password, an unknown principal and a stale timestamp all get the same generic error (T11: 'without revealing which part failed').",
              "<b>Mutual authentication:</b> message 6 proves that S could open the ticket (it knows Ks); message 7 proves that C knows Kc,s and contributes Ns freshness; message 8 confirms Ksess to C. Both sides hold a fresh session key.",
              "<b>Encoding:</b> length-prefixed binary or JSON over TCP (8800 KDC, 8801 service); 12-byte random nonce per AEAD message, key never reused across directions without a fresh nonce (SR01)."]),
          IMG(krb, 15.2), P("Figure 3 - Message sequence of the draft protocol (full notation in auth_protocols/PROTOCOL.md from M3).", "cap"),
          T([["#", "Message (standard notation)", "AAD / checks"],
             ["1", "C -> K : C, TGS, N1, {T1}Kc", "AAD='AS-REQ'||C||TGS||N1 ; K checks |now-T1|<=60 s, replay cache"],
             ["2", "K -> C : {Kc,tgs, N1, TGS, Texp}Kc , TGT   with TGT = {Kc,tgs, C, Tstart, Texp}Ktgs", "C checks N1 matches; cannot read TGT"],
             ["3", "C -> K : S, N2, TGT, {C, T2}Kc,tgs", "K opens TGT, checks lifetime, authenticator, replay cache"],
             ["4", "K -> C : {Kc,s, N2, S, Texp}Kc,tgs , ST   with ST = {Kc,s, C, Tstart, Texp}Ks", "C checks N2"],
             ["5", "C -> S : ST, {C, T3, Nc}Kc,s", "S opens ST with Ks, checks C in ticket = C in authenticator, T3 window, replay cache"],
             ["6", "S -> C : {Nc, Ns, T3}Kc,s", "C checks Nc and T3 echoed: S is authentic"],
             ["7", "C -> S : {Ns}Ksess", "S checks Ns: C holds the session key"],
             ["8", "S -> C : {OK, Nc}Ksess", "Key confirmation both ways"]],
            [0.8, 9.6, 7.0]),
          H1("4. Weak variant and planned attack (SR10, T12a/T12b)"),
          *B(["<b>Weak variant</b> (attacks/replay/ only): the authenticator in message 5 is {C}Kc,s without T3 and Nc, message 6 returns only {OK}, and S keeps no replay cache. It therefore resembles the freshness flaw of Needham-Schroeder-style protocols.",
              "<b>Attack (T12a):</b> the attacker captures message 5 (readable on the WAN while no tunnel protects it) and re-sends it to S: S accepts and 'authenticates' the attacker as C. This will be documented with capture and logs.",
              "<b>Fix (T12b):</b> the fixed protocol above; the same replayed message is rejected by the timestamp window or the replay cache and the rejection is logged."]),
          H1("5. Open design points (to settle in M2/M3)"),
          *B([f"<b>Attacker reach for T12:</b> the attacker has no route to the HQ LAN. For T12a/T12b the replay will be sent through an attack-only exposure (documented DNAT on gw-hq, or a copy of the weak service on the WAN) kept inside attacks/replay/ and removed afterwards, so the final configuration is not weakened (FR12).",
              "<b>Where the attacker sees traffic:</b> a Docker bridge does not flood unicast, so captures are taken on the gateway WAN interface (as the specification prescribes) and, for attacker-side sniffing, by ARP spoofing inside the lab only.",
              "<b>T5 (DNS spoof):</b> client-br's /etc/hosts is changed to point portal." + D + f" to {WAN}.66; the attacker serves a rogue-CA certificate; curl without -k must fail with a verification error."])]
    build(f"{OUT}/M1_ProtocolDesign.pdf", s, "M1 Protocol Design")


THREATS = [
 # id, STRIDE, asset, threat, likelihood, impact, control, SR/FR, test, residual L, residual I
 ("TH-01", "Spoofing", "Portal name / TLS session (A4, A11)", f"Attacker spoofs DNS for portal.{D} and presents a certificate from a rogue CA with a copied name to read credentials/traffic", 3, 5, "Trust store holds only the group Root; full chain, SAN and EKU verified; no curl -k in tests; HSTS", "SR06, SR04", "T5", 1, 5),
 ("TH-02", "Spoofing", "Gateway identity (A6)", "Rogue or valid staff certificate presented as the peer gateway to establish the IPsec tunnel", 3, 5, "Pinned remote id, chain to Root, CRL, EKU, no PSK", "SR07, SR02", "T8", 1, 5),
 ("TH-03", "Information disclosure", "WAN traffic HQ<->Branch (A9)", "Passive eavesdropping on the WAN reads HTTP, credentials and Kerberos messages", 5, 4, "ESP tunnel (AES-GCM) between gateways; TLS inside", "SR12, FR06", "T7", 1, 4),
 ("TH-04", "Tampering", "Traffic and protocol messages (A8, A9)", "Active attacker modifies packets or Kerberos tickets/authenticators in transit", 3, 4, "ESP integrity (AEAD); AEAD with AAD in tickets; TLS AEAD", "SR01, SR09", "T2, T7", 1, 4),
 ("TH-05", "Elevation of privilege", "TLS/IKE negotiation (A4, A6)", "Downgrade to TLS 1.0/1.1, non-AEAD/non-PFS suite or weak IKE proposal", 3, 4, "TLS min 1.2 AEAD+PFS only; single explicit IKE/ESP proposals", "SR04, SR07, SR13", "T6, T8", 1, 4),
 ("TH-06", "Spoofing", "Kerberos authenticators (A8)", "Replay of a captured authenticator to impersonate a staff principal to the service", 4, 4, "Timestamp window +/-60 s, nonce, replay cache, mutual authentication", "SR09, SR10", "T12a, T12b", 1, 4),
 ("TH-07", "Information disclosure", "KDC long-term keys / passwords (A7)", "Offline guessing of the password from an AS reply or user enumeration through different error messages", 3, 4, "Pre-authentication {T1}Kc, scrypt-derived key, generic uniform error", "SR09", "T11", 2, 3),
 ("TH-08", "Elevation of privilege", "Root CA key (A1)", "Theft or online use of the Root CA key allows forging any certificate", 2, 5, "Offline, passphrase-protected, never mounted in services, pathlen constraints", "SR02, SR11", "T13", 1, 5),
 ("TH-09", "Information disclosure", "Repository (A10)", "Private keys, passphrases, PSKs, .env or key-log files committed to Git", 4, 5, ".gitignore, secret scan of history before each tag, only .env.example committed", "SR11", "T13", 1, 5),
 ("TH-10", "Spoofing", "Staff client certificate (A5)", "A revoked or stolen staff certificate is used on /staff/", 3, 4, "CRL checked by nginx; key mode 600; one key per person; short validity", "SR03, SR05", "T4", 2, 3),
 ("TH-11", "Denial of service", "CRL (A3)", "CRL expired or unreachable: either legitimate users are locked out or (soft-fail) revoked certs are accepted", 3, 3, "Fail-closed policy, 7-day window with daily refresh, expiry monitoring", "SR03", "T4 (expiry case)", 2, 2),
 ("TH-12", "Information disclosure", "LAN-to-LAN traffic (A9)", "If the IKE daemon stops, traffic is forwarded in clear text across the WAN", 3, 4, "Fail-closed gateway firewall (drop forward unless via IPsec policy)", "SR08", "T9", 1, 4),
 ("TH-13", "Repudiation", "Staff actions on /staff/ and KDC (A12)", "A staff member denies an action; no trustworthy record of who accessed what", 3, 3, "Client-certificate subject logged by nginx; KDC and service log principal and result", "SR05, SR14", "T3", 2, 2),
 ("TH-14", "Elevation of privilege", "Staff keys (A5)", "A member uses another member's key or certificate", 2, 3, "Individual certs, mode 600, contribution log, policy", "Spec 5", "T3", 2, 2),
 ("TH-15", "Denial of service", "Gateways and HQ LAN (A6)", "Port scan and probing find open services on the gateways or reach the HQ LAN", 4, 3, "Firewall: only UDP 500/4500 and ESP on WAN; no route for attacker into HQ LAN", "SR08", "T10", 1, 3),
 ("TH-16", "Tampering", "Final configuration (FR12)", "A weak test configuration (PSK, weak TLS, no-freshness protocol) leaks into the final system", 2, 3, "Weak variants kept only in attacks/; run_all.sh greps final configs", "FR12", "T6, T12a", 1, 3),
 ("TH-17", "Information disclosure", "Traffic inside LANs (A9)", "Clear LAN traffic can be read by a compromised host in the same LAN (VPN covers only GW<->GW)", 3, 3, "TLS on portal and AEAD Kerberos messages regardless of VPN (defence in depth); residual risk accepted", "Spec 4", "T3", 2, 3),
 ("TH-18", "Information disclosure", "SSLKEYLOGFILE output (A12)", "Key-log file from the SR12 exercise leaks session secrets", 2, 4, "Lab-only exercise, file deleted afterwards, git-ignored, scan", "SR12, SR11", "T13", 1, 4),
]
ASSETS = [("A1", "Root CA private key + passphrase", "SECRET"), ("A2", "Issuing CA private key", "SECRET"), ("A3", "CRL (issuing.crl, root.crl)", "PUBLIC"),
          ("A4", "Portal private key and TLS sessions", "SECRET"), ("A5", "Staff client keys/certificates", "SECRET"), ("A6", "Gateway keys, IKE/ESP SAs", "SECRET"),
          ("A7", "KDC long-term keys database", "SECRET"), ("A8", "Kerberos tickets and authenticators", "INTERNAL"), ("A9", "WAN and LAN traffic", "INTERNAL"),
          ("A10", "Git repository (configs, scripts)", "INTERNAL"), ("A11", "Name resolution (/etc/hosts in lab)", "INTERNAL"), ("A12", "Logs, captures, key-log file", "INTERNAL/SECRET")]


def stride_xlsx():
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.formatting.rule import CellIsRule
    wb = Workbook(); ws = wb.active; ws.title = "Threats"
    F = "Arial"; thin = Side(style="thin", color="999999"); bd = Border(left=thin, right=thin, top=thin, bottom=thin)
    ws["A1"] = f"STRIDE threat model - Group {GID} - Secure Inter-Campus Communication Network (M1)"; ws["A1"].font = Font(name=F, bold=True, size=13)
    ws["A2"] = "Likelihood (L) and Impact (I) scored 1-5 by the group (blue = input). Score = L x I; rating by formula: >=15 High, 8-14 Medium, <8 Low. Residual = expected after the listed control is implemented."
    ws["A2"].font = Font(name=F, italic=True, size=9)
    hdr = ["ID", "STRIDE", "Asset (see Assets sheet)", "Threat", "L", "I", "Score", "Rating", "Control (planned)", "Requirement", "Test", "Residual L", "Residual I", "Residual score", "Residual rating"]
    for c, h in enumerate(hdr, 1):
        x = ws.cell(row=4, column=c, value=h); x.font = Font(name=F, bold=True, color="FFFFFF", size=10); x.fill = PatternFill("solid", fgColor="14304A")
        x.alignment = Alignment(wrap_text=True, vertical="center"); x.border = bd
    for r, t in enumerate(THREATS, 5):
        vals = [t[0], t[1], t[2], t[3], t[4], t[5], f"=E{r}*F{r}", f'=IF(G{r}>=15,"High",IF(G{r}>=8,"Medium","Low"))', t[6], t[7], t[8], t[9], t[10], f"=L{r}*M{r}", f'=IF(N{r}>=15,"High",IF(N{r}>=8,"Medium","Low"))']
        for c, v in enumerate(vals, 1):
            x = ws.cell(row=r, column=c, value=v); x.font = Font(name=F, size=9, color="0000FF" if c in (5, 6, 12, 13) else "000000")
            x.alignment = Alignment(wrap_text=True, vertical="top"); x.border = bd
    last = 4 + len(THREATS)
    for col, w in zip("ABCDEFGHIJKLMNO", [7, 17, 26, 52, 4, 4, 7, 9, 48, 14, 11, 9, 9, 10, 10]):
        ws.column_dimensions[col].width = w
    for rng in (f"H5:H{last}", f"O5:O{last}"):
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"High"'], fill=PatternFill("solid", bgColor="F4B6B6")))
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Medium"'], fill=PatternFill("solid", bgColor="FCE4A8")))
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"Low"'], fill=PatternFill("solid", bgColor="CDEBC5")))
    ws.freeze_panes = "E5"
    s = last + 2
    ws.cell(row=s, column=3, value="Summary").font = Font(name=F, bold=True)
    for i, (lab, f) in enumerate([("Number of threats", f"=COUNTA(A5:A{last})"), ("High (inherent)", f'=COUNTIF(H5:H{last},"High")'),
                                  ("Medium (inherent)", f'=COUNTIF(H5:H{last},"Medium")'), ("High (residual)", f'=COUNTIF(O5:O{last},"High")'),
                                  ("Average inherent score", f"=AVERAGE(G5:G{last})"), ("Average residual score", f"=AVERAGE(N5:N{last})")], 1):
        ws.cell(row=s + i, column=3, value=lab).font = Font(name=F, size=9); c = ws.cell(row=s + i, column=4, value=f); c.font = Font(name=F, size=9); c.alignment = Alignment(horizontal="left")
        if "Average" in lab: c.number_format = "0.0"
    a = wb.create_sheet("Assets")
    for c, h in enumerate(["ID", "Asset", "Classification"], 1):
        x = a.cell(row=1, column=c, value=h); x.font = Font(name=F, bold=True, color="FFFFFF"); x.fill = PatternFill("solid", fgColor="14304A")
    for r, row in enumerate(ASSETS, 2):
        for c, v in enumerate(row, 1): a.cell(row=r, column=c, value=v).font = Font(name=F, size=10)
    a.column_dimensions["A"].width = 6; a.column_dimensions["B"].width = 44; a.column_dimensions["C"].width = 18
    lg = wb.create_sheet("Legend")
    rows = [("Scale", "1 = very low ... 5 = very high"), ("Likelihood", "How likely the attack is from the WAN attacker node or a mistake inside the lab"), ("Impact", "Damage to confidentiality, integrity, availability or trust of the PKI"),
            ("Rating", "High >= 15; Medium 8-14; Low < 8"), ("Scope", "Threats are tied to this lab's assets and the milestones that test them (T1-T13); scores are the group's judgement and are discussed in the report")]
    for r, (k, v) in enumerate(rows, 1):
        lg.cell(row=r, column=1, value=k).font = Font(name=F, bold=True); lg.cell(row=r, column=2, value=v).font = Font(name=F)
    lg.column_dimensions["A"].width = 14; lg.column_dimensions["B"].width = 110
    wb.save(f"{OUT}/M1_STRIDE.xlsx")


def teamplan():
    s = cover("M1 - Team Work Plan", "Responsibilities, schedule, Git workflow and release plan")
    m1, m2, m3 = MEMBERS
    s += [H1("1. Team and primary responsibilities"),
          P("Every member owns one stream but must understand and be able to explain all of them (the Week-14 discussion asks each member about any part). Every merge request is reviewed by another member."),
          T([["Member", "Primary stream (lead)", "Secondary (reviewer / support)"],
             [m1, "PKI scripts (build_pki, issue, revoke), certificate profiles, nginx TLS + mutual TLS, TLS assessment (testssl), MITM/downgrade-TLS attacks", "IKE certificates and CRL in strongSwan; report: PKI and TLS chapters"],
             [m2, "Docker lab, baseline/WAN captures, strongSwan IKEv2, gateway firewall, fail-closed proof, T7-T10, tests/run_all.sh", "Crypto tool test vectors; README and rebuild verification"],
             [m3, "Crypto tool (scpcrypt.py + known-answer and tamper tests), KDC/client/service, weak variant + replay attack/fix (T11-T12), secret scan (T13)", "STRIDE upkeep; report: authentication protocol chapter"]],
            [3.2, 9.0, 5.2]),
          P("Roles may be renamed to the real names/IDs in docs/tools (environment variables M1_NAME, M2_NAME, M3_NAME) and the PDFs regenerated."),
          H1("2. Deliverable ownership for M1"),
          T([["Deliverable", "Author", "Reviewer", "Due"],
             ["M1_Requirements.pdf", m2, m1, "03/11"], ["M1_Topology_Trust.pdf", m2, m3, "03/11"], ["M1_PKI_Design.pdf", m1, m2, "04/11"],
             ["M1_ProtocolDesign.pdf (TLS, IKEv2, Kerberos draft)", f"{m1} (TLS), {m2} (IKEv2), {m3} (Kerberos)", "each other", "04/11"],
             ["M1_STRIDE.xlsx", m3, m1, "04/11"], ["Baseline: lab up + evidence/pcaps/M1_baseline_wan.pcap", m2, m3, "02/11"],
             ["Repository, README, .gitignore, tag M1", m3, m2, "05/11"]],
            [6.6, 5.0, 3.6, 2.2]),
          H1("3. Schedule"),
          T([["Period", "Milestone", "Main tasks", "Output"],
             ["29/10 - 06/11", "M1 (4 marks)", "Lab up, baseline capture, six design documents, STRIDE, repository with tag M1", "Tag M1"],
             ["07/11 - 20/11", "M2 (6 marks)", "week 1: openssl configs + build_pki.sh, issue/revoke, scpcrypt.py with RFC 4231/8032 vectors; week 2: nginx TLS/mTLS, CRL, functional tests, README", "Tag M2"],
             ["21/11 - 11/12", "M3 (11 marks)", "Midterm exam week 29/11-05/12: no milestone due, reduced load. Before: gateway certs + swanctl + firewall; after: KDC/client/service, weak variant, attacks (MITM, downgrade, replay), tests T1-T10, before/after captures", "Tag M3"],
             ["12/12 - 25/12", "M4 (9 marks)", "Revocation + key rotation demo, testssl before/after, T1-T13 via run_all.sh, final report (12-20 pages), secret scan, rebuild on clean machine, tag FINAL", "Tag FINAL"],
             ["10/01 - 14/01/2027", "Week 14", "Group discussion, 10 min live tests + 10 min individual questions, on FINAL", "-"]],
            [2.6, 2.4, 9.6, 2.8]),
          P("Internal buffers: finish each milestone 24 hours before the deadline for the secret scan and a fresh clone test. Late submission costs 10% per day, so no milestone is planned to use late days."),
          H1("4. Git workflow and release plan"),
          *B(["Private GitHub repository created by one member; the other two are collaborators. Folder structure as in the specification (lab/, pki/, crypto/, tls/, ipsec/, auth_protocols/, attacks/, tests/, docs/, evidence/, contribution/).",
              "Branches: <b>main</b> (always working), <b>feature/&lt;area&gt;-&lt;name&gt;</b> per task, merged by pull request after review by another member. Commit messages: 'area: what' (e.g. 'pki: add issuing CA profile').",
              "Tags: <b>M1</b> (06/11), <b>M2</b> (20/11), <b>M3</b> (11/12), <b>FINAL</b> (25/12, before the end of the day). Annotated tags: git tag -a M1 -m 'Milestone 1'; git push origin M1.",
              "Before every tag: run the secret scan over the full history (gitleaks, or the grep patterns in tests/secret_scan.sh) and verify git status shows no .env, *.key, *.p12, *.pcap with credentials, key-log files.",
              "Each member's contribution is visible in commits and summarised in contribution/individual_contributions.pdf (M4); no member commits another's work under their name."]),
          H1("5. Definition of done (every task)"),
          *B(["Script or configuration committed and runs on the lab from the README steps; a test (or documented command + output) is linked to its T-number.",
              "Evidence stored in evidence/ with the command, capture filter or packet numbers - never screenshots alone.",
              "Reviewed by another member; no secret in the diff."]),
          H1("6. Project risks"),
          T([["Risk", "Impact", "Mitigation"],
             ["strongSwan/Docker issues (capabilities, charon without systemd)", "Delays M3", "Test charon start-up and a PSK-free minimal tunnel in the first week of M2; keep notes in docs/M3"],
             ["Midterm exam week reduces working time", "M3 slips", "Finish PKI and gateway certificates before 29/11; plan M3 core before the exam"],
             ["One member is the only one who understands a component", "Individual discussion marks", "Cross-review, rotate explaining each component in team meetings"],
             ["Secrets committed by accident", "Mark loss, SR11", ".gitignore, scan before each tag, rotate the lab keys if it happens"],
             ["Copying another group's numbers", "Treated as copied work", f"All names/addresses derive from G={G} and GROUP_ID={GID} only"]],
            [6.2, 3.2, 8.0]),
          H1("7. Communication"),
          P("Two short team meetings per week (decisions written in docs/ as short notes), a shared task list in GitHub Issues, and a 30-minute weekly cross-explanation session in which each member presents one component to the others.")]
    build(f"{OUT}/M1_TeamPlan.pdf", s, "M1 Team Plan")


if __name__ == "__main__":
    protocol(); stride_xlsx(); teamplan(); print("B done")
