# Magic Munch Map

A one-page static site for planning what to eat and ride at Disneyland and California Adventure. OpenStreetMap base layer, no build step, no backend.

## Files

- `index.html` — the whole app, including the logo (inline SVG in the app bar)
- `places.js` — the data. This is the only file you need to touch day to day.
- `README.md` — this
- `CLAUDE.md` — orientation notes for Claude Code
- `CNAME` — the custom domain. Deleting it drops the site back to `jdmiller2010.github.io/magic-munch-map`.

## Run it

Open `index.html` in a browser. That's it. Tiles load from OpenStreetMap over the network.

## Host it

Any static host works. Two easy options:

**GitHub Pages** — Settings → Pages → Source: **Deploy from a branch**, `main`, `/ (root)`. GitHub then republishes the repo root on every push to `main`. There is no build step, so no workflow is involved. Live at **https://mmm.molendino.com** a minute or so after each push. Editing `places.js` in the GitHub web editor counts as a push, which means you can add a restaurant from your phone and have it live before you reach the front of the line.

**Netlify** — drag the folder onto app.netlify.com. Instant URL, custom domain if you want one.

### Custom domain

The site is served at `mmm.molendino.com`. Two pieces make that work, and both need to be in place:

- **DNS** — a `CNAME` record on `molendino.com`, name `mmm`, pointing at `jdmiller2010.github.io.` (trailing dot included).
- **The `CNAME` file** in this repo, which GitHub reads on every publish. Setting the custom domain in Settings → Pages normally creates this file for you; it is committed here already, so the setting should populate itself.

Tick **Enforce HTTPS** in Settings → Pages once the certificate provisions. It's free, via Let's Encrypt, and can take anywhere from a minute to a few hours.

Worth knowing: `localStorage` is scoped per origin, so browser-only edits saved against the old `jdmiller2010.github.io` address are not visible at `mmm.molendino.com`. They aren't deleted, just unreachable from the new domain. Same applies in reverse if the domain is ever removed.

## Adding places

Two ways, and they meet in the middle:

1. **In the browser.** Tap "Add a pin", tap the map, fill in the form. Turn on "Move pins" and drag anything that's in the wrong spot. Tap the star on any card to flag it as a must do.
2. **In the file.** Edit `places.js` directly. The format is one object per line.

Browser edits save to that browser only — they won't show up on the other person's phone. When you're happy with them, hit **Copy data file** and paste the result over the contents of `places.js`, then redeploy. Now it's shared.

## Fields

| Field | Values |
|---|---|
| `name` | Anything |
| `park` | `dl` or `dca` |
| `land` | Free text. Groups the list. |
| `type` | `food`, `ride`, `show`, `shop` |
| `lat` / `lng` | Decimal degrees |
| `must` | `true` or `false`. Shows a gold Must do tag. |
| `note` | Free text |

## Known rough edges

- **Pin positions are approximate.** They're placed from general knowledge of the park layout, not surveyed. Expect some to be off by a building or two. The "Move pins" mode exists for exactly this — fix them once and copy the data file back.
- Some venues rotate names and menus. Verify anything you're building a reservation around.
- The map is deliberately bounded to the resort so you can't pan off to sea.

## Design notes

The logo is a map pin with a bite taken out of it, flanked by two twinkling sparkles — magic, munch, map. It's inline SVG in the app bar (and, hardcoded, a `data:` favicon in `<head>`), so it recolors with the theme instead of shipping an image file. The bite is a `<mask>`: two black circles over a white rect. The sparkle twinkle stops under `prefers-reduced-motion`.

Modern mobile-app layout: sticky app bar, segmented park control, horizontally scrolling filter chips, card list, floating action button, and a bottom sheet for editing. Dark mode follows the system setting. Fonts are Outfit (headings) and Inter (body) from Google Fonts.

Palette lives in the `:root` block at the top of `index.html`, with dark values in the `prefers-color-scheme` block right below it:

- `--brand #5b3fd6` primary actions
- `--logo-a` / `--logo-b` the gradient in the logo pin
- `--gold #f0a500` must-do state
- `--food #f2603c` / `--ride #009e86` / `--show #8055ff` / `--shop #c07d1f` category colors

## Attribution

Base map data © OpenStreetMap contributors, ODbL. The attribution link in the footer and on the map must stay.

Not affiliated with, endorsed by, or sponsored by Disney. Don't use official park map artwork as a background — it's copyrighted.
