# Lechery

A NSFW transformation RPG. Top-down movement between rooms, procedurally
arranged areas with handcrafted set pieces, and a paperdoll character view.

TypeScript and Svelte, built with Vite. The browser on a phone is the
primary target; a desktop plays the same build in a desktop browser.

Play it at <https://cinnamonbaar.github.io/Lechery/>.

## Running

```sh
cd web
npm install
npm run dev        # http://localhost:5173
```

**Controls** — WASD or arrows to move, or drag anywhere on the world view
for the on-screen stick. The tabs at the top right open the paperdoll and
the log; the gear opens settings.

## Development

```sh
cd web
npm test           # the model suite, no browser needed
npm run check      # types, components included
npm run build      # check + build into web/dist
npm run smoke      # walk the game in a real browser, writing screenshots
```

`npm run smoke` needs a built copy being served:

```sh
npm run build:fast && npx vite preview --port 4173 &
npm run smoke -- screenshots
```

It exists because every hard bug in this project has been invisible outside
a browser — a canvas that never painted, a library that failed to load, a
layout that only broke at a phone's aspect ratio.

## Layout

- `web/src/lib/` — the game model, with no rendering dependency: world,
  generation, space, traits, stats, log, narration, content, session. This
  is what the tests exercise.
- `web/src/ui/` — Svelte components and the canvas renderer.
- `web/src/theme.css` — every colour, size and font in the game, as custom
  properties. The world canvas reads the `--world-*` ones too, so there is
  no second palette hiding in the renderer.

## Credits

The character avatar is drawn by
[dynamic-avatar-drawer](https://gitlab.com/PerplexedPeach/dynamic-avatar-drawer)
by Johnson Zhong, used under the LGPL v3 and vendored unmodified in
`web/public/vendor/dynamic-avatar-drawer/`. The author asks that the library
and any assets created for it stay freely accessible; see that directory's
`LICENSE.md`. It is loaded at runtime as a plain script rather than bundled,
so it stays replaceable, as that licence requires.

## Backups

`.github/workflows/backup.yml` packs the entire history into a git bundle on
every push and weekly, kept as a downloadable artifact for 90 days. A bundle
is a whole repository in one file — `git clone lechery-YYYYMMDD.bundle` gives
it all back.

To also mirror to a second host, add repository secrets `MIRROR_URL` (a push
URL) and `MIRROR_TOKEN`, then set the variable `MIRROR_ENABLED` to `true`.
The mirror step is host-agnostic on purpose: pick a destination after
checking its content policy, since hosts differ on what they will keep.

Artifacts expire. If this project matters to you, download a bundle
periodically and keep it somewhere that is not GitHub.
