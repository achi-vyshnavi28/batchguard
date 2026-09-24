"""Generate low-fidelity wireframes as SVG (drag the files into a Figma file: they become editable layers).

    python design/make_wireframes.py
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent / "wireframes"
W, H = 1280, 800
INK, MUTED, LINE, FILL, ACCENT, BAD, OK = "#1c2330", "#6b7280", "#d0d5dd", "#f2f4f7", "#2f5bd3", "#b42318", "#1a7f4b"


class Frame:
    def __init__(self, title: str, height: int = H):
        self.h = height
        self.parts = [f'<rect width="{W}" height="{height}" fill="#ffffff"/>',
                      f'<rect width="{W}" height="56" fill="#101828"/>',
                      f'<text x="24" y="35" fill="#fff" font-size="18" font-weight="700" font-family="Inter, Arial">BatchGuard</text>',
                      *[f'<text x="{x}" y="35" fill="#cfd7ea" font-size="15" font-family="Inter, Arial">{t}</text>'
                        for x, t in ((150, "Batches"), (240, "Audit trail"), (350, "Cleaning log"))],
                      f'<text x="{W - 24}" y="35" fill="#cfd7ea" font-size="14" text-anchor="end" font-family="Inter, Arial">Kiran QA · qa · Log out</text>']
        self.title = title

    def text(self, x, y, s, size=14, color=INK, weight=400, anchor="start"):
        self.parts.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" '
                          f'text-anchor="{anchor}" font-family="Inter, Arial">{escape(s)}</text>')

    def box(self, x, y, w, h, fill=FILL, stroke=LINE, r=8, dash=False):
        d = ' stroke-dasharray="6 4"' if dash else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"{d}/>')

    def input(self, x, y, w, label, placeholder=""):
        self.text(x, y - 6, label, 13, MUTED)
        self.box(x, y, w, 36, "#fff")
        self.text(x + 10, y + 23, placeholder, 13, "#98a2b3")

    def button(self, x, y, label, primary=True, w=None):
        w = w or 16 + 8 * len(label)
        self.box(x, y, w, 36, ACCENT if primary else "#fff", ACCENT, 6)
        self.text(x + w / 2, y + 23, label, 14, "#fff" if primary else ACCENT, 600, "middle")

    def pill(self, x, y, label, color):
        w = 14 + 7 * len(label)
        self.box(x, y, w, 22, "#fff", color, 11)
        self.text(x + w / 2, y + 15, label, 12, color, 600, "middle")

    def note(self, x, y, lines):
        self.box(x, y, 300, 26 + 20 * len(lines), "#fffbe6", "#f5c542", 6)
        for i, line in enumerate(lines):
            self.text(x + 12, y + 22 + 20 * i, line, 12, "#7a5c00")

    def svg(self):
        head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{self.h}" viewBox="0 0 {W} {self.h}">'
        return head + f"<title>{escape(self.title)}</title>" + "".join(self.parts) + "</svg>"


def table(f: Frame, x, y, cols, rows, widths):
    f.box(x, y, sum(widths), 40 + 48 * len(rows), "#fff")
    cx = x
    for c, w in zip(cols, widths):
        f.text(cx + 12, y + 26, c, 13, MUTED, 600)
        cx += w
    for i, row in enumerate(rows):
        ry = y + 40 + 48 * i
        f.parts.append(f'<line x1="{x}" y1="{ry}" x2="{x + sum(widths)}" y2="{ry}" stroke="{LINE}"/>')
        cx = x
        for cell, w in zip(row, widths):
            color = BAD if "out of spec" in cell else INK
            f.text(cx + 12, ry + 29, cell, 13, color)
            cx += w


def login():
    f = Frame("01 Login")
    f.box(440, 150, 400, 420, "#fff")
    f.text(470, 205, "Log in", 24, weight=700)
    f.input(470, 260, 340, "Username", "e.g. op1")
    f.input(470, 340, 340, "Password", "••••••••")
    f.button(470, 400, "Log in", w=340)
    f.text(470, 480, "Accounts lock after 3 failed attempts.", 12, MUTED)
    f.text(470, 500, "Sessions end after 15 minutes idle.", 12, MUTED)
    f.note(880, 150, ["Part 11 §11.10(d): unique login", "Error text never says which field", "was wrong (no user enumeration)"])
    return f


def batch():
    f = Frame("02 Batch execution", 900)
    f.text(40, 105, "B-2026-014", 26, weight=700)
    f.pill(210, 86, "in progress", "#b54708")
    f.text(40, 132, "Paracetamol 500 mg tablets · master record v1.0 · ALCOA+ report", 13, MUTED)
    table(f, 40, 160, ["#", "Instruction", "Spec", "Value", "Recorded", "Signatures", "Action"], [
        ["1 ★", "Dispense API", "49.5–50.5 kg", "50.0 kg", "Asha · 09:02", "✔ verified Meera", ""],
        ["2", "Blend", "15–20 min", "17 min", "Asha · 09:25", "", "Correct"],
        ["3", "Granulation temp", "20–25 °C", "—", "", "", "[ value ] Record"],
        ["4 ★", "Hardness", "8–12 kP", "13 kP out of spec", "Asha · 10:10", "", "Verify"],
        ["5 ★", "Tablet weight", "570–630 mg", "—", "", "", "[ value ] Record"]],
        [60, 230, 140, 170, 170, 220, 210])
    f.text(40, 470, "★ critical step: needs second-person verification", 12, MUTED)
    f.box(40, 500, 1200, 150, "#fff")
    f.text(60, 535, "Deviations", 18, weight=700)
    f.text(60, 570, "#1  Hardness = 13 kP outside [8, 12] kP     major", 14)
    f.pill(470, 555, "open", BAD)
    f.box(40, 680, 1200, 150, "#fff")
    f.text(60, 715, "Review and release", 18, weight=700)
    f.text(60, 745, "Release blocked:  • Step 3 not recorded  • Critical step 4 not verified  • Deviation #1 open", 14, BAD)
    f.note(960, 80, ["Out-of-spec value turns red and", "raises a deviation automatically.", "Corrections keep the original."])
    return f


def esign():
    f = Frame("03 E-signature dialog (v1.1 proposal)")
    f.parts.append(f'<rect x="0" y="56" width="{W}" height="{H - 56}" fill="#101828" opacity="0.35"/>')
    f.box(390, 180, 500, 400, "#fff")
    f.text(420, 230, "Sign: verify step 4 (Hardness)", 20, weight=700)
    f.text(420, 262, "Meaning:  Verified", 14)
    f.text(420, 288, "Record:   B-2026-014 · Hardness = 11.2 kP", 14)
    f.text(420, 314, "Signer:   Meera Supervisor (sup1)", 14)
    f.input(420, 360, 440, "Password", "••••••••")
    f.text(420, 430, "By signing you confirm this is your legally binding signature.", 12, MUTED)
    f.button(420, 470, "Cancel", primary=False, w=120)
    f.button(740, 470, "Sign", w=120)
    f.note(930, 180, ["Part 11 §11.50: show name, time,", "meaning. §11.200: re-enter password.", "Today: inline field → propose modal."])
    return f


def release():
    f = Frame("04 QA review and release")
    f.text(40, 105, "B-2026-014", 26, weight=700)
    f.pill(210, 86, "in review", "#b54708")
    f.box(40, 140, 760, 250, "#fff")
    f.text(60, 175, "Release checklist", 18, weight=700)
    for i, (ok, s) in enumerate([(True, "All 5 steps recorded"), (True, "3/3 critical steps verified"),
                                 (True, "Deviation #1 closed (QA, signed)"), (True, "Audit trail intact"),
                                 (True, "ALCOA+ 9/9 pass")]):
        f.text(60, 215 + 32 * i, ("✔  " if ok else "✖  ") + s, 15, OK if ok else BAD)
    f.input(60, 440, 300, "Password to sign", "••••••••")
    f.button(380, 440, "Release batch")
    f.button(540, 440, "Reject batch (v1.1)", primary=False)
    f.note(840, 140, ["Reviewer and releaser must be", "different people (two-person rule).", "Reject needs reason + signature."])
    return f


def audit():
    f = Frame("05 Audit trail")
    f.text(40, 105, "Audit trail", 26, weight=700)
    f.pill(210, 86, "hash chain intact", OK)
    table(f, 40, 130, ["#", "Time (UTC)", "User", "Action", "Record", "Before → After", "Reason"], [
        ["142", "10:41:03", "qa1", "release_batch", "batch 14", "in_review → released", ""],
        ["141", "10:40:51", "qa1", "close_deviation", "deviation 1", "open → closed", "Tester recalibrated…"],
        ["138", "10:12:40", "op1", "correct_value", "entry 9", "13.0 → 11.2", "Re-measured after…"],
        ["131", "10:10:02", "system", "raise_deviation", "deviation 1", "→ Hardness 13 kP…", ""]],
        [60, 130, 90, 170, 130, 330, 290])
    f.note(40, 420, ["Every event stores the hash of the", "previous one: edits/deletions are", "detected and shown here."])
    return f


def cleaning():
    f = Frame("06 Cleaning log (v1.1, PRD US-101/102)")
    f.text(40, 105, "Equipment cleaning log", 26, weight=700)
    table(f, 40, 130, ["Equipment", "Last cleaned", "Type", "By", "Verified", "Valid until", "Status"], [
        ["Blender BL-02", "24 Sep 08:10", "major", "Asha", "Meera", "27 Sep 08:10", "clean"],
        ["Granulator GR-01", "20 Sep 17:40", "minor", "Ravi", "—", "23 Sep 17:40", "expired"]],
        [200, 160, 100, 120, 120, 180, 120])
    f.box(40, 300, 700, 250, "#fff")
    f.text(60, 335, "Record cleaning", 18, weight=700)
    f.input(60, 380, 300, "Equipment", "Select…")
    f.input(380, 380, 300, "Type", "minor / major")
    f.button(60, 450, "Sign and save")
    f.note(780, 300, ["OPEN QUESTIONS (SpecCheck):", "• 72 h from cleaning end or start?", "• 'since last use' = batch start or end?",
                      "• Override: who, reason, e-signature?"])
    return f


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for make in (login, batch, esign, release, audit, cleaning):
        frame = make()
        name = frame.title.split(" (")[0].lower().replace(" ", "_")
        (OUT / f"{name}.svg").write_text(frame.svg(), encoding="utf-8")
    print(f"Wrote {len(list(OUT.glob('*.svg')))} wireframes to {OUT}")


if __name__ == "__main__":
    main()
