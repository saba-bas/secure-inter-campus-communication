"""Shared helpers for the M1 document generator (ReportLab + matplotlib). ASCII text only."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, KeepTogether)

# ---------------- group parameters (edit .env / env vars, then re-run build_m1.py) ----------------
G = int(os.environ.get("GROUP_NUM", "7"))
GID = os.environ.get("GROUP_ID", f"{G:02d}")
D = f"g{GID}.scp.lab"
WAN, HQ, BR = f"172.16.{G}", f"10.{G}.1", f"10.{G}.2"
MEMBERS = [n for n in (os.environ.get("M1_NAME", "Member 1 (name / ID)"),
                       os.environ.get("M2_NAME", "Member 2 (name / ID)"),
                       os.environ.get("M3_NAME", "Member 3 (name / ID)")) if n and n != "-"]
COURSE = "Secure Communication Protocols (1305301) - First Semester 2026/2027"
NAVY = colors.HexColor("#14304a")
LIGHT = colors.HexColor("#e6eef4")

# ---------------- styles ----------------
S = {
    "title": ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=NAVY, spaceAfter=6),
    "sub": ParagraphStyle("s", fontName="Helvetica", fontSize=11, leading=15, textColor=colors.HexColor("#444444")),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=NAVY, spaceBefore=12, spaceAfter=5),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=8, spaceAfter=3),
    "p": ParagraphStyle("p", fontName="Helvetica", fontSize=9.6, leading=13.2, spaceAfter=4),
    "b": ParagraphStyle("b", fontName="Helvetica", fontSize=9.6, leading=13, leftIndent=14, bulletIndent=3, spaceAfter=1.5),
    "c": ParagraphStyle("c", fontName="Helvetica", fontSize=8.2, leading=10.2),
    "ch": ParagraphStyle("ch", fontName="Helvetica-Bold", fontSize=8.2, leading=10.2, textColor=colors.white),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=8.2, leading=10.5, leftIndent=8, backColor=colors.HexColor("#f3f3f3"), spaceAfter=4, borderPadding=3),
    "cap": ParagraphStyle("cap", fontName="Helvetica-Oblique", fontSize=8.2, leading=10, textColor=colors.HexColor("#555555"), spaceAfter=6),
}


def P(t, st="p"): return Paragraph(t, S[st])
def H1(t): return Paragraph(t, S["h1"])
def H2(t): return Paragraph(t, S["h2"])
def B(items): return [Paragraph(i, S["b"], bulletText="-") for i in items]
def CODE(t): return Paragraph(t.replace("\n", "<br/>").replace(" ", "&nbsp;"), S["code"])


def T(rows, widths, hdr=True, zebra=True):
    """Table with wrapped cells. widths in cm (sum should be <= 17.4)."""
    data = []
    for i, r in enumerate(rows):
        data.append([Paragraph(str(c), S["ch"] if (hdr and i == 0) else S["c"]) for c in r])
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if hdr else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa9b5")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if hdr:
        st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra:
        for i in range(1 if hdr else 0, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(st))
    return t


def IMG(path, width_cm=17.0):
    from PIL import Image as PI
    w, h = PI.open(path).size
    return Image(path, width=width_cm * cm, height=width_cm * cm * h / w)


def build(path, story, title):
    def deco(c, doc):
        c.saveState()
        c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#666666"))
        c.drawString(1.8 * cm, 1.1 * cm, f"{title} | Group {GID} | {COURSE} | M1")
        c.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, f"Page {doc.page}")
        c.setStrokeColor(NAVY); c.setLineWidth(1.2); c.line(1.8 * cm, A4[1] - 1.3 * cm, A4[0] - 1.8 * cm, A4[1] - 1.3 * cm)
        c.restoreState()
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                            topMargin=1.8 * cm, bottomMargin=1.7 * cm, title=title, author=f"Group {GID}")
    doc.build(story, onFirstPage=deco, onLaterPages=deco)


def cover(title, subtitle):
    return [Spacer(1, 0.3 * cm), P(title, "title"), P(subtitle, "sub"),
            P(f"Group {GID} (G={G}) | Team: " + "; ".join(MEMBERS), "sub"),
            P("Milestone M1 - due Friday 06/11/2026 | Repository tag: M1", "sub"), Spacer(1, 0.3 * cm)]


# ---------------- diagrams ----------------
def _box(ax, x, y, w, h, text, fc="#ffffff", ec="#14304a", fs=8, lw=1.2, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")


def seq_diagram(path, actors, msgs, title=None, width=9.0, step=0.5):
    """msgs: ('A','B','label') arrow; ('A','A','label') self; ('note','text') spanning note; ('sep','text') divider."""
    n = len(actors); idx = {a: i for i, a in enumerate(actors)}
    h = 1.2 + step * len(msgs)
    fig, ax = plt.subplots(figsize=(width, h)); ax.set_xlim(-0.5, n - 0.5); ax.set_ylim(-h + 1.0, 0.7); ax.axis("off")
    if title: ax.set_title(title, fontsize=10, fontweight="bold", color="#14304a")
    for a, i in idx.items():
        _box(ax, i - 0.33, 0.15, 0.66, 0.4, a, fc="#e6eef4", fs=8, bold=True)
        ax.plot([i, i], [0.15, -h + 1.0], color="#8899a6", lw=0.8, ls="--")
    y = -0.1
    for m in msgs:
        y -= step
        if m[0] == "sep":
            ax.plot([-0.5, n - 0.5], [y, y], color="#bbbbbb", lw=0.6)
            ax.text(-0.45, y + 0.04, m[1], fontsize=7.5, fontweight="bold", color="#14304a", va="bottom")
        elif m[0] == "note":
            ax.text((n - 1) / 2, y, m[1], ha="center", va="center", fontsize=7, bbox=dict(fc="#fff8dc", ec="#c9b458", boxstyle="round,pad=0.25"))
        else:
            a, b, lab = m[:3]; i, j = idx[a], idx[b]
            if i == j:
                ax.annotate("", xy=(i, y - 0.12), xytext=(i, y + 0.12), arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-1.6", color="#14304a"))
                ax.text(i + 0.12, y, lab, fontsize=7, va="center")
            else:
                ax.annotate("", xy=(j, y), xytext=(i, y), arrowprops=dict(arrowstyle="->", color="#14304a", lw=1.1))
                ax.text((i + j) / 2, y + 0.04, lab, ha="center", va="bottom", fontsize=7)
    fig.savefig(path, dpi=170, bbox_inches="tight"); plt.close(fig)


def topology_diagram(path):
    fig, ax = plt.subplots(figsize=(10, 6.2)); ax.set_xlim(0, 10); ax.set_ylim(0, 6.2); ax.axis("off")
    def zone(x, y, w, h, label, ec, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.1", fc=fc, ec=ec, lw=1.8, ls="--"))
        ax.text(x + 0.1, y + h - 0.12, label, fontsize=8.5, fontweight="bold", color=ec, va="top")
    zone(0.1, 1.5, 2.3, 4.2, f"TB3  Branch LAN\n10.{G}.2.0/24", "#2e7d32", "#f3faf3")
    zone(2.7, 1.5, 4.6, 4.2, f"TB1  WAN (UNTRUSTED)\n172.16.{G}.0/24", "#c62828", "#fff5f5")
    zone(7.6, 1.5, 2.3, 4.2, f"TB2  HQ LAN\n10.{G}.1.0/24", "#1565c0", "#f3f8ff")
    _box(ax, 0.3, 3.3, 1.9, 0.8, f"client-br\n10.{G}.2.10\nstaff client", fs=8)
    _box(ax, 3.0, 3.3, 1.7, 0.8, f"gw-branch\nWAN 172.16.{G}.20\nLAN 10.{G}.2.1", fc="#e8f5e9", fs=7.5)
    _box(ax, 5.3, 3.3, 1.7, 0.8, f"gw-hq\nWAN 172.16.{G}.10\nLAN 10.{G}.1.1", fc="#e3f2fd", fs=7.5)
    _box(ax, 7.8, 3.9, 1.9, 0.9, f"web-hq 10.{G}.1.10\nportal(443) CRL(80)\nKerberos svc(8801)", fs=7.5)
    _box(ax, 7.8, 2.5, 1.9, 0.8, f"kdc 10.{G}.1.20\nKDC (TCP 8800)", fs=8)
    _box(ax, 4.0, 1.75, 2.0, 0.8, f"attacker\n172.16.{G}.66\n(lab tests only)", fc="#ffebee", ec="#c62828", fs=8)
    ax.annotate("", xy=(3.0, 3.7), xytext=(2.2, 3.7), arrowprops=dict(arrowstyle="->", color="#555"))
    ax.annotate("", xy=(7.8, 4.2), xytext=(7.0, 3.75), arrowprops=dict(arrowstyle="->", color="#555"))
    ax.annotate("", xy=(7.8, 2.9), xytext=(7.0, 3.5), arrowprops=dict(arrowstyle="->", color="#555"))
    ax.annotate("", xy=(5.3, 3.7), xytext=(4.7, 3.7), arrowprops=dict(arrowstyle="<->", color="#14304a", lw=2.4))
    ax.text(5.0, 4.25, "IKEv2 / ESP tunnel\n(after M3)", ha="center", fontsize=8, fontweight="bold", color="#14304a")
    ax.annotate("", xy=(5.0, 3.3), xytext=(5.0, 2.55), arrowprops=dict(arrowstyle="->", color="#c62828", ls="--"))
    ax.text(5.1, 2.95, "observes WAN\n(clear text until M3)", fontsize=6.5, color="#c62828")
    ax.annotate("", xy=(3.4, 3.3), xytext=(4.2, 2.55), arrowprops=dict(arrowstyle="->", color="#c62828", ls="--"))
    ax.text(2.8, 1.65, "reaches Branch LAN via\ngw-branch; NO route\ninto HQ LAN", fontsize=6.5, color="#c62828")
    _box(ax, 0.1, 0.1, 3.3, 1.0, f"TB4  OFFLINE Root CA (host only)\n'ABU SCP Root CA g{GID}'\npassphrase-protected, never mounted\ninto a service container", fc="#fff8e1", ec="#ef6c00", fs=7.5, lw=1.8)
    _box(ax, 3.7, 0.1, 3.0, 1.0, f"Issuing CA (pki scripts, host/pki node)\n'ABU SCP Issuing CA g{GID}', pathlen 0\nCRL: http://pki.{D}/crl/", fc="#fffdf0", ec="#ef6c00", fs=7.5)
    ax.annotate("", xy=(3.7, 0.6), xytext=(3.4, 0.6), arrowprops=dict(arrowstyle="->", color="#ef6c00", lw=1.6))
    ax.text(3.55, 0.78, "signs", fontsize=6.5, ha="center", color="#ef6c00")
    _box(ax, 7.0, 0.1, 2.9, 1.0, "Defence in depth:\nVPN protects only GW<->GW.\nLAN traffic is still clear -> TLS", fc="#f5f5f5", ec="#777", fs=7.5)
    fig.savefig(path, dpi=170, bbox_inches="tight"); plt.close(fig)


def pki_diagram(path):
    fig, ax = plt.subplots(figsize=(10, 5.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 5.6); ax.axis("off")
    _box(ax, 3.3, 4.7, 3.4, 0.8, f"Root CA  'ABU SCP Root CA g{GID}'\nECDSA P-384 | pathlen:1 | 5 y | OFFLINE", fc="#fff8e1", ec="#ef6c00", fs=8, lw=2)
    _box(ax, 3.3, 3.3, 3.4, 0.8, f"Issuing CA  'ABU SCP Issuing CA g{GID}'\nECDSA P-384 | pathlen:0 | 2 y | CRL DP", fc="#fffdf0", ec="#ef6c00", fs=8, lw=2)
    leaves = [("Portal\nportal / pki\nP-256, 398 d\nserverAuth", 0.1), ("gw-hq\nP-256/384, 398 d\nserverAuth+\nclientAuth+ipsecIKE", 2.1),
              ("gw-branch\nP-256/384, 398 d\nsame as gw-hq", 4.1), ("staff01..03\nP-256, 1 y\nclientAuth\n(staff03 REVOKED)", 6.1)]
    for t, x in leaves:
        _box(ax, x, 1.5, 1.85, 1.2, t, fc="#e6eef4", fs=7)
        ax.annotate("", xy=(x + 0.92, 2.7), xytext=(5.0, 3.3), arrowprops=dict(arrowstyle="->", color="#14304a"))
    ax.annotate("", xy=(5.0, 4.1), xytext=(5.0, 4.7), arrowprops=dict(arrowstyle="->", color="#14304a", lw=2))
    _box(ax, 8.3, 3.3, 1.6, 0.8, "issuing.crl\nnextUpdate 7 d\nHTTP, public", fc="#e8f5e9", ec="#2e7d32", fs=7)
    ax.annotate("", xy=(8.3, 3.7), xytext=(6.7, 3.7), arrowprops=dict(arrowstyle="->", color="#2e7d32"))
    _box(ax, 8.3, 4.7, 1.6, 0.8, "root.crl\nnextUpdate 365 d", fc="#e8f5e9", ec="#2e7d32", fs=7)
    ax.annotate("", xy=(8.3, 5.1), xytext=(6.7, 5.1), arrowprops=dict(arrowstyle="->", color="#2e7d32"))
    _box(ax, 8.2, 1.5, 1.7, 1.2, "Rogue CA\n(attacks/ only)\nself-signed\nimitation name", fc="#ffebee", ec="#c62828", fs=7)
    ax.text(5.0, 0.8, "All end-entity certs: random serial, SAN mandatory, CA:FALSE, key file mode 600", ha="center", fontsize=8, style="italic")
    fig.savefig(path, dpi=170, bbox_inches="tight"); plt.close(fig)


def usecase_diagram(path):
    fig, ax = plt.subplots(figsize=(11, 6.0)); ax.set_xlim(0, 11); ax.set_ylim(0, 6); ax.axis("off")
    ax.add_patch(FancyBboxPatch((2.6, 0.1), 6.6, 5.8, boxstyle="round,pad=0.02", fc="#fafcfd", ec="#14304a", lw=1.2))
    ax.text(5.9, 5.7, "Secure Inter-Campus Communication Network", ha="center", fontsize=9, fontweight="bold", color="#14304a")
    ucs = {"UC1 View public portal": (4.0, 5.0), "UC2 Open /staff/ (mTLS)": (4.0, 4.1), "UC3 Kerberos login + service": (4.0, 3.2),
           "UC4 Use crypto tool": (4.0, 2.3), "UC5 Reach HQ over VPN": (4.0, 1.4),
           "UC6 Build PKI": (7.6, 5.0), "UC7 Issue certificate": (7.6, 4.1), "UC8 Revoke + publish CRL": (7.6, 3.2),
           "UC9 Run attacks + tests": (7.6, 2.3), "UC10 Rebuild from scratch": (7.6, 1.4)}
    for t, (x, y) in ucs.items():
        ax.add_patch(Ellipse((x, y), 2.6, 0.7, fc="#e6eef4", ec="#14304a")); ax.text(x, y, t, ha="center", va="center", fontsize=7)
    actors = {"Public\nvisitor": (1.0, 4.9, ["UC1"]), "Staff\nmember": (1.0, 3.0, ["UC1", "UC2", "UC3", "UC4", "UC5"]),
              "Administrator": (10.2, 3.0, ["UC6", "UC7", "UC8", "UC9", "UC10"])}
    pos = {k.split()[0]: v for k, v in ucs.items()}
    for a, (x, y, lst) in actors.items():
        ax.plot([x], [y + 0.45], "o", ms=9, color="#14304a"); ax.plot([x, x], [y + 0.35, y - 0.1], color="#14304a")
        ax.plot([x - 0.3, x + 0.3], [y + 0.2, y + 0.2], color="#14304a"); ax.text(x, y - 0.45, a, ha="center", fontsize=8, fontweight="bold")
        for u in lst:
            ux, uy = pos[u]; ax.plot([x + (0.3 if ux < 5 else -0.3), ux - 1.3 if ux < 5 else ux + 1.3], [y + 0.2, uy], color="#9aa9b5", lw=0.7)
    ax.text(5.9, 0.25, "Adversary (WAN attacker) is not an actor of the system: it is modelled in the STRIDE sheet and in attacks/.", ha="center", fontsize=7, style="italic")
    fig.savefig(path, dpi=170, bbox_inches="tight"); plt.close(fig)
