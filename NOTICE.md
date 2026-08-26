# Notice on third-party content

The MIT license in `LICENSE` covers **the code in this repository** — `index.html`,
the scripts in `tools/`, `sw.js`, and the icons, all written for this project.

It does **not** cover the generated data files, which are not the author's to
license. They are three different things with three different rules:

## `dining.js` — venue positions and park boundaries

Derived from **OpenStreetMap**, © OpenStreetMap contributors, licensed
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/). ODbL is share-alike: a
substantially derived database carries the same licence and the same attribution
requirement. The attribution appears in the app footer and on the map, and must
stay there.

## `dining.js` — menu items, prices and hours

Fetched from `disneyland.disney.go.com`. This is Disney's content. It is not
licensed for redistribution, and republishing it — which a public repository
does — is Disney's call to object to, not something the MIT licence can grant.

## `menu.js` — seasonal items, descriptions and photos

From the Disney Parks Blog, likewise Disney's content. The photos are
hotlinked rather than copied, but the dish names and descriptions are stored
here, and the same caveat applies.

## What this means in practice

For a small personal planner nobody is likely to mind. But the honest position
is that this repository redistributes Disney's content without permission, and
"it's MIT licensed" does not change that. If that matters to you:

- Add `menu.js` and the `items`/`details` keys of `dining.js` to `.gitignore`
  and have each person run `tools/refresh_data.py` locally. The tools are the
  valuable part and they are unambiguously MIT.
- Or keep only the OpenStreetMap-derived parts — venues, boundaries — which are
  ODbL and freely redistributable with attribution.

Not affiliated with, endorsed by, or sponsored by Disney.
