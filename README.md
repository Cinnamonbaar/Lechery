# Lechery

A NSFW transformation RPG. Top-down movement between rooms, procedurally
arranged areas with handcrafted set pieces, and a paperdoll character view.

Built with Pygame-CE, targeting desktop and the browser (via pygbag).

## Running

```sh
pip install -r requirements.txt
python main.py            # a random world
python main.py 1234       # replay a specific seed
```

`python main.py` opens the menu; a seed on the command line skips straight
into the world with a default character, for iterating on generation.

**Controls** — WASD or arrows to move, mouse to look, `[` and `]` toggle the
side bars, `F5` cycles the layout (auto / wide / compact), `Esc` returns to
the menu.

## Development

```sh
pip install -r requirements-dev.txt
python -m pytest                        # the whole suite, no display needed
python tools/mapdump.py 1234            # dump generated areas as ASCII
python tools/mapdump.py 1234 tutorial --tiles   # per-room floorplans
```

## Building for the web

```sh
python tools/buildweb.py           # build into build/web
python tools/buildweb.py --serve   # build and serve on localhost:8000
```

The staging step exists because pygbag packages whatever directory you point
it at and has no exclude flag — aiming it at the repo root ships the test
suite to every player.

Two constraints the web build puts on the code, both already handled:

- **The loop must be async.** A WASM build shares the browser's single
  thread, so `main.run` awaits `asyncio.sleep(0)` every frame to hand the
  frame back. Without it the tab freezes.
- **`SysFont` does not work in the browser.** There is no OS font list to
  query, and it degrades silently — so a web build would render in a
  different typeface than the desktop one, and you would only find out after
  packaging. `lechery/ui/fonts.py` loads bundled files by path instead, and
  falls back to the font inside the pygame wheel.

## Layout

| Package | What lives there |
| --- | --- |
| `lechery/world` | Rooms, areas, exits, roles. Geography and movement rules. |
| `lechery/generation` | Layouts, room templates, per-area seeding. |
| `lechery/space` | Tilemaps, carving, collision. Geometry, not rendering. |
| `lechery/entities` | Bodies that occupy and move through space. |
| `lechery/ui` | Everything that imports pygame, and nothing else does. |
| `lechery/stats.py` | Stats and skills: capability, as opposed to body. |
| `lechery/ui/screens` | Menu, character creation, play. |
| `lechery/content` | The actual game: areas, rooms, backstories, prose. |

Only `lechery/ui` imports pygame. Everything else is plain Python, which is
why the whole simulation is testable without a display.

## Playing it on a phone

Every push to `main` builds the web version and publishes it to GitHub
Pages; open that URL on a phone and refresh after each push. Nothing needs
installing on the phone, and no desktop is involved.

Pushes to working branches build and test but do not publish, so a broken
build shows up before it reaches the phone rather than after.

Most iteration does not need a phone at all: `F5` cycles the layout to
compact on the desktop, and the on-screen stick accepts mouse drags for
exactly that reason.

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
