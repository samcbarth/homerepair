#!/usr/bin/env python3
"""Static build for homerepair.samcbarth.com (Fix It Notes).

Sources (edit these, then run `python build.py`):
  config.json            site ids (Amazon tag, AdSense, contact form)
  content/categories.json category hubs
  content/guides/*.json  one repair guide per file
  content/toolkit.json   basic home toolkit buying guide
  content/news/*.json    one news story per file
  content/pages.json     about / contact / privacy / terms / disclosure

Outputs plain HTML at the repo root for GitHub Pages.
"""
import json, html, pathlib, datetime, re, shutil
from urllib.parse import quote_plus

ROOT = pathlib.Path(__file__).parent
C = ROOT / "content"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
BASE = CFG["BASE_URL"].rstrip("/")
SITE = CFG["SITE_NAME"]
TODAY = datetime.date.today().isoformat()

CATS = json.loads((C / "categories.json").read_text(encoding="utf-8"))
CAT = {c["slug"]: c for c in CATS}
GUIDES = sorted((json.loads(p.read_text(encoding="utf-8")) for p in (C / "guides").glob("*.json")),
                key=lambda g: g["title"])
G = {g["slug"]: g for g in GUIDES}
NEWS = sorted((json.loads(p.read_text(encoding="utf-8")) for p in (C / "news").glob("*.json")),
              key=lambda n: n["date"], reverse=True)
TOOLKIT = json.loads((C / "toolkit.json").read_text(encoding="utf-8"))
PAGES = json.loads((C / "pages.json").read_text(encoding="utf-8"))

NETWORK = [
    ("realestate", "Real Estate"), ("tools", "Tools"), ("games", "Games"),
    ("streaming", "Streaming"), ("homerepair", "Home Repair"), ("deals", "Deals"), ("news", "News"),
]

CALCS = [
    {"slug": "paint-coverage", "title": "Paint Coverage Calculator",
     "short": "How many gallons of paint for a room",
     "desc": "Free paint calculator: enter room size, doors, windows and coats to estimate how many gallons of wall paint you need."},
    {"slug": "tile-flooring", "title": "Tile and Flooring Calculator",
     "short": "Square feet and boxes of tile, laminate or vinyl plank",
     "desc": "Free flooring calculator: get square footage, waste allowance and the number of boxes of tile, laminate or vinyl plank to buy."},
    {"slug": "mulch-gravel", "title": "Mulch and Gravel Calculator",
     "short": "Cubic yards, bags and tons for beds and paths",
     "desc": "Free mulch and gravel calculator: convert bed size and depth into cubic yards, 2 cubic foot bags, and approximate tons of gravel."},
]

esc = html.escape


def j(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1).replace("</", "<\\/")


def amazon(q):
    url = "https://www.amazon.com/s?k=" + quote_plus(q)
    if CFG.get("AMAZON_TAG"):
        url += "&tag=" + quote_plus(CFG["AMAZON_TAG"])
    return url


def amazon_btn(q, label="Check price on Amazon"):
    return (f'<a class="btn-amz" href="{esc(amazon(q))}" target="_blank" '
            f'rel="sponsored nofollow noopener">{esc(label)}</a>')


DISCLOSURE = ('<p class="disclosure">Some links below are affiliate links. If you buy through them we may earn a '
              'commission at no extra cost to you. <a href="/affiliate-disclosure/">How this works</a>.</p>')

GTM = f'''<script async src="https://www.googletagmanager.com/gtag/js?id={CFG["GTM_ID"]}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{CFG["GTM_ID"]}');
</script>
<!-- monetag -->
<script src="https://5gvci.com/act/files/tag.min.js?z=12242945" data-cfasync="false" async></script>
<script>(function(s){{s.dataset.zone='12242946',s.src='https://nap5k.com/tag.min.js'}})([document.documentElement, document.body].filter(Boolean).pop().appendChild(document.createElement('script')))</script>
<script>(function(s){{s.dataset.zone='12242947',s.src='https://n6wxm.com/vignette.min.js'}})([document.documentElement, document.body].filter(Boolean).pop().appendChild(document.createElement('script')))</script>'''

ICONS = {
    "plumbing": '<path d="M7 3v5a5 5 0 0 0 10 0V3M12 13v8M8 21h8"/>',
    "electrical": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "walls": '<path d="M3 5h18v14H3zM3 12h18M9 5v7M15 12v7"/>',
    "doors-windows": '<path d="M6 3h12v18H6zM14 12h.01"/>',
    "appliances": '<path d="M5 3h14v18H5zM5 9h14M9 6h.01"/>',
    "outdoor": '<path d="M12 3 4 10h3v8h10v-8h3zM10 18v-4h4v4"/>',
    "tool": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    "calc": '<path d="M6 3h12v18H6zM9 7h6M9 12h.01M12 12h.01M15 12h.01M9 16h.01M12 16h.01M15 16h.01"/>',
    "news": '<path d="M4 5h13v14H6a2 2 0 0 1-2-2zM17 9h3v8a2 2 0 0 1-2 2M8 9h5M8 13h5"/>',
}


def icon(name, size=28):
    return (f'<svg class="ico" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + u}
                                for i, (n, u) in enumerate(items)]}


def crumbs_html(items):
    parts = []
    for i, (n, u) in enumerate(items):
        parts.append(f'<a href="{u}">{esc(n)}</a>' if i < len(items) - 1 else f'<span aria-current="page">{esc(n)}</span>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + ' <span class="sep">/</span> '.join(parts) + '</nav>'


WEBSITE_LD = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE, "url": BASE + "/",
              "description": CFG["SITE_TAGLINE"], "publisher": {"@type": "Person", "name": CFG["AUTHOR"]}}


def ad_slot(name):
    """Renders nothing until ADSENSE_CLIENT is set (assets/site.js fills it)."""
    if not CFG.get("ADSENSE_CLIENT"):
        return ""
    return f'<div class="ad-slot" data-ad-slot="{name}"></div>'


def page(path, title, desc, body, crumbs=None, ld=None, og_type="website", og_image="/assets/og/default.png", extra_head=""):
    """path like '/guides/x/' -> writes guides/x/index.html"""
    canonical = BASE + path
    lds = [WEBSITE_LD] + ([crumbs_ld(crumbs)] if crumbs else []) + (ld or [])
    ld_html = "\n".join(f'<script type="application/ld+json">{j(x)}</script>' for x in lds)
    nav = "".join(f'<a href="/{c["slug"]}/">{esc(c["short"])}</a>' for c in CATS)
    net = "".join(
        (f'<span class="net-cur" aria-current="true">{esc(label)}</span>' if sub == "homerepair"
         else f'<a href="https://{sub}.samcbarth.com/">{esc(label)}</a>')
        for sub, label in NETWORK)
    full_title = title if SITE in title else f"{title} | {SITE}"
    doc = f'''<!doctype html>
<html lang="en">
<head>
{GTM}
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(SITE)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE)}" href="/feed.xml">
<link rel="alternate" type="application/feed+json" title="{esc(CFG["NEWS_BRAND"])}" href="/news/feed.json">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&family=Barlow:wght@900&family=Inter:wght@400;500;700&display=swap">
<link rel="stylesheet" href="/assets/style.css">
{extra_head}{ld_html}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
 <div class="wrap head-row">
  <a class="brand" href="/"><span class="dot" aria-hidden="true"></span><span>{esc(SITE)}</span></a>
  <nav class="main-nav" aria-label="Main">{nav}<a href="/calculators/">Calculators</a><a href="/basic-home-toolkit/">Toolkit</a><a href="/news/">News</a></nav>
 </div>
</header>
<div class="grad-band" aria-hidden="true"></div>
<main id="main" class="wrap">
{crumbs_html(crumbs) if crumbs else ""}
{body}
</main>
<div class="grad-band" aria-hidden="true"></div>
<footer class="site-foot">
 <div class="wrap">
  <p class="foot-links"><a href="/about/">About</a><a href="/contact/">Contact</a><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a><a href="/affiliate-disclosure/">Affiliate disclosure</a><a href="/guides/">All guides</a><a href="/feed.xml">RSS</a></p>
  <p class="foot-note">Guides are general information, not professional advice. Follow local codes and the manufacturer's instructions, and hire a licensed pro for electrical, gas and structural work where required.</p>
  <nav class="network" aria-label="samcbarth.com network"><span class="net-label">Network:</span>{net}</nav>
  <p class="foot-note">&copy; {datetime.date.today().year} {esc(SITE)} on samcbarth.com</p>
 </div>
</footer>
<script src="/assets/config.js"></script>
<script src="/assets/site.js" defer></script>
</body>
</html>
'''
    out = ROOT / path.strip("/") / "index.html" if path != "/" else ROOT / "index.html"
    if path.endswith(".html"):
        out = ROOT / path.strip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    SITEMAP.append(path)


SITEMAP = []


def guide_card(g):
    c = CAT[g["category"]]
    return (f'<a class="card" href="/guides/{g["slug"]}/"><span class="card-cat">{esc(c["short"])}</span>'
            f'<strong>{esc(g["title"])}</strong><span class="card-meta">{esc(g["difficulty"])} &middot; {esc(g["time"])}</span></a>')


def news_card(n):
    return (f'<a class="card" href="/news/{n["slug"]}/"><span class="card-cat">{esc(n["tags"][0])}</span>'
            f'<strong>{esc(n["title"])}</strong><span class="card-meta">{fmt_date(n["date"])}</span></a>')


def fmt_date(d):
    x = datetime.date.fromisoformat(d)
    return f"{x:%B} {x.day}, {x.year}"


def items_list(items):
    rows = []
    for it in items:
        note = f'<span class="item-note">{esc(it["note"])}</span>' if it.get("note") else ""
        btn = amazon_btn(it["q"]) if it.get("q") else ""
        rows.append(f'<li><div><span class="item-name">{esc(it["name"])}</span>{note}</div>{btn}</li>')
    return '<ul class="items">' + "".join(rows) + "</ul>"


WARN = {
    "electrical": ("Electrical safety", "Turn off the breaker for this circuit and confirm the power is off with a voltage tester before you touch any wire. Many places require a licensed electrician or a permit for wiring work. If anything you see does not match these steps, stop and call an electrician."),
    "gas": ("Gas safety", "If you smell gas (a rotten-egg odor), do not light anything or flip switches. Leave the house and call your gas utility or 911 from outside. Gas valve, burner and venting repairs belong to a licensed technician."),
    "ladder": ("Ladder safety", "Set the ladder on firm, level ground, keep three points of contact, never stand on the top rungs, and look up for power lines before you raise it. Work with a helper when you can."),
    "structural": ("Structural safety", "Cracks wider than about 1/4 inch, sagging, or doors and windows that suddenly bind can point to structural movement. Have a structural engineer or licensed contractor look before you patch."),
}


def build_guide(g):
    c = CAT[g["category"]]
    crumbs = [("Home", "/"), (c["name"], f'/{c["slug"]}/'), (g["title"], f'/guides/{g["slug"]}/')]
    warns = "".join(
        f'<aside class="warn warn-{w}" role="note"><strong>{esc(WARN[w][0])}</strong><p>{esc(WARN[w][1])}</p></aside>'
        for w in g.get("warnings", []))
    steps = "".join(f'<li id="step-{i+1}"><h3>{esc(s["title"])}</h3><p>{s["text"]}</p></li>' for i, s in enumerate(g["steps"]))
    safety = "".join(f"<li>{esc(s)}</li>" for s in g["safety"])
    pro = "".join(f"<li>{esc(s)}</li>" for s in g["call_pro"])
    faq = "".join(f'<details><summary><h3>{esc(f["q"])}</h3></summary><p>{esc(f["a"])}</p></details>' for f in g["faq"])
    srcs = "".join(f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["name"])}</a></li>' for s in g["sources"])
    related = [G[s] for s in g.get("related", []) if s in G]
    rel_html = ('<section><h2>Related guides</h2><div class="cards">' + "".join(guide_card(r) for r in related) + "</div></section>") if related else ""
    calc_link = ""
    if g.get("calc"):
        cc = next(x for x in CALCS if x["slug"] == g["calc"])
        calc_link = f'<p class="callout">Planning materials? Try the <a href="/calculators/{cc["slug"]}/">{esc(cc["title"])}</a>.</p>'
    news_rel = [n for n in NEWS if g["slug"] in n.get("related", [])]
    news_html = ""
    if news_rel:
        news_html = '<section><h2>In the news</h2><ul class="plain">' + "".join(
            f'<li><a href="/news/{n["slug"]}/">{esc(n["title"])}</a> <span class="muted">({fmt_date(n["date"])})</span></li>' for n in news_rel) + "</ul></section>"
    has_items = any(it.get("q") for it in g["tools"] + g["materials"])
    body = f'''
<article class="guide">
 <header class="g-head">
  <p class="eyebrow"><a href="/{c["slug"]}/">{esc(c["name"])}</a></p>
  <h1>{esc(g["title"])}</h1>
  <div class="answer"><p><strong>Short answer:</strong> {esc(g["summary"])}</p></div>
  <dl class="facts"><div><dt>Difficulty</dt><dd>{esc(g["difficulty"])}</dd></div><div><dt>Time</dt><dd>{esc(g["time"])}</dd></div><div><dt>Updated</dt><dd>{fmt_date(g.get("updated", TODAY))}</dd></div></dl>
 </header>
 {warns}
 {ad_slot("after-intro")}
 <section><h2>What is causing it?</h2><p>{g["causes"]}</p></section>
 <section class="kit">
  <h2>Tools and materials</h2>
  {DISCLOSURE if has_items else ""}
  <h3>Tools</h3>{items_list(g["tools"])}
  <h3>Materials</h3>{items_list(g["materials"])}
 </section>
 <section><h2>How do you {esc(g["howto_verb"])}? Step by step</h2><ol class="steps">{steps}</ol></section>
 {calc_link}
 {ad_slot("mid-content")}
 <section class="safety"><h2>Safety notes</h2><ul>{safety}</ul></section>
 <section class="pro"><h2>When should you call a pro?</h2><ul>{pro}</ul></section>
 <section class="faq"><h2>Frequently asked questions</h2>{faq}</section>
 <section class="sources"><h2>Sources</h2><p class="muted">Steps are based on these manufacturer and safety references. Your product's own manual comes first.</p><ul>{srcs}</ul></section>
 {news_html}
 {rel_html}
 {ad_slot("end-content")}
</article>'''
    ld = [{
        "@context": "https://schema.org", "@type": "Article", "headline": g["title"],
        "description": g["summary"], "datePublished": g.get("published", TODAY), "dateModified": g.get("updated", TODAY),
        "author": {"@type": "Person", "name": CFG["AUTHOR"]}, "publisher": {"@type": "Organization", "name": SITE, "url": BASE + "/"},
        "mainEntityOfPage": BASE + f'/guides/{g["slug"]}/', "image": BASE + f'/assets/og/{c["slug"]}.png',
        "articleSection": c["name"], "citation": [s["url"] for s in g["sources"]],
    }, {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in g["faq"]],
    }]
    page(f'/guides/{g["slug"]}/', g["title"], g["meta"], body, crumbs, ld, "article", f'/assets/og/{c["slug"]}.png')


def build_category(c):
    gs = [g for g in GUIDES if g["category"] == c["slug"]]
    crumbs = [("Home", "/"), (c["name"], f'/{c["slug"]}/')]
    body = f'''
<header class="hub-head">{icon(c["slug"], 40)}<div><h1>{esc(c["name"])} repairs you can do yourself</h1><p class="lead">{esc(c["intro"])}</p></div></header>
{f'<aside class="warn" role="note"><strong>Safety first</strong><p>{esc(c["safety"])}</p></aside>' if c.get("safety") else ""}
<section><h2>{esc(c["short"])} guides</h2><div class="cards">{"".join(guide_card(g) for g in gs)}</div></section>
<section><h2>What {esc(c["short"].lower())} jobs are safe to DIY?</h2><p>{esc(c["diy_line"])}</p></section>
<section><h2>Tools for {esc(c["short"].lower())} work</h2><p>Most of these jobs use the same short list of hand tools. See the <a href="/basic-home-toolkit/">basic home toolkit</a> for what to buy first.</p></section>
{ad_slot("end-content")}'''
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": c["name"] + " repair guides",
           "description": c["meta"], "url": BASE + f'/{c["slug"]}/',
           "hasPart": [{"@type": "Article", "headline": g["title"], "url": BASE + f'/guides/{g["slug"]}/'} for g in gs]}]
    page(f'/{c["slug"]}/', f'{c["name"]} Repair Guides', c["meta"], body, crumbs, ld, og_image=f'/assets/og/{c["slug"]}.png')


def build_toolkit():
    t = TOOLKIT
    crumbs = [("Home", "/"), ("Basic home toolkit", "/basic-home-toolkit/")]
    secs = ""
    for s in t["sections"]:
        rows = ""
        for it in s["items"]:
            uses = ", ".join(f'<a href="/guides/{u}/">{esc(G[u]["title"].lower())}</a>' for u in it.get("used_in", []) if u in G)
            uses_html = f'<p class="muted small">Used in: {uses}</p>' if uses else ""
            rows += (f'<div class="tk-item"><div><h3>{esc(it["name"])}</h3><p>{esc(it["why"])}</p>'
                     f'<p class="small"><strong>What to look for:</strong> {esc(it["look_for"])}</p>{uses_html}</div>{amazon_btn(it["q"])}</div>')
        secs += f'<section><h2>{esc(s["title"])}</h2><p>{esc(s["intro"])}</p>{rows}</section>'
    faq = "".join(f'<details><summary><h3>{esc(f["q"])}</h3></summary><p>{esc(f["a"])}</p></details>' for f in t["faq"])
    body = f'''
<article class="guide">
<h1>{esc(t["title"])}</h1>
<div class="answer"><p><strong>Short answer:</strong> {esc(t["summary"])}</p></div>
<p class="muted small">How we chose: we listed the tools the guides on this site actually call for and noted the features that matter for each. We have not run hands-on product tests, and we do not show prices or star ratings. Check current prices and reviews on the retailer's page.</p>
{DISCLOSURE}
{secs}
<section class="faq"><h2>Frequently asked questions</h2>{faq}</section>
</article>'''
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": t["title"], "description": t["summary"],
           "datePublished": t["published"], "dateModified": t["updated"], "author": {"@type": "Person", "name": CFG["AUTHOR"]},
           "publisher": {"@type": "Organization", "name": SITE}, "mainEntityOfPage": BASE + "/basic-home-toolkit/",
           "image": BASE + "/assets/og/default.png"},
          {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in t["faq"]]}]
    page("/basic-home-toolkit/", t["title"], t["meta"], body, crumbs, ld, "article")


CALC_FORMS = {
    "paint-coverage": '''
<form class="calc" data-calc="paint" onsubmit="return false">
 <div class="grid2">
  <label>Room length (ft)<input type="number" name="len" value="12" min="0" step="0.1" inputmode="decimal"></label>
  <label>Room width (ft)<input type="number" name="wid" value="12" min="0" step="0.1" inputmode="decimal"></label>
  <label>Wall height (ft)<input type="number" name="hgt" value="8" min="0" step="0.1" inputmode="decimal"></label>
  <label>Coats<input type="number" name="coats" value="2" min="1" step="1"></label>
  <label>Doors<input type="number" name="doors" value="1" min="0" step="1"></label>
  <label>Windows<input type="number" name="wins" value="2" min="0" step="1"></label>
  <label>Coverage per gallon (sq ft)<input type="number" name="cov" value="350" min="50" step="10"></label>
  <label class="check"><input type="checkbox" name="ceil"> Include the ceiling</label>
 </div>
 <output class="result" aria-live="polite"></output>
</form>''',
    "tile-flooring": '''
<form class="calc" data-calc="floor" onsubmit="return false">
 <div class="grid2">
  <label>Room length (ft)<input type="number" name="len" value="10" min="0" step="0.1" inputmode="decimal"></label>
  <label>Room width (ft)<input type="number" name="wid" value="12" min="0" step="0.1" inputmode="decimal"></label>
  <label>Extra area, closets or nooks (sq ft)<input type="number" name="extra" value="0" min="0" step="0.5"></label>
  <label>Waste allowance (%)<select name="waste"><option value="5">5% simple straight lay</option><option value="10" selected>10% standard</option><option value="15">15% diagonal or herringbone</option><option value="20">20% many cuts or large tile</option></select></label>
  <label>Coverage per box (sq ft)<input type="number" name="box" value="20" min="1" step="0.01"></label>
  <label>Price per sq ft (optional)<input type="number" name="price" value="" min="0" step="0.01" placeholder="e.g. 2.49"></label>
 </div>
 <output class="result" aria-live="polite"></output>
</form>''',
    "mulch-gravel": '''
<form class="calc" data-calc="mulch" onsubmit="return false">
 <div class="grid2">
  <label>Area length (ft)<input type="number" name="len" value="20" min="0" step="0.1" inputmode="decimal"></label>
  <label>Area width (ft)<input type="number" name="wid" value="4" min="0" step="0.1" inputmode="decimal"></label>
  <label>Depth (inches)<input type="number" name="dep" value="3" min="0.5" step="0.5"></label>
  <label>Material<select name="mat"><option value="0">Mulch or compost</option><option value="1.4" selected>Gravel or crushed stone (about 1.4 tons per cubic yard)</option><option value="1.3">Sand (about 1.3 tons per cubic yard)</option><option value="1.5">River rock (about 1.5 tons per cubic yard)</option></select></label>
  <label>Bag size (cubic feet)<select name="bag"><option value="2" selected>2 cu ft</option><option value="1.5">1.5 cu ft</option><option value="3">3 cu ft</option><option value="0.5">0.5 cu ft</option></select></label>
 </div>
 <output class="result" aria-live="polite"></output>
</form>''',
}

CALC_BODY = {
    "paint-coverage": {
        "answer": "A typical 12 by 12 foot room with 8 foot walls, one door and two windows needs about 2 gallons of paint for two coats, at the common label rate of 350 square feet per gallon.",
        "how": "Wall area is the room perimeter times the wall height. The calculator subtracts about 21 square feet per standard door and 15 square feet per average window, multiplies by the number of coats, and divides by the coverage on your paint can. Labels commonly list 250 to 400 square feet per gallon; rough, porous or freshly patched walls land at the low end. Buy an extra quart for touch-ups.",
        "faq": [
            {"q": "How many square feet does a gallon of paint cover?", "a": "Most interior wall paints list 250 to 400 square feet per gallon per coat. Check the label on the can you are buying and enter that number. Textured or unprimed drywall uses more paint."},
            {"q": "Do I need two coats?", "a": "Plan on two coats for a color change, a dark color, or new drywall. One coat can be enough when you repaint the same color over a clean, sound finish."},
            {"q": "Should I prime first?", "a": "Prime new drywall, drywall patches, stains and glossy surfaces. Primer on patched spots keeps them from showing through as dull patches."},
        ],
        "guides": ["patch-small-drywall-hole", "patch-large-drywall-hole", "fix-drywall-nail-pops"],
    },
    "tile-flooring": {
        "answer": "Multiply the room's length by its width for square feet, add 10 percent for cuts and breakage (15 percent or more for diagonal or herringbone layouts), then divide by the coverage printed on one box and round up.",
        "how": "Measure each rectangle in the room and add them. The calculator adds your waste allowance, then rounds the box count up because stores sell whole boxes. Buy all boxes from the same lot or dye number so the color matches, and keep one spare box for future repairs.",
        "faq": [
            {"q": "How much extra flooring should I buy?", "a": "Ten percent is the usual allowance for a straight layout. Use 15 percent for diagonal or herringbone patterns, and more for rooms with many corners or large-format tile."},
            {"q": "How do I measure an L-shaped room?", "a": "Split it into two rectangles, measure each, and add the results. Enter the second rectangle in the extra area box."},
            {"q": "Does the calculator work for vinyl plank and laminate?", "a": "Yes. Any product sold by the box with a square-foot coverage on the label works the same way."},
        ],
        "guides": ["regrout-tile", "caulk-a-bathtub"],
    },
    "mulch-gravel": {
        "answer": "Multiply length by width for square feet, multiply by depth in inches, and divide by 324 to get cubic yards. A 20 by 4 foot bed at 3 inches deep needs about 0.74 cubic yards, or 10 bags of 2 cubic feet.",
        "how": "One cubic yard is 27 cubic feet, and one inch is 1/12 of a foot, so square feet times inches divided by 324 gives cubic yards. Gravel weight varies by stone and moisture; the calculator uses common estimates of about 1.3 to 1.5 tons per cubic yard. Ask your supplier for their conversion before you order by the ton.",
        "faq": [
            {"q": "How deep should mulch be?", "a": "Two to three inches is the common range for garden beds. Keep mulch a few inches away from tree trunks and house siding."},
            {"q": "How many bags of mulch make a cubic yard?", "a": "A cubic yard is 27 cubic feet, so it takes 13.5 bags of 2 cubic feet each. Round up to 14."},
            {"q": "How much does a cubic yard of gravel weigh?", "a": "Roughly 1.3 to 1.5 tons depending on the stone size and how wet it is. Your supplier can give an exact figure for their material."},
        ],
        "guides": ["clean-gutters", "winterize-outdoor-faucet"],
    },
}


def build_calcs():
    cards = "".join(f'<a class="card" href="/calculators/{x["slug"]}/"><span class="card-cat">Calculator</span><strong>{esc(x["title"])}</strong><span class="card-meta">{esc(x["short"])}</span></a>' for x in CALCS)
    page("/calculators/", "Home Project Calculators", "Free paint, flooring and mulch calculators for planning DIY home projects. No sign-up, works on your phone.",
         f'<h1>Home project calculators</h1><p class="lead">Quick estimates so you buy the right amount the first time. Everything runs in your browser.</p><div class="cards">{cards}</div>',
         [("Home", "/"), ("Calculators", "/calculators/")],
         [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Home project calculators", "url": BASE + "/calculators/"}])
    for x in CALCS:
        b = CALC_BODY[x["slug"]]
        faq = "".join(f'<details><summary><h3>{esc(f["q"])}</h3></summary><p>{esc(f["a"])}</p></details>' for f in b["faq"])
        rel = "".join(guide_card(G[s]) for s in b["guides"] if s in G)
        body = f'''
<h1>{esc(x["title"])}</h1>
<div class="answer"><p><strong>Short answer:</strong> {esc(b["answer"])}</p></div>
{CALC_FORMS[x["slug"]]}
<section><h2>How is this calculated?</h2><p>{esc(b["how"])}</p></section>
{ad_slot("mid-content")}
<section class="faq"><h2>Frequently asked questions</h2>{faq}</section>
<section><h2>Related guides</h2><div class="cards">{rel}</div></section>'''
        ld = [{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": x["title"], "applicationCategory": "UtilitiesApplication",
               "operatingSystem": "Any (web browser)", "url": BASE + f'/calculators/{x["slug"]}/', "description": x["desc"],
               "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
              {"@context": "https://schema.org", "@type": "Article", "headline": x["title"], "description": x["desc"],
               "datePublished": "2026-11-09", "dateModified": TODAY, "author": {"@type": "Person", "name": CFG["AUTHOR"]},
               "publisher": {"@type": "Organization", "name": SITE}, "image": BASE + "/assets/og/default.png"},
              {"@context": "https://schema.org", "@type": "FAQPage",
               "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in b["faq"]]}]
        page(f'/calculators/{x["slug"]}/', x["title"], x["desc"], body,
             [("Home", "/"), ("Calculators", "/calculators/"), (x["title"], f'/calculators/{x["slug"]}/')], ld,
             extra_head='<script src="/assets/calc.js" defer></script>\n')


def build_news():
    brand = CFG["NEWS_BRAND"]
    lead, rest = NEWS[0], NEWS[1:]
    body = f'''
<header class="news-head"><p class="eyebrow">{esc(brand)}</p><h1>Home repair news: recalls, rebates and safety alerts</h1>
<p class="lead">Short, sourced updates for people who fix things at home. Every item links to the primary source.</p></header>
<a class="lead-story" href="/news/{lead["slug"]}/"><span class="card-cat">{esc(lead["tags"][0])}</span><h2>{esc(lead["title"])}</h2><p>{esc(lead["summary"])}</p><span class="card-meta">{fmt_date(lead["date"])}</span></a>
<div class="cards">{"".join(news_card(n) for n in rest)}</div>
<p class="muted small">Get updates: <a href="/news/feed.json">JSON Feed</a> or <a href="/feed.xml">RSS</a>. Check any product you own at the <a href="https://www.cpsc.gov/Recalls" target="_blank" rel="noopener">CPSC recalls list</a>.</p>'''
    page("/news/", f"Home Repair News, Recalls and Rebates", "Sourced home repair news: CPSC product recalls for tools, ladders and appliances, energy rebate updates and home improvement trends.",
         body, [("Home", "/"), ("News", "/news/")],
         [{"@context": "https://schema.org", "@type": "CollectionPage", "name": brand, "url": BASE + "/news/"}])
    for n in NEWS:
        paras = "".join(f"<p>{p}</p>" for p in n["body"])
        rel = [G[s] for s in n.get("related", []) if s in G]
        rel_html = ('<section><h2>Related guides</h2><div class="cards">' + "".join(guide_card(r) for r in rel) + "</div></section>") if rel else ""
        quote = f'<blockquote><p>"{esc(n["quote"]["text"])}"</p><cite>{esc(n["quote"]["by"])}</cite></blockquote>' if n.get("quote") else ""
        body = f'''
<article class="guide news-art">
<p class="eyebrow">{esc(brand)} &middot; {esc(", ".join(n["tags"]))}</p>
<h1>{esc(n["title"])}</h1>
<p class="muted">Published {fmt_date(n["date"])} &middot; Source: <a href="{esc(n["source_url"])}" target="_blank" rel="noopener">{esc(n["source_name"])}</a></p>
<div class="answer"><p><strong>The short version:</strong> {esc(n["summary"])}</p></div>
<h2>What happened</h2>{paras}
{quote}
<h2>Why it matters if you fix things at home</h2><p>{n["why"]}</p>
<p><a class="btn" href="{esc(n["source_url"])}" target="_blank" rel="noopener">Read the full notice at {esc(n["source_name"])}</a></p>
{rel_html}
</article>'''
        ld = [{"@context": "https://schema.org", "@type": "NewsArticle", "headline": n["title"], "description": n["summary"],
               "datePublished": n["date"], "dateModified": n.get("updated", n["date"]),
               "author": {"@type": "Person", "name": CFG["AUTHOR"]}, "publisher": {"@type": "Organization", "name": SITE},
               "mainEntityOfPage": BASE + f'/news/{n["slug"]}/', "image": BASE + n.get("image", "/assets/og/news.png"),
               "isBasedOn": n["source_url"]}]
        page(f'/news/{n["slug"]}/', n["title"], n["summary"][:155], body,
             [("Home", "/"), ("News", "/news/"), (n["title"], f'/news/{n["slug"]}/')], ld, "article", n.get("image", "/assets/og/news.png"))
    feed = {
        "version": "https://jsonfeed.org/version/1.1", "title": brand, "home_page_url": BASE + "/news/",
        "feed_url": BASE + "/news/feed.json", "description": "Home repair news: recalls, rebates and safety alerts from " + SITE,
        "language": "en-US", "authors": [{"name": CFG["AUTHOR"]}], "icon": BASE + "/assets/og/news.png",
        "items": [{"id": BASE + f'/news/{n["slug"]}/', "url": BASE + f'/news/{n["slug"]}/', "title": n["title"],
                   "summary": n["summary"], "content_text": n["summary"], "date_published": n["date"] + "T12:00:00-06:00",
                   "image": BASE + n.get("image", "/assets/og/news.png"), "tags": n["tags"], "external_url": n["source_url"]}
                  for n in NEWS],
    }
    (ROOT / "news" / "feed.json").write_text(json.dumps(feed, indent=1, ensure_ascii=False), encoding="utf-8")


def build_home():
    cats = "".join(f'<a class="cat" href="/{c["slug"]}/">{icon(c["slug"])}<strong>{esc(c["name"])}</strong><span>{sum(1 for g in GUIDES if g["category"]==c["slug"])} guides</span></a>' for c in CATS)
    popular = [G[s] for s in ["fix-running-toilet", "fix-leaky-faucet", "unclog-sink-drain", "reset-tripped-gfci", "patch-small-drywall-hole", "fix-garbage-disposal-jam", "water-heater-not-hot", "fix-squeaky-door"] if s in G]
    body = f'''
<section class="hero"><p class="eyebrow">DIY home repair, done safely</p><h1>Fix common home problems yourself, safely</h1>
<p class="lead">Step-by-step repair guides with the tools you need, the steps in order, and a clear line on when to call a pro. Based on manufacturer instructions and published safety guidance.</p>
<form class="search" action="/guides/" role="search"><label class="sr" for="q">Search guides</label><input id="q" name="q" type="search" placeholder="Search guides: toilet, faucet, outlet..."><button type="submit">Search</button></form></section>
<section class="band"><h2>Browse by area of the house</h2><div class="cats">{cats}</div></section>
<section><h2>Most-needed repairs</h2><div class="cards">{"".join(guide_card(g) for g in popular)}</div></section>
<section class="two band"><div><h2>Calculators</h2><ul class="plain">{"".join(f'<li><a href="/calculators/{x["slug"]}/">{esc(x["title"])}</a></li>' for x in CALCS)}</ul>
<h2>Start a toolkit</h2><p>Not sure what to buy? The <a href="/basic-home-toolkit/">basic home toolkit</a> covers the dozen or so tools that handle most of these repairs.</p></div>
<div><h2>Latest news</h2><ul class="plain">{"".join(f'<li><a href="/news/{n["slug"]}/">{esc(n["title"])}</a> <span class="muted small">{fmt_date(n["date"])}</span></li>' for n in NEWS[:5])}</ul><p><a href="/news/">All news</a></p></div></section>'''
    page("/", f"{SITE}: DIY Home Repair Guides", "Plain-English DIY home repair guides: running toilets, leaky faucets, clogged drains, drywall holes, GFCI outlets and more, with tools, steps and safety notes.",
         body, None, [{"@context": "https://schema.org", "@type": "Organization", "name": SITE, "url": BASE + "/", "logo": BASE + "/assets/favicon.svg"}])


def build_all_guides():
    groups = ""
    for c in CATS:
        gs = [g for g in GUIDES if g["category"] == c["slug"]]
        groups += f'<section><h2><a href="/{c["slug"]}/">{esc(c["name"])}</a></h2><div class="cards">{"".join(guide_card(g) for g in gs)}</div></section>'
    index = [{"t": g["title"], "u": f'/guides/{g["slug"]}/', "k": " ".join([g["summary"], " ".join(g.get("keywords", []))])} for g in GUIDES]
    body = f'''<h1>All home repair guides</h1>
<p class="lead">{len(GUIDES)} step-by-step guides, grouped by area of the house.</p>
<div class="search"><label class="sr" for="gq">Filter guides</label><input id="gq" type="search" placeholder="Filter guides..." autocomplete="off"></div>
<ul id="gresults" class="plain" hidden></ul>
<script type="application/json" id="gindex">{j(index)}</script>
{groups}'''
    page("/guides/", "All DIY Home Repair Guides", f"Browse all {len(GUIDES)} DIY home repair guides: plumbing, electrical, walls, doors and windows, appliances and outdoor fixes.",
         body, [("Home", "/"), ("All guides", "/guides/")],
         [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "All guides", "url": BASE + "/guides/"}])


def build_static_pages():
    for p in PAGES:
        body = f'<article class="guide prose"><h1>{esc(p["title"])}</h1>{p["html"]}'
        if p["slug"] == "contact":
            if CFG.get("CONTACT_FORM_ID"):
                body += '<div class="hs-form-slot" id="hs-contact" data-hs-form="contact"></div>'
            elif CFG.get("CONTACT_EMAIL"):
                body += f'<p><a class="btn" href="mailto:{esc(CFG["CONTACT_EMAIL"])}">Email {esc(CFG["CONTACT_EMAIL"])}</a></p>'
            else:
                body += '<p class="muted">The contact form is being set up. Please check back shortly.</p>'
        body += f'<p class="muted small">Last updated {fmt_date(p["updated"])}.</p></article>'
        page(f'/{p["slug"]}/', p["title"], p["meta"], body, [("Home", "/"), (p["title"], f'/{p["slug"]}/')],
             [{"@context": "https://schema.org", "@type": "WebPage", "name": p["title"], "url": BASE + f'/{p["slug"]}/'}])


def build_404():
    page("/404.html", "Page not found", "That page does not exist. Browse all home repair guides instead.",
         '<h1>Page not found</h1><p>That page does not exist or has moved. Try <a href="/guides/">all guides</a> or the <a href="/">home page</a>.</p>')
    SITEMAP.remove("/404.html")


def build_feeds():
    urls = "".join(f"<url><loc>{BASE}{p}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in SITEMAP)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    items = []
    for n in NEWS:
        items.append((n["date"], n["title"], f'/news/{n["slug"]}/', n["summary"]))
    for g in GUIDES:
        items.append((g.get("published", TODAY), g["title"], f'/guides/{g["slug"]}/', g["summary"]))
    items.sort(reverse=True)
    def rfc(d):
        return datetime.datetime.fromisoformat(d + "T12:00:00").strftime("%a, %d %b %Y 12:00:00 -0600")
    rss_items = "".join(f"<item><title>{esc(t)}</title><link>{BASE}{u}</link><guid>{BASE}{u}</guid><pubDate>{rfc(d)}</pubDate><description>{esc(s)}</description></item>\n" for d, t, u, s in items[:50])
    (ROOT / "feed.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{esc(SITE)}</title><link>{BASE}/</link><description>{esc(CFG["SITE_TAGLINE"])}</description><language>en-us</language>\n{rss_items}</channel></rss>\n', encoding="utf-8")
    llms = [f"# {SITE}", "", f"> {CFG['SITE_TAGLINE']} at {BASE}. Answer-first DIY repair guides with tools, steps, safety notes and when to call a licensed pro. Sources are linked on every guide.", ""]
    for c in CATS:
        llms.append(f"## {c['name']}")
        for g in GUIDES:
            if g["category"] == c["slug"]:
                llms.append(f"- [{g['title']}]({BASE}/guides/{g['slug']}/): {g['summary']}")
        llms.append("")
    llms.append("## Calculators")
    llms += [f"- [{x['title']}]({BASE}/calculators/{x['slug']}/): {x['desc']}" for x in CALCS]
    llms += ["", "## Other", f"- [Basic home toolkit]({BASE}/basic-home-toolkit/): {TOOLKIT['summary']}",
             f"- [News]({BASE}/news/): recalls, rebates and safety alerts. JSON Feed: {BASE}/news/feed.json", ""]
    (ROOT / "llms.txt").write_text("\n".join(llms), encoding="utf-8")
    (ROOT / "CNAME").write_text("homerepair.samcbarth.com\n", encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    cfg_js = {k: v for k, v in CFG.items() if not k.startswith("_")}
    (ROOT / "assets" / "config.js").write_text("/* Generated from config.json by build.py. Edit config.json, not this file. */\nwindow.SITE_CONFIG = " + json.dumps(cfg_js, indent=1) + ";\n", encoding="utf-8")


def check():
    """Basic content checks: banned characters/words, missing related links."""
    bad = []
    banned = re.compile(r"—|\b(unlock|leverage|supercharge|transform|delve|harness|empower)\w*", re.I)
    for p in list(C.rglob("*.json")):
        t = p.read_text(encoding="utf-8")
        for m in banned.finditer(t):
            bad.append(f"{p.name}: '{m.group(0)}'")
    for g in GUIDES:
        for r in g.get("related", []):
            if r not in G:
                bad.append(f"{g['slug']}: related '{r}' missing")
        if g["category"] not in CAT:
            bad.append(f"{g['slug']}: bad category")
    for n in NEWS:
        for r in n.get("related", []):
            if r not in G:
                bad.append(f"news {n['slug']}: related '{r}' missing")
    if bad:
        print("CONTENT WARNINGS:\n  " + "\n  ".join(bad))


if __name__ == "__main__":
    check()
    build_home()
    build_all_guides()
    for c in CATS:
        build_category(c)
    for g in GUIDES:
        build_guide(g)
    build_toolkit()
    build_calcs()
    build_news()
    build_static_pages()
    build_404()
    build_feeds()
    print(f"Built {len(SITEMAP)} pages: {len(GUIDES)} guides, {len(CATS)} hubs, {len(CALCS)} calculators, {len(NEWS)} news.")
