# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Magic Munch Map — a zero-build web app: a Leaflet map of food/rides/shows/shops across Disneyland and California Adventure. Everything — markup, CSS, and app logic — lives in [index.html](index.html). Place data lives in [places.js](places.js). There is no package.json, no bundler, no test suite, and no dependencies installed locally; Leaflet 1.9.4 and Google Fonts load from CDNs at runtime. See [README.md](README.md) for hosting and data-entry workflow.

## Running it

Open [index.html](index.html) directly — `file://` works, since `places.js` is a classic script rather than a module. A local server behaves identically if you prefer one:

```
python3 -m http.server 8000    # then open http://localhost:8000
```

There is nothing to build, lint, or test. Verify changes by loading the page and exercising the UI.

## Data flow

Place data has three tiers, resolved in `load()` ([index.html:387](index.html#L387)):

1. **[places.js](places.js)** — the shared, committed seed data, a plain script that assigns `window.PLACES = [...]`, one object per line. Entries carry no `id`, so `load()` assigns synthetic ones (`seed-<index>`) — which means ids are positional and reordering the file reshuffles them.
2. **`localStorage["magicMunchMap.v1"]`** — per-browser edits (falling back to the pre-rename `parkFoodMap.v1` key on read). If a non-empty array is stored, it wins outright over `window.PLACES`; the seed is not merged in, so edits to `places.js` are invisible to a browser that has local edits until Reset. Every mutation (add, edit, star, delete, pin drag) calls `save()` immediately.
3. **"Copy data file"** ([index.html:703](index.html#L703)) — serializes current `places` back into `window.PLACES = [...]` source text for pasting into `places.js`. This is the only path for promoting local edits into shared data, so its output format and the `places.js` format must stay in sync.

A place record: `{ id, name, park: "dl"|"dca", land, type: "food"|"ride"|"show"|"shop", lat, lng, must, note, ord }`.

`ord` controls list grouping order. It exists because Firestore returns documents unordered and a multi-field `orderBy` would require a composite index, so the snapshot handler sorts client-side on `ord` instead — which also preserves the curated ordering of `places.js` rather than falling back to alphabetical.

### Cloud sync

A fourth, optional tier sits on top, in the cloud block at the end of the script. It is inert unless `window.FIREBASE_CONFIG` is non-null *and* the Firebase SDK loaded, both checked by `configured()`. When a user signs in:

- `startWatch()` subscribes to the `places` collection and **`onSnapshot` becomes the owner of the `places` array** — it replaces the array wholesale and calls `render()`. Local mutation is still applied optimistically first; the snapshot echo reconciles it, and because the array is replaced rather than appended to, that cannot duplicate.
- Every mutation goes through `persist(p)` / `persistDelete(id)`, which write a **single document** in cloud mode and fall back to `save()` (whole-array localStorage) when signed out. Never call `save()` directly from a mutation site — in cloud mode that would write a stale localStorage shadow that then shadows `places.js` after sign-out.
- Firestore's offline cache means writes succeed with no network; their promises simply don't settle until the server acks, so error handlers must not assume failure from silence.

The Firebase SDK is loaded as **compat** builds, deliberately: they are classic scripts, which keeps the ES5 dialect and the `file://` workflow working. The modular SDK is ES-module-only and would break both.

## Rendering model

`render()` ([index.html:584](index.html#L584)) is the single entry point: filter `places` through `visible()`, then fully rebuild both the map markers and the list from scratch. There is no diffing or virtual DOM — markers are all removed and recreated, and `#list` is cleared and repopulated. Any state change ends in a `render()` call.

Filter state lives in one `state` object (park segment, per-type toggles, must-only, search query, plus the `adding`/`moving` modes). `visible()` ([index.html:437](index.html#L437)) is the sole place these combine.

The list groups by `park|land` in first-encountered order, which means group ordering follows array order in `places` — reordering the data reorders the UI.

## Conventions to match

- **ES5 style throughout**: `var`, `function(){}`, no arrow functions, template literals, `const`/`let`, or optional chaining. The whole script is one IIFE with no module system. Keep new code in the same dialect.
- **XSS discipline**: user-supplied text reaches the DOM two ways. Where `innerHTML` is used (popups, group headers), run values through `esc()` ([index.html:424](index.html#L424)); elsewhere prefer `textContent`, as `cardFor()` does. `svg()`/`GLYPH` interpolation is for trusted static icon paths only.
- **Type is a four-way key**, and adding a fifth means touching all of: `COLORS`, `KINDS`, `GLYPH`, the `<select>` options, the filter chips, and the `.chip[data-type=...]` CSS rules.
- **The logo** is inline SVG in the app bar, colored with `var(--logo-a)`/`var(--logo-b)`/`var(--gold)` so it follows the theme. The `<head>` favicon is the same artwork as a `data:` URI with hardcoded hex — CSS vars don't resolve there, so changing the logo means updating both.
- **Theming is CSS custom properties** on `:root` with a `prefers-color-scheme: dark` override. New colors belong there, not inline — except marker/popup styling, which Leaflet injects outside the themed tree and therefore hardcodes hex values (`COLORS`, `.pop`). The `COLORS` object must be kept in step with the `--food`/`--ride`/`--show`/`--shop` tokens by hand; nothing enforces it.
- **`--brand` inverts between themes** — dark cyan on light, bright cyan on dark — so never hardcode `#fff` on a brand-colored surface. Use `--on-brand`, which flips with it. The palette is tuned so every foreground/background pair clears WCAG AA at 4.5:1; if you change a category color, re-check it against white chip labels, which is the tightest pair.
- **Accessibility patterns already in place**: toggles use `aria-pressed` as their source of truth (handlers read the attribute back, e.g. the chip handler at [index.html:651](index.html#L651)), icon-only buttons carry `aria-label`, and animations are gated on `prefers-reduced-motion` in both CSS and JS.
- Park assignment for new pins is inferred from latitude (`lat > 33.8095` → `dl`) at [index.html:630](index.html#L630); the map is also bounded to the resort by `setMaxBounds`.
