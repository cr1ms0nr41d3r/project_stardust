# Sprite Credits

The game's sprite images live in this folder and are served locally by the app
(`/static/assets/...`). They are wired to the game through the `MANIFEST` in
[`static/js/assets.js`](../js/assets.js).

## Current art

The placeholder sprites shipped here (planets, ships, the enemy vessels) were
generated as simple labelled image tiles from **[placehold.co](https://placehold.co)**,
a free web image service. They are colour-themed to match each world's nature
(e.g. Inferna II is furnace-orange, Verdanya is life-green). Each is a plain PNG
with no usage restrictions.

## Swapping in your own / nicer art

1. Drop a PNG into the matching sub-folder (`planets/`, `ships/`, `enemy/`,
   `crew/`).
2. Point that file's alias at it in `MANIFEST` (`static/js/assets.js`).

That's the only change needed. Good free, no-attribution ("CC0") sources:

- **Kenney** — <https://kenney.nl/assets> (search "space", "planets")
- **OpenGameArt (CC0 filter)** — <https://opengameart.org>
- **NASA image library (public domain)** — <https://images.nasa.gov>

If an alias is missing or a file fails to load, the game automatically draws a
generated placeholder shape instead — so the game never breaks over art.
