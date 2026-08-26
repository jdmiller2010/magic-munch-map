# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Magic Munch Map — a zero-build web app: a Leaflet map of **food only** across Disneyland and California Adventure. Rides, shows, and shops were removed deliberately: there is one kind of place, so records carry no `type` and there is no category filter. Everything — markup, CSS, and app logic — lives in [index.html](index.html). There is no seed data file; the list starts empty. There is no package.json, no bundler, no test suite, and no dependencies installed locally; Leaflet 1.9.4 and Google Fonts load from CDNs at runtime. See [README.md](README.md) for hosting and data-entry workflow.

## Running it

Open [index.html](index.html) directly — `file://` works, since the Firebase compat SDK loads as classic scripts rather than modules. A local server behaves identically if you prefer one:

```
python3 -m http.server 8000    # then open http://localhost:8000
```

There is nothing to build, lint, or test. Verify changes by loading the page and exercising the UI.

## Data flow

Place data has two tiers:

1. **`localStorage["magicMunchMap.v1"]`** — per-browser edits, read by `load()` (falling back to the pre-rename `parkFoodMap.v1` key). Every mutation calls `save()` immediately. Signed out, this is the entire store, and a fresh browser starts empty.
2. **Firestore** — see below. Signed in, the snapshot replaces the array outright and `localStorage` is left untouched.

**Copy backup** serializes the current list to JSON on the clipboard. It is a one-way snapshot: nothing imports it back.

A place record: `{ id, name, park: "dl"|"dca", land, meal, date, lat, lng, must, note, tried, visited, rating, verdict, ord }`.

- `lat`/`lng` are **optional** — a place can sit in the list with no pin and get one later via `armPlacement()`. Anything touching coordinates goes through `hasCoords(p)` first: `drawMarkers` filters on it, `focus()` bails on it.
- `meal` is `breakfast|am|lunch|pm|dinner` or `""`, ordered by `MEAL_ORDER` **chronologically** (AM snack between breakfast and lunch), which is how the timeline lays out a day.
- `date` (planned) and `visited` (actual) are ISO `YYYY-MM-DD`, sortable as plain strings. `fmtDate` builds a **local** `Date` from explicit y/m/d parts — handing the string to `new Date()` parses as UTC and renders the previous day anywhere west of Greenwich.
- `note` is written before going; `verdict` is written after. `rating` is 0–5, where 0 means unrated, and tapping the current score clears it back to 0.

`ord` controls list grouping order. It exists because Firestore returns documents unordered and a multi-field `orderBy` would require a composite index, so the snapshot handler sorts client-side on `ord` instead. New pins get `nextOrd()`, one past the current maximum.

### Cloud sync

A fourth, optional tier sits on top, in the cloud block at the end of the script. It is inert unless `window.FIREBASE_CONFIG` is non-null *and* the Firebase SDK loaded, both checked by `configured()`. When a user signs in:

- `startWatch()` subscribes to the `places` collection and **`onSnapshot` becomes the owner of the `places` array** — it replaces the array wholesale and calls `render()`. Local mutation is still applied optimistically first; the snapshot echo reconciles it, and because the array is replaced rather than appended to, that cannot duplicate.
- `persist(p, only)` takes an optional field list and writes with `{merge:true}`, so each action sends only what it touched: starring writes `{must}`, a drag writes `{lat,lng}`, the sheet writes its own fields. Two people editing one place then collide only if they change the *same field*. Omitting `only` writes the whole document — right for a new place, wrong for a targeted edit.
- Every mutation goes through `persist(p)` / `persistDelete(id)`, which write a **single document** in cloud mode and fall back to `save()` (whole-array localStorage) when signed out. Never call `save()` directly from a mutation site — in cloud mode that would write a stale localStorage shadow that resurfaces after sign-out.
- Firestore's offline cache means writes succeed with no network; their promises simply don't settle until the server acks, so error handlers must not assume failure from silence.
- A `permission-denied` snapshot error sets `cloud.on = false`, dropping the session back to local mode. Without that the account is signed in but unauthorized, `persist()` still routes to Firestore, and every edit is written nowhere — rejected by the rules and skipped by the localStorage fallback.

The Firebase SDK is loaded as **compat** builds, deliberately: they are classic scripts, which keeps the ES5 dialect and the `file://` workflow working. The modular SDK is ES-module-only and would break both.

## Rendering model

Four views — `list`, `map`, `time`, `tried` — switched by `setView(v)`, which stamps `data-view` on `<body>` (CSS handles showing and hiding) and calls `map.invalidateSize()` when the map becomes visible again. **That call is load-bearing**: Leaflet measures its container as 0×0 while `display:none`, so without a re-measure the map comes back as a grey box.

`render()` is the single entry point: filter `places` through `visible()`, then rebuild the markers plus one of the three list renderers from scratch. There is no diffing or virtual DOM — markers are all removed and recreated, and `#list` is cleared and repopulated. Any state change ends in a `render()` call.

Filter state lives in one `state` object (park segment, per-type toggles, must-only, search query, plus the `adding`/`moving` modes). `visible()` ([index.html:437](index.html#L437)) is the sole place these combine.

The list groups by `park|land` in first-encountered order, which means group ordering follows array order in `places` — reordering the data reorders the UI.

### Known venues (OpenStreetMap)

`fetchVenues()` runs one Overpass query **per zone, scoped to that zone's own polygon**, not a bounding box and not a latitude threshold. There are three: Disneyland and California Adventure are `tourism=theme_park`, while Downtown Disney is `landuse=retail` — hence `OSM_AREA` carrying a whole selector string per zone rather than just a name. That matters: a bbox over the resort returns ~170 places including Downtown Disney and the hotels, while the polygons return ~34 per park correctly attributed. Guessing park from latitude is what made the original seed data wrong.

Signed in, the list lives in one shared Firestore doc (`venues/all`) — it is identical for everyone, so the first device to find it missing fetches from Overpass and writes it, and every device after just reads. `localStorage["magicMunchMap.osm.v1"]` mirrors it for signed-out and offline use. **All searching runs against that cache**. Never query per keystroke: Nominatim's usage policy forbids autocomplete traffic outright, and Overpass is volunteer-run. The cache also means suggestions work in the parks, where there is no signal.

OSM commonly holds both a node and a building way for one venue, so `step()` dedupes on `park|name`. `nearestVenue()` uses an equirectangular approximation, which is accurate well past the 60m radius it is called with.

Venues carry more than a name: `amenity` (100% coverage — this is what distinguishes table service from quick service), `cuisine` (~80%), `website` (~85%), and `mobile_ordering` (~57%). These are copied onto a place when one is picked, so cards can show them.

OSM knows nothing about Disney "lands", so `land` stays a manual choice from `LANDS`.

### The focus mask

`drawFocus()` veils everything outside the selected zones. The rings come from `DINING.bounds` — real OSM park outlines, simplified to ~4m with Douglas-Peucker (261 points for all three). Disneyland is a MultiPolygon, so a zone can contribute more than one ring; never assume one ring per zone.

The convex-hull code (`convexHull`/`expandRing`/`roundRing`) is still there as a fallback for a zone with no boundary. It shipped first, when Overpass was unreachable, and it is worse: a hull of venue positions has no relationship to the park edge, which is what the eye expects to see.

Boundaries come from **Nominatim**, not Overpass — Overpass has been unreachable or 500ing from here, while Nominatim returns polygon geometry directly. Its policy caps requests at one per second, hence the sleep in `boundaries()`. `overpass_venues()` now tries three endpoints in turn for the same reason.

Leaflet fills with `evenodd`, so passing `[outer].concat(rings)` to `L.polygon` punches the rings out as holes. The softness comes from `filter: blur(9px)` on the veil itself, which turns each hole edge into a gradient rather than a cut — cheaper and far more robust than blurring map tiles, which would need a second clipped tile layer re-projected on every zoom.

### Catalogs, and the shape of the app

**Meals are multi-select, and nothing selected means no filter.** `state.meals` is a set; `mealOk()` passes anything answering to *any* chosen meal. That is the opposite default to the park chips (all on) — deliberately, because you narrow to one or two meals and rarely exclude one, and the sheet's wording carries the difference.

**Seasonal items are exempt from the meal filter.** Every one of the 195 blog items has no service time — the foodie guide never states one. Judging them on a meal would have silently emptied the whole Seasonal section, which is Explore's default scope. `mealOkCatalog()` lets them through, and the filter sheet hides the meal group entirely when Explore is scoped to seasonal.

**Disney's menu sections are not the app's meals.** `mealsFor()` maps a `period` label to zero or more meal keys: "Lunch And Dinner" (1,457 items, the largest bucket) answers to both, "Snack" to AM and PM since it says nothing about which, "Special" and "Lounge" to neither. Matching on the `meal` key alone left 2,737 of 4,020 items unreachable by the filter. Every meal check goes through `mealOk()` — `visible()` and the Explore filter both — so the two cannot drift.

**The card cap must never reach the map.** `exploreList()` returns every match, uncapped; `drawExploreCards()` slices it. Markers are ~86 points however many dishes sit on them, so there is no reason to limit them — and doing so was actively wrong: a pin claimed the count of the *visible slice*, and any venue past the cut disappeared from the map altogether. Flo's V8 Café, with 115 matches, showed nothing at all.

**A cap must never be silent.** Explore holds back what it cannot render — four thousand cards on a phone is not viable — but every section header reads "350 of 2,488" when it is truncated, the count is the full total rather than the visible slice, and a Show more button raises the ceiling. Silent truncation reads as "this is everything", which is the one thing it is not.

**Explore caps each section separately.** One shared cap meant the 193 seasonal items were pushed first and the menu got the remainder: seven of nearly four thousand, so a venue with a large menu looked empty.

**One marker per location, never one per record.** 4,020 dishes resolve to 55 venues — median 52 per point, worst 270 — so a marker each would stack hundreds invisibly on one pixel. `groupBySpot()` buckets by rounded lat/lng, the pin carries the count, and `spotPopup()` lists what is there with an action per row (Add in Explore, Edit in My list), capped at 12. `markers` is keyed under **every** member of a group so `focus(p)` still finds the pin for a given record, and dragging is disabled on a grouped pin — moving one would move all of them.

**Filters live in one sheet, not a chip strip.** The strip scrolled sideways, so options fell off the edge with nothing indicating they were there — which is why filtering never felt complete. Everything filterable is now in `#filterDlg` under labelled groups (Where / Only show / Meal / Arrange), the sheet hides whichever controls do not apply to the current mode, and the Filters button carries a dot whenever anything is off its default. `activeFilters()` must count every one of them; a filter the badge ignores is a filter the user cannot tell is on.

**The header is a phone budget.** Two sticky rows, about 95px: mark + search + account, then mode + count + Filters (+ the list/map toggle above 700px, where the bottom pill is hidden instead). The old layout spent ~240px before any content. The `<h1>` survives as `.sr` (visually hidden) — the mark carries the identity on screen because a phone cannot spare the row. Group/meal/scope live in a filter sheet, which also shows only the controls that apply to the current mode.

**Two concepts, two presentations, and they are independent.** `state.mode` is *what* you are looking at (`mine` | `explore`); `state.show` is *how* (`cards` | `map`). That crossing is deliberate — "my list on a map" and "search results as a list" are both things people want, and the old five-tab control could express neither. `state.group` (`area` | `day` | `tried`) arranges the list and only applies to `mine`.

Filters were cut from twelve chips to five (three parks, Near me, Must do) plus two selects (group, meal). Meal became a select because it only matters when planning; Near me is a *sort*, not a filter, and reorders `mine` into one distance-ordered list.

**`hit` is the explore-result discriminator, never `kind`** — saved places already use `kind` for the OSM amenity type, and reusing it routed saved restaurants into the explore popup renderer.

**My list shows only my list.** Discovery lives in Explore and nowhere else. An earlier design leaked catalog matches into the list as ghost cards, which was wrong twice over: they were not on the list, and they bypassed `visible()`, so Must do appeared broken because the ghosts ignored it.

**The to-do list is the product.** Everything else is a way to get things onto it. Three catalogs feed it, and all three follow the same rule: **a source, never content**. Nothing reaches `places` until the user taps add.

| Catalog | From | Carries |
|---|---|---|
| `venues` | Overpass, live or from `dining.js` | positions, cuisine, mobile ordering |
| `window.MENU` | `tools/extract_menu.py` | seasonal dishes, photos |
| `window.DINING.items` | `tools/refresh_data.py` | 4,000 menu items with prices |

`drawExplore()` searches all three at once. `state.here` (geolocation) flips `drawList()` from land-grouping to a single distance-ordered list, which is what "what's near me right now" actually needs.

`dining.js` is committed with a venue snapshot, so a first-time visitor has working positions and suggestions before anyone taps Resync.

**Disney's endpoints send no CORS headers**, so `refresh_data.py` cannot move into the browser — that half is build-time by necessity, not by choice. Overpass does send them, which is why the in-app button can refresh only that half.

### The seasonal catalog

`window.MENU` (from `menu.js`, generated by `tools/extract_menu.py`) is the third catalog, and follows the same rule as venues: **a source, never content**. Nothing reaches `places` until the user taps add. `drawMenu()` renders it; `savedMenuKeys()` marks what is already owned so re-running the extractor cannot create duplicates.

`venueByName()` joins the two catalogs — a dish knows its venue by name, the OSM venue list knows where that venue is — so adding a dish gets real coordinates. Matching goes through `norm()`, which folds case, accents and curly apostrophes, because the blog and OSM spell the same venue differently.

The extractor's two hard-won details, both worth preserving: the post ships **unclosed `<p>` tags**, so a lazy `<p>.*?</p>` spans thousands of characters and swallows 753 images — the token patterns are unrolled so a paragraph can never cross an `<img>`. And there is **no `<article>` element**; `<main>` is the wrapper, and scoping matters because the page chrome is full of unrelated images.

Photos are hotlinked from Disney's CDN, picking the smallest srcset candidate ≥600px rather than the 1920px inline `src`. `referrerpolicy="no-referrer"` and `loading="lazy"` are set on every thumbnail. Treat the URLs as fragile: they are Disney's to move.

## Conventions to match

- **ES5 style throughout**: `var`, `function(){}`, no arrow functions, template literals, `const`/`let`, or optional chaining. The whole script is one IIFE with no module system. Keep new code in the same dialect.
- **XSS discipline**: user-supplied text reaches the DOM two ways. Where `innerHTML` is used (popups, group headers), run values through `esc()` ([index.html:424](index.html#L424)); elsewhere prefer `textContent`, as `cardFor()` does. `svg()`/`GLYPH` interpolation is for trusted static icon paths only.
- **There is exactly one kind of place.** `FOOD` (color) and `GLYPH` (icon path) are single constants, not maps. Reintroducing categories means restoring those maps plus the `<select>`, the filter chips, the `.chip[data-type=...]` rules, and a per-type branch in `visible()`.
- **The logo** is inline SVG in the app bar, colored with `var(--logo-a)`/`var(--logo-b)`/`var(--gold)` so it follows the theme. The `<head>` favicon is the same artwork as a `data:` URI with hardcoded hex — CSS vars don't resolve there, so changing the logo means updating both.
- **Theming is CSS custom properties** on `:root` with a `prefers-color-scheme: dark` override. New colors belong there, not inline — except marker/popup styling, which Leaflet injects outside the themed tree and therefore hardcodes hex values (`FOOD`, `.pop`). `FOOD` must be kept in step with the `--food` token by hand; nothing enforces it.
- **`--brand` inverts between themes** — dark cyan on light, bright cyan on dark — so never hardcode `#fff` on a brand-colored surface. Use `--on-brand`, which flips with it. The palette is tuned so every foreground/background pair clears WCAG AA at 4.5:1; if you change a category color, re-check it against white chip labels, which is the tightest pair.
- **Accessibility patterns already in place**: toggles use `aria-pressed` as their source of truth (handlers read the attribute back, e.g. the chip handler at [index.html:651](index.html#L651)), icon-only buttons carry `aria-label`, and animations are gated on `prefers-reduced-motion` in both CSS and JS.
- Park assignment for new pins is inferred from latitude (`lat > 33.8095` → `dl`) at [index.html:630](index.html#L630); the map is also bounded to the resort by `setMaxBounds`.
