"""Format the final Markdown report as PDF; no scientific calculations or training."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
WIDTH = A4[0] - 96
SOURCE = ROOT / "docs/final-study-report.md"
OUTPUT = ROOT / "reports/final-study-report.pdf"
BLUE = colors.HexColor("#183d50")
STYLES = getSampleStyleSheet()
STYLES.add(
    ParagraphStyle(
        "ReportTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=BLUE,
        spaceAfter=14,
    )
)
STYLES.add(
    ParagraphStyle(
        "ReportBody",
        fontName="Times-Roman",
        fontSize=10.5,
        leading=14.2,
        spaceAfter=8,
        splitLongWords=True,
        allowWidows=0,
        allowOrphans=0,
    )
)
STYLES.add(
    ParagraphStyle(
        "ReportH2",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=BLUE,
        spaceBefore=16,
        spaceAfter=9,
        keepWithNext=True,
    )
)
STYLES.add(
    ParagraphStyle(
        "ReportH3",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=BLUE,
        spaceBefore=11,
        spaceAfter=7,
        keepWithNext=True,
    )
)
STYLES.add(
    ParagraphStyle("ReportCell", fontName="Helvetica", fontSize=8, leading=10.5, spaceAfter=0)
)
STYLES.add(
    ParagraphStyle(
        "ReportCaption",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#455a64"),
        spaceBefore=5,
        spaceAfter=12,
    )
)
CAPTIONS = {
    "rq1": "Figure 1. RR variability improved mean AP under fixed classifier settings.",
    "rq2": "Figure 2. Five fold scores and their means; dashed line: constant-score reference.",
    "thresholds": "Figure 3. CNN inner thresholds already favored many positive calls.",
    "curves": "Figure 4. Selected training and stopping losses; dotted lines mark chosen epochs.",
    "signals": "Figure 5. Shading marks constant-source minutes before and after filtering.",
}


def ascii_punctuation(s):
    return s.translate(
        str.maketrans(
            {
                "–": "-",
                "—": "-",
                "−": "-",
                "‑": "-",
                "‘": "'",
                "’": "'",
                "“": '"',
                "”": '"',
                "·": " | ",
            }
        )
    )


def inline(nodes):
    out = []
    for node in nodes:
        typ = node["type"]
        children = node.get("children", [])
        if typ == "text":
            out.append(html.escape(ascii_punctuation(node["raw"])))
        elif typ == "strong":
            out.append("<b>" + inline(children) + "</b>")
        elif typ == "emphasis":
            out.append("<i>" + inline(children) + "</i>")
        elif typ == "codespan":
            out.append(
                '<font name="Courier" size="8">'
                + html.escape(ascii_punctuation(node["raw"]))
                + "</font>"
            )
        elif typ == "link":
            url = node["attrs"]["url"]
            label = inline(children)
            out.append(
                '<link href="'
                + html.escape(url, quote=True)
                + '" color="#185d7b">'
                + label
                + "</link>"
                if url.startswith(("http://", "https://"))
                else label
            )
        elif typ in ["softbreak", "linebreak"]:
            out.append(" " if typ == "softbreak" else "<br/>")
        elif typ != "image":
            out.append(
                inline(children)
                if children
                else html.escape(ascii_punctuation(node.get("raw", "")))
            )
    return "".join(out)


def make_table(token):
    head = token["children"][0]["children"]
    rows = [head] + [r["children"] for r in token["children"][1]["children"]]
    data = [
        [Paragraph(inline(cell["children"]), STYLES["ReportCell"]) for cell in row] for row in rows
    ]
    lengths = [
        max(len(re.sub("<[^>]+>", "", inline(row[i]["children"]))) for row in rows)
        for i in range(len(head))
    ]
    weights = [max(10, min(42, length)) for length in lengths]
    # First column names need room; numeric columns can stay narrow.
    if len(weights) >= 4:
        weights = [max(weights[0], 28)] + [min(w, 19) for w in weights[1:]]
    widths = [WIDTH * w / sum(weights) for w in weights]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf3f6")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafbfc")]),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#9caeb8")),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#dce4e8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return [KeepTogether([Spacer(1, 5), table, Spacer(1, 11)])]


def blocks(tokens):
    story = []
    for t in tokens:
        typ = t["type"]
        if typ == "heading":
            level = t["attrs"]["level"]
            name = "ReportTitle" if level == 1 else "ReportH2" if level == 2 else "ReportH3"
            story.append(Paragraph(inline(t["children"]), STYLES[name]))
        elif typ in ["paragraph", "block_text"]:
            children = t.get("children", [])
            images = [x for x in children if x["type"] == "image"]
            if images:
                for image in images:
                    path = (SOURCE.parent / image["attrs"]["url"]).resolve()
                    fig = Image(str(path))
                    scale = min(WIDTH / fig.imageWidth, 220 / fig.imageHeight)
                    fig.drawWidth = fig.imageWidth * scale
                    fig.drawHeight = fig.imageHeight * scale
                    fig.hAlign = "CENTER"
                    caption = Paragraph(
                        CAPTIONS.get(path.stem, inline(image.get("children", []))),
                        STYLES["ReportCaption"],
                    )
                    story.append(KeepTogether([Spacer(1, 8), fig, caption]))
            else:
                story.append(Paragraph(inline(children), STYLES["ReportBody"]))
        elif typ == "table":
            story.extend(make_table(t))
        elif typ == "list":
            start = t.get("attrs", {}).get("start", 1)
            for i, item in enumerate(t["children"]):
                nested = blocks(item["children"])
                if nested and isinstance(nested[0], Paragraph):
                    bullet = f"{start + i}." if t.get("attrs", {}).get("ordered") else "-"
                    nested[0] = Paragraph(bullet + " " + nested[0].text, STYLES["ReportBody"])
                story.extend(nested)
        elif typ in ["block_quote"]:
            story.extend(blocks(t["children"]))
    return story


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d5dfe4"))
    canvas.line(48, 37, A4[0] - 48, 37)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#526873"))
    canvas.drawString(48, 25, "ECG sleep apnea classification | Study report")
    canvas.drawRightString(A4[0] - 48, 25, str(doc.page))
    canvas.restoreState()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        tokens = json.loads(Path(sys.argv[1]).read_text())
    else:
        import mistune

        tokens = mistune.create_markdown(renderer="ast", plugins=["table"])(SOURCE.read_text())
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=48,
        leftMargin=48,
        topMargin=45,
        bottomMargin=52,
        title="RR interval features and a lightweight CNN for sleep apnea classification",
        author="S-W-Leong",
    )
    story = blocks(tokens)
    packed = []
    i = 0
    while i < len(story):
        item = story[i]
        if isinstance(item, Paragraph) and item.style.name in {"ReportH2", "ReportH3"}:
            group = [item]
            i += 1
            while (
                i < len(story)
                and isinstance(story[i], Paragraph)
                and story[i].style.name in {"ReportH2", "ReportH3"}
            ):
                group.append(story[i])
                i += 1
            if i < len(story):
                next_item = story[i]
                if isinstance(next_item, KeepTogether):
                    group.extend(next_item._content)
                else:
                    group.append(next_item)
                i += 1
            packed.append(KeepTogether(group))
        else:
            packed.append(item)
            i += 1
    doc.build(packed, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)
