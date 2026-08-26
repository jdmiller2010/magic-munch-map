# Magic Munch Map

A one-page static site for planning what to eat at Disneyland and California Adventure. Food only — no rides, shows, or shops. OpenStreetMap base layer, no build step, no backend.

## Files

- `index.html` — the whole app, including the logo (inline SVG in the app bar). There is no seed data file; the list starts empty and lives in Firestore or your browser.
- `menu.js` — seasonal items from a Disney Parks Blog foodie guide, with photos
- `dining.js` — every venue's full menu, prices and hours, plus venue positions
- `tools/extract_menu.py` / `tools/refresh_data.py` — generate those two
- `firebase-config.js` — optional cloud sync config. Null by default; the app works without it.
- `firestore.rules` — the security rules to paste into the Firebase console.
- `README.md` — this
- `CLAUDE.md` — orientation notes for Claude Code
- `CNAME` — the custom domain. Deleting it drops the site back to `jdmiller2010.github.io/magic-munch-map`.

## Run it

Open `index.html` in a browser. That's it. Tiles load from OpenStreetMap over the network.

## Host it

Any static host works. Two easy options:

**GitHub Pages** — Settings → Pages → Source: **Deploy from a branch**, `main`, `/ (root)`. GitHub then republishes the repo root on every push to `main`. There is no build step, so no workflow is involved. Live at **https://mmm.molendino.com** a minute or so after each push. Adding a restaurant from your phone goes through the app and Firestore, not through a deploy.

**Netlify** — drag the folder onto app.netlify.com. Instant URL, custom domain if you want one.

### Custom domain

The site is served at `mmm.molendino.com`. Two pieces make that work, and both need to be in place:

- **DNS** — a `CNAME` record on `molendino.com`, name `mmm`, pointing at `jdmiller2010.github.io.` (trailing dot included).
- **The `CNAME` file** in this repo, which GitHub reads on every publish. Setting the custom domain in Settings → Pages normally creates this file for you; it is committed here already, so the setting should populate itself.

Tick **Enforce HTTPS** in Settings → Pages once the certificate provisions. It's free, via Let's Encrypt, and can take anywhere from a minute to a few hours.

Worth knowing: `localStorage` is scoped per origin, so browser-only edits saved against the old `jdmiller2010.github.io` address are not visible at `mmm.molendino.com`. They aren't deleted, just unreachable from the new domain. Same applies in reverse if the domain is ever removed.

## Adding places

Tap **Load park venues** in Manage once, and the app pulls every mapped food venue in both parks from OpenStreetMap — surveyed positions, not guesses. After that the name field autocompletes as you type, and picking a suggestion fills in the park and the real coordinates.

Tap **Add**, fill in the form. A place doesn't need a pin — it'll show in the list either way, and the button on its card drops one whenever you get round to it. In Map view the same button becomes **Drop pin**: tap where you're standing and the nearest mapped venue within 60m is offered as the name. Clear it and type your own for a cart or stand nobody has mapped — the pin stays exactly where you put it.

Four views across the top: **List** groups by land, **Map** shows the pins, **Timeline** lays out each day by meal, and **Tried** splits everything into what you've eaten and what's still waiting. Tick "We tried this" on any place to rate it out of five and write down what you thought.

To fix a pin's position: turn on **Move pins** and drag it. Tap the star on any card to flag it as a must do.

Signed in, every edit goes straight to the shared list and shows up on the other phone. Signed out, edits save to that browser only — **Copy backup** puts the whole list on your clipboard as JSON if you want a snapshot for safekeeping.

## Cloud sync (optional)

Without it, the app is browser-local: every browser keeps its own list and nothing is shared. Turn sync on and both phones read and write one live list instead, with no copy-paste step.

Setup is about ten minutes in the Firebase console, all of it listed in the comments at the top of `firebase-config.js`. The short version:

1. Create a Firebase project, then a Firestore database in Native mode (`us-west1` is closest to Anaheim).
2. Register a web app, copy the `firebaseConfig` object into `firebase-config.js`.
3. Authentication → Sign-in method → enable **Google**.
4. Authentication → Settings → Authorized domains → add **mmm.molendino.com**. Sign-in fails silently on the live site without this.
5. Firestore → Rules → paste `firestore.rules`, with the email addresses that should have access.

Then push. Sign in from the Manage section; the first device to sign in gets an **Upload local list** button that seeds the shared list from the shared list.

The `apiKey` in `firebase-config.js` is not a secret — it names the project, it doesn't grant anything. Access is controlled entirely by the rules, which is why the allowlist in `firestore.rules` is the part worth getting right.

### How it behaves

- **Signed in**, Firestore owns the list. Each edit writes one document, so two people editing different pins merge cleanly instead of overwriting each other's work.
- **Offline**, edits are cached locally and sync when signal returns — which matters, because the parks are a dead zone. The status dot turns gold while offline.
- **Signed out**, nothing changes from before: the shared list plus this browser's `localStorage`.
- Signing in does **not** touch `localStorage`, so signing out returns you to whatever you had before, untouched.

## Using it

**Your list is the point.** Open the app, and List answers "what's on my list, and what's near me?" — tap **Near me** and everything reorders by walking distance with a distance on each card.

**Explore** is the other half: search once across seasonal blog items, every venue's full menu, and the venues themselves. Results show prices and descriptions, and each has an add button. Nothing reaches your list until you tap it.

## The menu catalog

`menu.js` holds every dish from a Disney Parks Blog foodie guide — name, venue, land, park, description, and a photo. The **Menu** view browses it grouped by land, and the add button on each card is the only way anything enters your list. Nothing is imported wholesale: the catalog is a source, not content. That's deliberate — the app is for the handful of things you actually want, not for every item Disney sells.

### Refreshing

Two commands, run whenever you want; both write files that get committed.

```
python3 tools/refresh_data.py > dining.js
python3 tools/extract_menu.py <guide-url> --season "Halloween 2026" > menu.js
```

`refresh_data.py` does both halves of the map data in one run: venue positions from OpenStreetMap, then each venue's menu, prices, hours and price range from `disneyland.disney.go.com`. It takes a few minutes and makes about 140 requests, rate-limited. Disney's endpoints send no CORS headers, so this cannot run in the browser — it has to be built and committed. The in-app **Resync map data** button refreshes the OpenStreetMap half, which *is* browser-callable.

The last run produced 86 venues, 4,020 menu items (2,672 with prices) and hours for 55 venues. That is 1.1MB of JSON, 83KB over the wire once GitHub Pages gzips it.

Rebuild the seasonal guide when a new one drops:

```
python3 tools/extract_menu.py <guide-url> --season "Halloween 2026" > menu.js
```

Add `--json` to inspect the extraction without writing the file. It scopes to `<main>`, treats a fully-bold paragraph as a venue, reads the `Location:` line for the land, and takes dish names and descriptions from image alt text, which is the richest field on the page. Items already on your list show a tick instead of a plus, so re-running the extractor never creates duplicates.

Photos are hotlinked from Disney's CDN at the 767px srcset size rather than the 1920px original. That keeps the list fast on park wifi, but it does mean the images are Disney's to move or block at any time — if they vanish, cards fall back to the fork glyph.

## Fields

| Field | Values |
|---|---|
| `name` | Anything |
| `park` | `dl` or `dca` |
| `land` | Free text. Groups the list. |
| `lat` / `lng` | Decimal degrees |
| `must` | `true` or `false`. Shows a gold Must do tag. |
| `note` | Free text, written before going |
| `meal` | `breakfast`, `am`, `lunch`, `pm`, `dinner`, or empty |
| `date` | `YYYY-MM-DD`. The day you plan to go. Drives the timeline. |
| `tried` | `true` once you've been |
| `visited` | `YYYY-MM-DD`. The day you actually went. |
| `rating` | 0–5. 0 means unrated. |
| `verdict` | Free text, written after |
| `ord` | Number. Controls the order groups appear in. |

## Known rough edges

- Some venues rotate names and menus. Verify anything you're building a reservation around.
- The map is deliberately bounded to the resort so you can't pan off to sea.

## Design notes

The logo is a map pin with a bite taken out of it, flanked by two twinkling sparkles — magic, munch, map. It's inline SVG in the app bar (and, hardcoded, a `data:` favicon in `<head>`), so it recolors with the theme instead of shipping an image file. The bite is a `<mask>`: two black circles over a white rect. The sparkle twinkle stops under `prefers-reduced-motion`.

Modern mobile-app layout: sticky app bar, segmented park control, horizontally scrolling filter chips, card list, floating action button, and a bottom sheet for editing. Dark mode follows the system setting. Fonts are Fredoka (headings, rounded and friendly) and Inter (body) from Google Fonts.

The look borrows from WALL-E: a sun-bleached earth palette — warm sand ground, rust and bronze, Buy-n-Large amber — with EVE's glowing cyan as the chrome on top of it. Dark mode moves to the night side of the Axiom, deep blue-black with the cyan turned up. Whimsy comes from form rather than decoration: generous rounding, springy overshoot on every press, cards that lift on hover, a floating button that bobs gently, and an eye in the middle of every map pin that blinks about once every six seconds in the logo. All motion is gated on `prefers-reduced-motion`.

Every foreground/background pair in the palette meets WCAG AA (4.5:1 for body text), including the white labels on selected filter chips, which the previous palette did not.

Palette lives in the `:root` block at the top of `index.html`, with dark values in the `prefers-color-scheme` block right below it:

- `--brand #0b7789` primary actions, with `--on-brand` for text that sits on top of it
- `--logo-a` / `--logo-b` the gradient in the logo pin
- `--gold #e09400` must-do state
- `--food #c64f29` / `--ride #358352` / `--show #7458e0` / `--shop #996c2b` category colors

`--on-brand` exists because `--brand` inverts between themes: it is a dark cyan on light backgrounds and a bright cyan on dark ones, so anything painted on a solid brand surface needs ink that flips with it rather than hardcoded white.

## Attribution

Base map data © OpenStreetMap contributors, ODbL. The attribution link in the footer and on the map must stay.

Not affiliated with, endorsed by, or sponsored by Disney. Don't use official park map artwork as a background — it's copyrighted.
