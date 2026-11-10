"""Render the written report with embedded figures, without private local links."""

import base64
import html
import re
from pathlib import Path

import mistune

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "docs/final-study-report.md"
body = mistune.create_markdown(escape=False, plugins=["table"])(source.read_text())


def image(match):
    path = (source.parent / match.group(1)).resolve()
    return 'src="data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode() + '"'


body = re.sub(r'src="([^"]+)"', image, body)


def link(match):
    url = match.group(1)
    if url.startswith(("https://", "http://", "#")):
        return match.group(0)
    assert (source.parent / url).resolve().exists(), url
    return 'title="Repository resource: ' + html.escape(url, quote=True) + '"'


body = re.sub(r'href="([^"]+)"', link, body)
css = """body{margin:0;
background:#f4f5f5;
color:#202b31;
font:16px/1.65 Georgia,serif}main{max-width:960px;
margin:36px auto;
padding:48px 60px;
background:white}h1,h2,h3,th{font-family:Arial,sans-serif}h1{font-size:2.2rem;
line-height:1.2;
color:#183d50}h2{font-size:1.4rem;
margin-top:2em;
border-bottom:1px solid #d8e1e5}h3{font-size:1.1rem}a{color:#185d7b}table{width:100%;
border-collapse:collapse;
font:14px/1.4 Arial,sans-serif;
margin:1.5em 0}th{background:#edf3f6;
text-align:left}th,td{padding:9px;
border-bottom:1px solid #d9e0e3}img{max-width:100%;
height:auto}code{font-size:.8em;
overflow-wrap:anywhere}li{margin:.6em 0}@media(max-width:700px){main{margin:0;
padding:20px}table{font-size:11px}th,td{padding:5px}}@media print{@page{size:A4;
margin:16mm}body{background:white;
font-size:10.5pt}main{margin:0;
padding:0}h2,h3{break-after:avoid}tr,img{break-inside:avoid}}"""
out = ROOT / "reports/final-study-report.html"
out.write_text(
    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1">'
    "<title>ECG sleep apnea study</title><style>"
    + css
    + "</style></head><body><main>"
    + body
    + "</main></body></html>"
)
print(out)
