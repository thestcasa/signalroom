from __future__ import annotations

import json
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outreach" / "SignalRoom_Case_Study.pdf"
INK = colors.HexColor("#102A43")
TEAL = colors.HexColor("#00A6A6")
CORAL = colors.HexColor("#FF6B5E")
PAPER = colors.HexColor("#F7F5EF")
MIST = colors.HexColor("#E8F1F5")
MUTED = colors.HexColor("#587287")
FONT = "DejaVuSans"
BOLD = "DejaVuSans-Bold"


def load(slug: str) -> dict:
    path = ROOT / "artifacts" / "cases" / slug / "bundle.json"
    return json.loads(path.read_text(encoding="utf-8"))


def paragraph(
    canvas: Canvas, text: str, x: float, y: float, width: float, style: ParagraphStyle
) -> float:
    block = Paragraph(text, style)
    _, height = block.wrap(width, 100 * mm)
    block.drawOn(canvas, x, y - height)
    return y - height


def main() -> None:
    pdfmetrics.registerFont(TTFont(FONT, "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont(BOLD, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
    brighton = load("brighton-wsl-2023-24")
    leverkusen = load("leverkusen-bundesliga-2023-24")
    width, height = A4
    canvas = Canvas(str(OUTPUT), pagesize=A4)
    canvas.setTitle("SignalRoom - Evidence-linked football intelligence")
    canvas.setAuthor("Alessandro Casadei")
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)

    canvas.setFillColor(INK)
    canvas.rect(0, height - 69 * mm, width, 69 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont(BOLD, 11)
    canvas.drawString(18 * mm, height - 17 * mm, "SIGNAL")
    canvas.setFillColor(TEAL)
    canvas.drawString(35.5 * mm, height - 17 * mm, "ROOM")
    canvas.setFillColor(CORAL)
    canvas.setFont(BOLD, 7.5)
    canvas.drawString(18 * mm, height - 29 * mm, "EVIDENCE-LINKED FOOTBALL INTELLIGENCE")
    canvas.setFillColor(colors.white)
    canvas.setFont(BOLD, 29)
    canvas.drawString(18 * mm, height - 44 * mm, "A briefing that can abstain")
    canvas.setFont(FONT, 11)
    canvas.setFillColor(colors.HexColor("#DCE8ED"))
    canvas.drawString(
        18 * mm,
        height - 53 * mm,
        "Public event data in. Prioritized, traceable historical evidence out.",
    )
    canvas.setFont(FONT, 8.5)
    canvas.drawString(
        18 * mm,
        height - 61 * mm,
        "Independent case study by Alessandro Casadei | MSc Data Science and Engineering",
    )

    card_y = height - 82 * mm
    stats = [
        (str(brighton["case"]["matches"]), "Brighton matches"),
        (f"{brighton['set_piece_lab']['corner_count']}", "Attacking corners"),
        (str(len(brighton["set_piece_lab"]["published_routines"])), "Repeatable routines"),
        ("0", "Forced broad claims"),
    ]
    card_width = 41 * mm
    for index, (value, label) in enumerate(stats):
        x = 18 * mm + index * 44 * mm
        canvas.setFillColor(colors.white)
        canvas.roundRect(x, card_y - 22 * mm, card_width, 22 * mm, 3 * mm, fill=1, stroke=0)
        canvas.setFillColor(INK)
        canvas.setFont(BOLD, 20)
        canvas.drawString(x + 5 * mm, card_y - 9 * mm, value)
        canvas.setFillColor(MUTED)
        canvas.setFont(FONT, 7.5)
        canvas.drawString(x + 5 * mm, card_y - 16 * mm, label)

    body_top = height - 118 * mm
    left_x = 18 * mm
    right_x = 112 * mm
    left_w = 82 * mm
    right_w = 79 * mm
    label_style = ParagraphStyle(
        "label", fontName=BOLD, fontSize=7.5, leading=9, textColor=CORAL, spaceAfter=2
    )
    body_style = ParagraphStyle(
        "body", fontName=FONT, fontSize=8.4, leading=11.3, textColor=INK, alignment=TA_LEFT
    )
    small_style = ParagraphStyle("small", fontName=FONT, fontSize=7.1, leading=9.2, textColor=MUTED)
    heading_style = ParagraphStyle(
        "heading", fontName=BOLD, fontSize=14.5, leading=17, textColor=INK
    )

    y = paragraph(canvas, "PRIMARY HISTORICAL CASE", left_x, body_top, left_w, label_style)
    y = paragraph(canvas, "Brighton Women, WSL 2023/24", left_x, y - 2 * mm, left_w, heading_style)
    y = paragraph(
        canvas,
        "All seven match-window changes were suppressed: effects were too small, unstable, or weak after multiple-comparison control. That abstention is the main credibility result.",
        left_x,
        y - 3 * mm,
        left_w,
        body_style,
    )
    y -= 7 * mm
    canvas.setFillColor(INK)
    canvas.setFont(BOLD, 10)
    canvas.drawString(left_x, y, "Published corner routines")
    y -= 7 * mm
    canvas.setFont(BOLD, 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(left_x, y, "ROUTINE")
    canvas.drawRightString(left_x + 57 * mm, y, "N")
    canvas.drawRightString(left_x + 70 * mm, y, "SHOTS")
    canvas.drawRightString(left_x + 82 * mm, y, "xG")
    y -= 3 * mm
    canvas.setStrokeColor(colors.HexColor("#CFDCE2"))
    canvas.line(left_x, y, left_x + left_w, y)
    for routine in brighton["set_piece_lab"]["published_routines"]:
        y -= 7 * mm
        canvas.setFillColor(INK)
        canvas.setFont(FONT, 7.2)
        name = routine["routine"].replace("central goalmouth", "central")
        canvas.drawString(left_x, y, name[:42])
        canvas.drawRightString(left_x + 57 * mm, y, str(routine["count"]))
        canvas.drawRightString(left_x + 70 * mm, y, str(routine["shots"]))
        canvas.drawRightString(left_x + 82 * mm, y, f"{routine['xg']:.2f}")
    y -= 9 * mm
    paragraph(
        canvas,
        "Each routine links to match ID, event IDs, players, coordinates, ordered actions, and the source corner. Clusters with fewer than four examples are not published.",
        left_x,
        y,
        left_w,
        small_style,
    )

    y2 = paragraph(canvas, "WHAT THE BUILD DEMONSTRATES", right_x, body_top, right_w, label_style)
    y2 = paragraph(
        canvas, "A complete analytical system", right_x, y2 - 2 * mm, right_w, heading_style
    )
    bullets = [
        "Provider adapter and normalized internal event model",
        "Versioned metric definitions and reproducible acquisition",
        "Match-level bootstrap intervals and sensitivity checks",
        "Effect-size and false-discovery publication gates",
        "Deterministic reporting that works without an LLM",
        "Interactive evidence room and exportable reports",
    ]
    for bullet in bullets:
        canvas.setFillColor(TEAL)
        canvas.circle(right_x + 1.2 * mm, y2 - 3.1 * mm, 1.1 * mm, fill=1, stroke=0)
        y2 = paragraph(canvas, bullet, right_x + 5 * mm, y2, right_w - 5 * mm, body_style) - 2 * mm

    y2 -= 2 * mm
    canvas.setFillColor(MIST)
    canvas.roundRect(right_x, y2 - 39 * mm, right_w, 39 * mm, 3 * mm, fill=1, stroke=0)
    paragraph(
        canvas, "PORTABILITY CHECK", right_x + 5 * mm, y2 - 5 * mm, right_w - 10 * mm, label_style
    )
    paragraph(
        canvas,
        f"The same code and only a different TOML configuration processed Bayer Leverkusen: {leverkusen['case']['matches']} matches, {leverkusen['set_piece_lab']['corner_count']} corners, and {len(leverkusen['set_piece_lab']['published_routines'])} published routine groups.",
        right_x + 5 * mm,
        y2 - 13 * mm,
        right_w - 10 * mm,
        body_style,
    )

    strip_y = 36 * mm
    canvas.setFillColor(INK)
    canvas.roundRect(18 * mm, strip_y, 173 * mm, 29 * mm, 3 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont(BOLD, 9)
    canvas.drawString(24 * mm, strip_y + 20 * mm, "POSITIONING")
    canvas.setFillColor(colors.HexColor("#DCE8ED"))
    canvas.setFont(FONT, 8)
    canvas.drawString(
        24 * mm,
        strip_y + 12 * mm,
        "Historical analyst triage, not current tactical advice. No club affiliation. No private data.",
    )
    canvas.drawString(
        24 * mm,
        strip_y + 6 * mm,
        "No causal or predictive sporting-value claim. Raw provider data is not redistributed.",
    )

    logo = ROOT / "assets" / "statsbomb-open-data-logo.png"
    logo_image = Image.open(logo).convert("RGB")
    canvas.drawImage(
        ImageReader(logo_image),
        18 * mm,
        17 * mm,
        width=40 * mm,
        height=6.4 * mm,
        preserveAspectRatio=True,
    )
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 6.8)
    canvas.drawString(18 * mm, 11 * mm, "Data: StatsBomb Open Data. Source terms apply.")
    canvas.setFillColor(TEAL)
    canvas.setFont(BOLD, 7.4)
    canvas.drawRightString(191 * mm, 18 * mm, "github.com/thestcasa/signalroom")
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 6.8)
    canvas.drawRightString(191 * mm, 11 * mm, "SignalRoom v0.1 | Generated 18 September 2026")
    canvas.save()


if __name__ == "__main__":
    main()
