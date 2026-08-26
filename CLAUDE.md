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

A place record: `{ id, name, park: "dl"|"dca", land, type: "food"|"ride"|"show"|"shop", lat, lng, must, note, ord }`.

`ord` controls list grouping order. It exists because Firestore returns documents unordered and a multi-field `orderBy` would require a composite index, so the snapshot handler sorts client-side on `ord` instead. New pins get `nextOrd()`, one past the current maximum.

### Cloud sync

A fourth, optional tier sits on top, in the cloud block at the end of the script. It is inert unless `window.FIREBASE_CONFIG` is non-null *and* the Firebase SDK loaded, both checked by `configured()`. When a user signs in:

- `startWatch()` subscribes to the `places` collection and **`onSnapshot` becomes the owner of the `places` array** — it replaces the array wholesale and calls `render()`. Local mutation is still applied optimistically first; the snapshot echo reconciles it, and because the array is replaced rather than appended to, that cannot duplicate.
- Every mutation goes through `persist(p)` / `persistDelete(id)`, which write a **single document** in cloud mode and fall back to `save()` (whole-array localStorage) when signed out. Never call `save()` directly from a mutation site — in cloud mode that would write a stale localStorage shadow that resurfaces after sign-out.
- Firestore's offline cache means writes succeed with no network; their promises simply don't settle until the server acks, so error handlers must not assume failure from silence.
- A `permission-denied` snapshot error sets `cloud.on = false`, dropping the session back to local mode. Without that the account is signed in but unauthorized, `persist()` still routes to Firestore, and every edit is written nowhere — rejected by the rules and skipped by the localStorage fallback.

The Firebase SDK is loaded as **compat** builds, deliberately: they are classic scripts, which keeps the ES5 dialect and the `file://` workflow working. The modular SDK is ES-module-only and would break both.

## Rendering model

`render()` ([index.html:584](index.html#L584)) is the single entry point: filter `places` through `visible()`, then fully rebuild both the map markers and the list from scratch. There is no diffing or virtual DOM — markers are all removed and recreated, and `#list` is cleared and repopulated. Any state change ends in a `render()` call.

Filter state lives in one `state` object (park segment, per-type toggles, must-only, search query, plus the `adding`/`moving` modes). `visible()` ([index.html:437](index.html#L437)) is the sole place these combine.

The list groups by `park|land` in first-encountered order, which means group ordering follows array order in `places` — reordering the data reorders the UI.

## Conventions to match

- **ES5 style throughout**: `var`, `function(){}`, no arrow functions, template literals, `const`/`let`, or optional chaining. The whole script is one IIFE with no module system. Keep new code in the same dialect.
- **XSS discipline**: user-supplied text reaches the DOM two ways. Where `innerHTML` is used (popups, group headers), run values through `esc()` ([index.html:424](index.html#L424)); elsewhere prefer `textContent`, as `cardFor()` does. `svg()`/`GLYPH` interpolation is for trusted static icon paths only.
- **There is exactly one kind of place.** `FOOD` (color) and `GLYPH` (icon path) are single constants, not maps. Reintroducing categories means restoring those maps plus the `<select>`, the filter chips, the `.chip[data-type=...]` rules, and a per-type branch in `visible()`.
- **The logo** is inline SVG in the app bar, colored with `var(--logo-a)`/`var(--logo-b)`/`var(--gold)` so it follows the theme. The `<head>` favicon is the same artwork as a `data:` URI with hardcoded hex — CSS vars don't resolve there, so changing the logo means updating both.
- **Theming is CSS custom properties** on `:root` with a `prefers-color-scheme: dark` override. New colors belong there, not inline — except marker/popup styling, which Leaflet injects outside the themed tree and therefore hardcodes hex values (`FOOD`, `.pop`). `FOOD` must be kept in step with the `--food` token by hand; nothing enforces it.
- **`--brand` inverts between themes** — dark cyan on light, bright cyan on dark — so never hardcode `#fff` on a brand-colored surface. Use `--on-brand`, which flips with it. The palette is tuned so every foreground/background pair clears WCAG AA at 4.5:1; if you change a category color, re-check it against white chip labels, which is the tightest pair.
- **Accessibility patterns already in place**: toggles use `aria-pressed` as their source of truth (handlers read the attribute back, e.g. the chip handler at [index.html:651](index.html#L651)), icon-only buttons carry `aria-label`, and animations are gated on `prefers-reduced-motion` in both CSS and JS.
- Park assignment for new pins is inferred from latitude (`lat > 33.8095` → `dl`) at [index.html:630](index.html#L630); the map is also bounded to the resort by `setMaxBounds`.
