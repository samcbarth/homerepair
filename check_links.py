#!/usr/bin/env python3
"""Link check. `python check_links.py` checks internal links; add `--external` to also HEAD/GET every outside URL."""
import pathlib, re, sys, json, urllib.request, concurrent.futures as cf
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).parent
SKIP = {"content", ".git", ".claude", "__pycache__"}


class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.ids = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k): self.links.append(a[k])


def target(path):
    path = path.split("#")[0].split("?")[0]
    p = ROOT / path.lstrip("/")
    if path.endswith("/") or p.is_dir():
        p = p / "index.html"
    return p


pages = [p for p in ROOT.rglob("*.html") if not (set(p.relative_to(ROOT).parts) & SKIP)]
bad, external = [], set()
for page in pages:
    pr = P(); pr.feed(page.read_text(encoding="utf-8"))
    for l in pr.links:
        if l.startswith(("http://", "https://")):
            if "samcbarth.com" not in l: external.add(l.replace("&amp;", "&"))
            continue
        if l.startswith(("mailto:", "#", "data:", "javascript:")):
            continue
        if not target(l).exists():
            bad.append(f"{page.relative_to(ROOT)} -> {l}")
print(f"{len(pages)} pages, {len(bad)} broken internal links")
for b in bad: print("  BROKEN", b)

if "--external" in sys.argv:
    ext = sorted(u for u in external if "amazon.com" not in u)
    def get(u):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (link check)"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return u, r.status
        except Exception as e:
            return u, getattr(e, "code", str(e)[:60])
    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(get, ext))
    fails = [(u, s) for u, s in res if s != 200]
    print(f"{len(ext)} external URLs checked, {len(fails)} not 200")
    for u, s in fails: print("  ", s, u)
sys.exit(1 if bad else 0)
