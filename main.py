"""Entry point, for the desktop and for the browser.

The loop is async because pygbag requires it: a WASM build shares the
browser's single thread, so a frame that never yields locks the tab. The
`await asyncio.sleep(0)` is that yield. It costs nothing on the desktop,
where `asyncio.run` drives the same coroutine.

pygbag looks for a top-level `main.py` that runs an async entry point, so
the shape of this file is part of the build contract -- keep it here.

    python main.py 1234        # desktop, replaying seed 1234
    python tools/buildweb.py   # build the web version
"""

from __future__ import annotations

import asyncio
import sys
import traceback

import pygame

from lechery.platform import is_web
from lechery.settings import Settings
from lechery.ui.app import App

SIZE = (1280, 760)
FPS = 60

#: Never advance the world by more than this in one frame. A browser tab in
#: the background stops painting, so the first frame after it returns can
#: carry seconds of elapsed time -- enough to move the player through a wall.
MAX_STEP = 1 / 30

CRASH_BG = (38, 16, 18)
CRASH_TEXT = (240, 220, 216)


def parse_seed(argv: list[str]) -> int | None:
    """The seed, if one was given and it is actually a number.

    Defensive because argv is not ours in a web build: pygbag invokes the
    module with whatever it likes, and `int()` on that would raise before
    the first frame -- which in a browser looks like a blank canvas and no
    explanation at all.
    """
    for argument in argv:
        if argument.lstrip("-").isdigit():
            return int(argument.lstrip("-"))
    return None


async def show_crash(screen: pygame.Surface, report: str) -> None:
    """Draw a traceback on the canvas and hold it there.

    In a browser an unhandled exception leaves a grey canvas and nothing
    else -- no console the player can reach, especially on a phone. Putting
    the traceback on screen is the difference between a bug report and
    "it doesn't work".
    """
    print(report, file=sys.stderr)

    # The font system may be what failed, so a plain fill happens first and
    # unconditionally: a red screen at least says "it crashed" rather than
    # "it never started".
    screen.fill(CRASH_BG)
    pygame.display.flip()

    try:
        font = pygame.font.Font(None, 20)
        lines: list[str] = []
        for line in report.splitlines():
            # Long paths wrap badly; the tail of each line is the useful part.
            while len(line) > 78:
                lines.append(line[:78])
                line = line[78:]
            lines.append(line)

        y = 16
        for line in lines[-30:]:
            screen.blit(font.render(line, True, CRASH_TEXT), (14, y))
            y += 22
        pygame.display.flip()
    except Exception:  # pragma: no cover - the last-resort path
        pass

    # Keep yielding, or the tab freezes on the error screen too.
    while True:
        pygame.event.get()
        await asyncio.sleep(0.1)


async def run(seed: int | None = None) -> int:
    pygame.init()
    pygame.display.set_caption("Lechery")

    # RESIZABLE is a desktop affordance; in a browser the canvas size is the
    # template's business, and asking for a mode it cannot give is a way to
    # fail before anything is drawn.
    flags = 0 if is_web() else pygame.RESIZABLE
    screen = pygame.display.set_mode(SIZE, flags)

    # The canvas may not be the size we asked for, so the app measures what
    # it actually got. Getting this wrong puts the whole UI off-screen.
    size = screen.get_size()
    clock = pygame.time.Clock()

    try:
        app = App(size, Settings.load())
        if seed is not None:
            from lechery.traits import default_character

            app.start_game(default_character(), seed=seed)

        running = True
        while running:
            dt = min(clock.tick(FPS) / 1000.0, MAX_STEP)
            running = app.step(screen, pygame.event.get(), dt)
            pygame.display.flip()

            # Hand the frame back to the browser. Awaited every pass,
            # including the one that quits.
            await asyncio.sleep(0)
    except Exception:
        await show_crash(screen, traceback.format_exc())

    pygame.quit()
    return 0


def main(argv: list[str]) -> int:
    return asyncio.run(run(parse_seed(argv)))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
