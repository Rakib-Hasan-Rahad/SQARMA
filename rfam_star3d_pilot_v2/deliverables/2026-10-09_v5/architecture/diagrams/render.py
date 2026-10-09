"""Render Mermaid sources (*.mmd) to PNG with headless Chrome + mermaid (cdn.jsdelivr.net), then crop whitespace."""
import glob
import html
import os
import subprocess

from PIL import Image, ImageChops

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HERE = os.path.dirname(os.path.abspath(__file__))
TPL = """<!doctype html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<style>body{margin:0;background:#fff;font-family:Arial,Helvetica,sans-serif} .mermaid{display:inline-block;padding:12px}</style>
</head><body><pre class="mermaid">%s</pre>
<script>mermaid.initialize({startOnLoad:true, theme:'neutral', flowchart:{useMaxWidth:false, htmlLabels:true, curve:'basis', nodeSpacing:30, rankSpacing:40},
 themeVariables:{fontSize:'15px', fontFamily:'Arial, Helvetica, sans-serif'}});</script></body></html>"""
for src in sorted(glob.glob(os.path.join(HERE, "*.mmd"))):
    stem = os.path.splitext(src)[0]
    open(stem + ".html", "w").write(TPL % html.escape(open(src).read()))
    png = stem + ".png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                    "--virtual-time-budget=15000", "--window-size=1600,4200", f"--screenshot={png}",
                    "file://" + stem + ".html"], capture_output=True)
    im = Image.open(png).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    box = ImageChops.difference(im, bg).getbbox()
    if box:
        im = im.crop((max(box[0] - 20, 0), max(box[1] - 20, 0), min(box[2] + 20, im.width), min(box[3] + 20, im.height)))
    im.save(png)
    print(os.path.basename(png), im.size)
