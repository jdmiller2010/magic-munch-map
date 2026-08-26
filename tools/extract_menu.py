#!/usr/bin/env python3
"""Turn a Disney Parks Blog Foodie Guide into menu.js for Magic Munch Map.

The guide nests like this, in document order:

    <h2>            section, e.g. "Delectable Delights at Disneyland Park"
    <p><strong>     venue,   e.g. "Carnation Cafe" - nested three deep, so the
                    check compares the outermost strong's text to the whole
                    paragraph's text rather than counting tags
    <p>...Location: land,    e.g. "Main Street, U.S.A."
    <h4>            dish name (repeated for the lightbox, so deduped)
    <img alt>       "Dish name: description" - the richest field on the page
    <li>            dish, used for drink lists: "Name: ingredients (New)"

Usage:  python3 tools/extract_menu.py <url> [--season "Halloween 2026"] > menu.js
"""
import re, sys, html, json, urllib.request, argparse

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

SECTION_PARK = [
    ("disneyland park", "dl"), ("california adventure", "dca"),
    ("downtown disney", "dtd"), ("hotels", "dtd"),
    ("disneyland resort", ""),          # "throughout the resort" - no single park
]

def pick_image(tag):
    """Smallest srcset candidate at least 600px wide, else the plain src.

    The inline src is the 1920px original; hotlinking that per card would be
    brutal on phone data in a park with bad signal.
    """
    best = None
    m = re.search(r'srcset="([^"]+)"', tag)
    if m:
        for part in m.group(1).split(","):
            bits = part.strip().split()
            if len(bits) == 2 and bits[1].endswith("w"):
                try:
                    w = int(bits[1][:-1])
                except ValueError:
                    continue
                if w >= 600 and (best is None or w < best[0]):
                    best = (w, bits[0])
    if best:
        return best[1]
    m = re.search(r'\ssrc="([^"]+)"', tag)
    return m.group(1) if m else ""


def strip(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment or "")).replace("\xa0", " ").strip()

def park_for(section):
    low = (section or "").lower()
    for needle, code in SECTION_PARK:
        if needle in low:
            return code
    return ""

def parse(body, source, season):
    # one ordered pass over just the tags that carry meaning
    # The post ships unclosed <p> tags, so a lazy <p>.*?</p> happily spans
    # thousands of characters and swallows the images inside. These patterns are
    # unrolled so a paragraph can never cross an <img>: the broken paragraphs
    # simply fail to match, which is fine, and their images stay visible.
    inner = r"[^<]*(?:<(?!img[\s>])(?!/%s>)[^>]*>[^<]*)*"
    token = re.compile(
        r"(?P<img><img[^>]*\salt=\"(?P<alt>[^\"]*)\"[^>]*>)"
        r"|<h2[^>]*>(?P<h2>" + (inner % "h2") + r")</h2>"
        r"|<h4[^>]*>(?P<h4>" + (inner % "h4") + r")</h4>"
        r"|<p[^>]*>(?P<p>" + (inner % "p") + r")</p>"
        r"|<li[^>]*>(?P<li>" + (inner % "li") + r")</li>", re.S)

    section = venue = land = avail = ""
    items, seen = [], set()

    def add(name, desc, image=""):
        name = re.sub(r"\s+", " ", name).strip(" :–-")
        if not name or not venue:
            return
        new = bool(re.search(r"\(new\)\s*$", name, re.I))
        name = re.sub(r"\s*\(new\)\s*$", "", name, flags=re.I).strip()
        if len(name) < 3 or len(name) > 90:
            return
        key = (venue.lower(), name.lower())
        if key in seen:
            return
        seen.add(key)
        items.append({
            "dish": name, "venue": venue, "land": land,
            "park": park_for(section), "season": season,
            "desc": re.sub(r"\s+", " ", desc or "").strip()[:400],
            "avail": avail, "new": new, "image": image, "source": source,
        })

    for m in token.finditer(body):
        if m.group("h2"):
            section, venue, land, avail = strip(m.group("h2")), "", "", ""
        elif m.group("p"):
            raw, text = m.group("p"), strip(m.group("p"))
            if not text:
                continue
            loc = re.search(r"Location\s*:\s*(.+)$", text, re.S)
            if loc:
                land = re.sub(r"\s+", " ", loc.group(1)).strip()
                a = re.search(r"\((Available[^)]*)\)", text, re.I)
                if a:
                    avail = a.group(1).strip()
                continue
            # A venue heading is a paragraph whose whole visible text sits
            # inside one <strong> run. Greedy .* grabs the outermost pair, so
            # the triple nesting in the source does not matter.
            bold = re.search(r"<strong[^>]*>(.*)</strong>", raw, re.S)
            if bold and strip(bold.group(1)) == text and 2 < len(text) < 80:
                venue, land, avail = text, "", ""
        elif m.group("h4"):
            add(strip(m.group("h4")), "")
        elif m.group("img") is not None:
            alt = html.unescape(m.group("alt")).strip()
            if ":" in alt:
                name, desc = alt.split(":", 1)
                add(name, desc, pick_image(m.group("img")))
        elif m.group("li"):
            text = strip(m.group("li"))
            if ":" in text and 10 < len(text) < 300:
                name, desc = text.split(":", 1)
                add(name, desc)
    return items

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--season", default="")
    ap.add_argument("--json", action="store_true", help="emit raw JSON instead of menu.js")
    a = ap.parse_args()

    page = urllib.request.urlopen(urllib.request.Request(a.url, headers=UA), timeout=60)
    doc = page.read().decode("utf-8", "replace")
    # No <article> on these posts; <main> is the reliable wrapper, and scoping
    # matters because the page chrome is full of unrelated images and headings.
    m = (re.search(r"<main[^>]*>(.*)</main>", doc, re.S)
         or re.search(r'entry-content[^>]*>(.*)', doc, re.S))
    items = parse(m.group(1) if m else doc, a.url, a.season)

    if a.json:
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return
    print("// Generated by tools/extract_menu.py - do not edit by hand.")
    print("// Source: %s" % a.url)
    print("window.MENU = %s;" % json.dumps(items, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
