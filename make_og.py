#!/usr/bin/env python3
"""Generate 1200x630 Open Graph cards into assets/og/. Run once (or after renaming categories)."""
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "assets" / "og"
OUT.mkdir(parents=True, exist_ok=True)
CARDS = {
    "default": ("Fix It Notes", "DIY home repair guides"),
    "plumbing": ("Plumbing", "Toilets, faucets, drains, water heaters"),
    "electrical": ("Electrical", "Breakers, GFCIs, switches, outlets"),
    "walls": ("Walls and Tile", "Drywall, caulk, grout"),
    "doors-windows": ("Doors and Windows", "Squeaks, sticking, latches, drafts"),
    "appliances": ("Appliances", "Disposals, dishwashers, fridges, dryers"),
    "outdoor": ("Outdoor", "Gutters, spigots, winter prep"),
    "news": ("Fix It Notes Bulletin", "Recalls, rebates and safety alerts"),
}


def font(size, bold=False):
    for name in (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


for slug, (title, sub) in CARDS.items():
    im = Image.new("RGB", (1200, 630), "#1f5f8b")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 560, 1200, 630], fill="#c2410c")
    d.text((80, 200), title, font=font(96, True), fill="white")
    d.text((80, 330), sub, font=font(48), fill="#dbeafe")
    d.text((80, 575), "homerepair.samcbarth.com", font=font(34, True), fill="white")
    im.save(OUT / f"{slug}.png", optimize=True)
print("ok", len(CARDS))
