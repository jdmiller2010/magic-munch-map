#!/usr/bin/env python3
"""Refresh both data sources for Magic Munch Map, writing dining.js.

Two sources, both refreshed in one run because they interlock: OpenStreetMap
knows where every venue physically is, and Disney knows what each one serves.

  OpenStreetMap (Overpass)  ->  venue positions, scoped to each zone's polygon
  disneyland.disney.go.com  ->  full menus, prices, hours, price range

The Disney endpoints send no CORS headers, so the browser cannot call them and
this has to run offline and commit its output. The Overpass half *is*
browser-callable - the app's own "Resync map data" button does it live - but
running it here too keeps one command as the way to refresh everything.

Usage:  python3 tools/refresh_data.py > dining.js
        python3 tools/refresh_data.py --json          # inspect without writing
        python3 tools/refresh_data.py --limit 5       # quick smoke test
"""
import argparse, json, math, re, sys, time, urllib.parse, urllib.request, unicodedata
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
JSON_UA = dict(UA, Accept="application/json, text/plain, */*")
# Overpass rejects the browser user-agent with a 406, and asks callers to
# identify themselves anyway.
OVERPASS_UA = {"User-Agent": "magic-munch-map/1.0 (https://mmm.molendino.com)"}

# The main instance has been unreachable from some networks; try mirrors in turn.
OVERPASS = ["https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://overpass.private.coffee/api/interpreter"]
NOMINATIM = "https://nominatim.openstreetmap.org/search"
BOUNDARIES = [("dl", "Disneyland Park, Anaheim"),
              ("dca", "Disney California Adventure, Anaheim"),
              ("dtd", "Downtown Disney, Anaheim")]
AMENITY = "^(restaurant|fast_food|cafe|ice_cream|bar|pub|biergarten)$"
ZONES = [
    ("dl",  '["tourism"="theme_park"]["name"="Disneyland"]'),
    ("dca", '["tourism"="theme_park"]["name"="Disney California Adventure"]'),
    ("dtd", '["landuse"="retail"]["name"="Downtown Disney"]'),
]
MENU_API = "https://disneyland.disney.go.com/dining/dinemenu/api/menu?searchTerm=%s&language=en-us"

# Disney's meal period labels -> the app's meal keys. Only the single-word
# labels used to map, which left "Lunch And Dinner" - the largest bucket by
# far - with no meal at all and unreachable by the filter. The raw label is
# kept in `period` regardless, and the app widens it further (a Snack answers
# to both AM and PM, which a single key cannot express).
MEAL = {"breakfast": "breakfast", "lunch": "lunch", "dinner": "dinner",
        "brunch": "lunch", "dessert": "dessert",
        "lunch and dinner": "lunch", "late night dining": "dinner"}


def get(url, headers=UA, timeout=45):
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout).read()


def fold(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def overpass_venues(log):
    out = []
    for code, selector in ZONES:
        q = ('[out:json][timeout:60];area%s->.p;'
             '(node(area.p)["amenity"~"%s"]["name"];'
             ' way(area.p)["amenity"~"%s"]["name"];);out center tags;' % (selector, AMENITY, AMENITY))
        body = urllib.parse.urlencode({"data": q}).encode()
        data = None
        for endpoint in OVERPASS:
            try:
                req = urllib.request.Request(endpoint, data=body, headers=OVERPASS_UA)
                data = json.loads(urllib.request.urlopen(req, timeout=90).read().decode())
                break
            except Exception as e:
                log("  %s unreachable (%s)" % (endpoint.split("/")[2], getattr(e, "code", type(e).__name__)))
        if data is None:
            raise SystemExit("every Overpass endpoint failed")
        n = 0
        for e in data.get("elements", []):
            t = e.get("tags") or {}
            lat = e.get("lat", (e.get("center") or {}).get("lat"))
            lon = e.get("lon", (e.get("center") or {}).get("lon"))
            if not t.get("name") or lat is None:
                continue
            v = {"name": t["name"], "lat": round(lat, 5), "lng": round(lon, 5), "park": code}
            if t.get("amenity"):        v["kind"] = t["amenity"]
            if t.get("cuisine"):        v["cuisine"] = t["cuisine"]
            if t.get("website"):        v["website"] = t["website"]
            if t.get("mobile_ordering") == "yes":  v["mobile"] = True
            if t.get("outdoor_seating") == "yes":  v["outdoor"] = True
            out.append(v); n += 1
        log("  %-4s %3d venues" % (code, n))
        time.sleep(1)
    seen, dedup = set(), []
    for v in out:
        key = (v["park"], fold(v["name"]))
        if key not in seen:
            seen.add(key); dedup.append(v)
    return dedup


def rdp(pts, eps):
    """Douglas-Peucker. Park outlines run to hundreds of points; a few dozen
    draw identically at the zooms this map uses."""
    if len(pts) < 3:
        return pts
    def gap(p, a, b):
        if a == b:
            return math.hypot(p[0] - a[0], p[1] - a[1])
        span = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        t = max(0, min(1, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / span))
        return math.hypot(p[0] - (a[0] + t * (b[0] - a[0])), p[1] - (a[1] + t * (b[1] - a[1])))
    far, idx = 0, 0
    for i in range(1, len(pts) - 1):
        d = gap(pts[i], pts[0], pts[-1])
        if d > far:
            far, idx = d, i
    if far > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def boundaries(log):
    """Park outlines, from Nominatim rather than Overpass.

    Overpass has been flaky here, and Nominatim hands back polygon geometry
    directly. Its policy caps this at one request a second, which is why the
    loop sleeps - three requests, once per refresh.
    """
    out = {}
    for code, query in BOUNDARIES:
        url = NOMINATIM + "?" + urllib.parse.urlencode(
            {"q": query, "format": "jsonv2", "polygon_geojson": 1, "limit": 3, "countrycodes": "us"})
        try:
            results = json.loads(get(url, OVERPASS_UA, 40).decode())
        except Exception as e:
            log("  %-4s boundary failed (%s)" % (code, getattr(e, "code", type(e).__name__)))
            time.sleep(1.2)
            continue
        for r in results:
            g = r.get("geojson") or {}
            if g.get("type") == "Polygon":
                rings = [g["coordinates"][0]]
            elif g.get("type") == "MultiPolygon":
                rings = [poly[0] for poly in g["coordinates"]]
            else:
                continue
            rings.sort(key=len, reverse=True)
            simple = [rdp(r2, 0.00004) for r2 in rings]          # ~4m tolerance
            out[code] = [[[round(pt[1], 5), round(pt[0], 5)] for pt in r2] for r2 in simple]
            log("  %-4s %d ring(s), %d points" % (code, len(simple), sum(len(r2) for r2 in simple)))
            break
        time.sleep(1.2)
    return out


def slug_for(v):
    """Disney's menu API keys off the slug in the venue's own dining URL."""
    m = re.search(r"disney\.go\.com/dining/[^/]+/([^/?#]+)", v.get("website", "") or "")
    if m:
        return m.group(1)
    return re.sub(r"[^a-z0-9]+", "-", fold(v["name"])).strip("-") or None


def ld_json(slug, park_slug):
    url = "https://disneyland.disney.go.com/dining/%s/%s/" % (park_slug, slug)
    m = re.search(rb'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                  get(url), re.S)
    return json.loads(m.group(1).decode("utf-8", "replace")) if m else {}


def parse_hours(spec):
    out = []
    for s in spec or []:
        for day in (s.get("dayOfWeek") or []):
            out.append({"day": day[:3], "open": s.get("opens", ""), "close": s.get("closes", ""),
                        "note": s.get("description", "")})
    return out


def disney_for(v, log):
    """Menu items plus venue detail for one venue. Returns (detail, items)."""
    slug = slug_for(v)
    if not slug:
        return None, []
    detail, items = {"name": v["name"], "slug": slug, "park": v["park"]}, []

    try:
        j = json.loads(get(MENU_API % slug, JSON_UA, 30).decode())
    except Exception as e:
        log("    %-32s menu: %s" % (slug[:31], getattr(e, "code", type(e).__name__)))
        return detail, []

    # "Disneyland Park, New Orleans Square" - park and land, straight from Disney
    loc = j.get("location") or ""
    if "," in loc:
        detail["land"] = loc.split(",", 1)[1].strip()

    for period in j.get("mealPeriods") or []:
        label = period.get("label") or period.get("name") or ""
        meal = MEAL.get(label.lower(), "")
        for group in period.get("groups") or []:
            for it in group.get("items") or []:
                title = (it.get("title") or "").strip()
                if not title:
                    continue
                price = ""
                for p in it.get("prices") or []:
                    if p.get("withoutTax") is not None:
                        price = "$%s" % p["withoutTax"]; break
                items.append({
                    "dish": title, "venue": v["name"], "park": v["park"],
                    "land": detail.get("land", ""), "meal": meal,
                    "period": label, "group": group.get("name", ""),
                    "price": price, "desc": (it.get("description") or "").strip()[:400],
                    "season": "", "image": "",
                    "source": "https://disneyland.disney.go.com/dining/dinemenu/",
                })

    # A dish can appear in a prix-fixe group with no price and again a la carte
    # with one. Keep the priced copy - that is the one worth knowing about.
    best = {}
    for it in items:
        key = (fold(it["dish"]), it["period"])
        if key not in best or (it["price"] and not best[key]["price"]):
            best[key] = it
    items = list(best.values())

    park_slug = "disneyland" if v["park"] == "dl" else "disney-california-adventure"
    try:
        d = ld_json(slug, park_slug)
        if d.get("priceRange"):          detail["price"] = d["priceRange"]
        if d.get("servesCuisine"):       detail["serves"] = d["servesCuisine"]
        if d.get("acceptsReservations") is not None:
            detail["reservations"] = bool(d["acceptsReservations"])
        hrs = parse_hours(d.get("openingHoursSpecification"))
        if hrs:                          detail["hours"] = hrs
        if d.get("url"):                 detail["url"] = d["url"].replace("http://", "https://")
    except Exception:
        pass                              # hours are a bonus, not a requirement
    return detail, items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--delay", type=float, default=0.4)
    a = ap.parse_args()
    log = lambda m: print(m, file=sys.stderr)

    log("OpenStreetMap:")
    venues = overpass_venues(log)
    log("  %d venues total" % len(venues))
    log("Park boundaries:")
    bounds = boundaries(log)
    log("")

    targets = [v for v in venues if v["park"] in ("dl", "dca")]
    if a.limit:
        targets = targets[:a.limit]
    log("Disney dining (%d venues):" % len(targets))

    details, items, hit = [], [], 0
    for i, v in enumerate(targets, 1):
        detail, got = disney_for(v, log)
        if detail:
            details.append(detail)
        if got:
            hit += 1
            items.extend(got)
        if i % 10 == 0:
            log("  %3d/%d  %d items so far" % (i, len(targets), len(items)))
        time.sleep(a.delay)
    log("  %d/%d venues had a menu, %d items\n" % (hit, len(targets), len(items)))

    # Four thousand items is a lot to parse on a phone, so empty and constant
    # fields are dropped and the JSON is emitted compact. Roughly 1.7MB -> 1MB,
    # and 82KB over the wire once GitHub Pages gzips it.
    for row in items + details + venues:
        for k in [k for k, v in row.items() if v in ("", None, False) or k == "source"]:
            del row[k]

    payload = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "itemSource": "https://disneyland.disney.go.com/dining/dinemenu/",
               "venues": venues, "bounds": bounds, "details": details, "items": items}
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print("// Generated by tools/refresh_data.py - do not edit by hand.")
        print("// OpenStreetMap positions (ODbL) + disneyland.disney.go.com menus.")
        print("window.DINING = %s;" % json.dumps(payload, ensure_ascii=False,
                                                 separators=(",", ":")))


if __name__ == "__main__":
    main()
