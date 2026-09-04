"""Entry point, for the desktop and for the browser.

The loop is async because pygbag requires it: a WASM build shares the
browser's single thread, so a frame that never yields locks the tab. The
`await asyncio.sleep(0)` is that yield. It costs nothing on the desktop,
where `asyncio.run` drives the same coroutine.

pygbag looks for a top-level `main.py` that runs an async entry point, so
the shape of this file is part of the build contract -- keep it here.

    python main.py 1234        # desktop, replaying seed 1234
    pygbag .                   # build and serve the web version
"""

from __future__ import annotations

import asyncio
import sys

import pygame

from lechery.session import Session
from lechery.settings import Settings
from lechery.ui.app import App

SIZE = (1280, 760)
FPS = 60

#: Never advance the world by more than this in one frame. A browser tab in
#: the background stops painting, so the first frame after it returns can
#: carry seconds of elapsed time -- enough to move the player through a wall.
MAX_STEP = 1 / 30


async def run(seed: int | None = None) -> int:
    pygame.init()
    pygame.display.set_caption("Lechery")
    screen = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
    clock = pygame.time.Clock()

    session = Session.new_game(seed)
    print(f"seed: {session.world.seed}")
    app = App(session, SIZE, Settings.load())

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, MAX_STEP)
        running = app.step(screen, pygame.event.get(), dt)
        pygame.display.flip()

        # Hand the frame back to the browser. Must be awaited every pass,
        # including on the frame that quits.
        await asyncio.sleep(0)

    pygame.quit()
    return 0


def main(argv: list[str]) -> int:
    return asyncio.run(run(int(argv[0]) if argv else None))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
