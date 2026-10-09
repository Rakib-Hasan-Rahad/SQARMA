"""Strip HTML (untrusted) to text and print sentences matching regex. Usage: v3_grep_text.py FILE REGEX"""
import re, sys, html
t = open(sys.argv[1], encoding="utf-8", errors="replace").read()
t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t); t = html.unescape(re.sub(r"<[^>]+>", " ", t)); t = re.sub(r"\s+", " ", t)
for s in re.split(r"(?<=[.!?])\s+", t):
    if re.search(sys.argv[2], s, re.I): print("-", s[:400])
