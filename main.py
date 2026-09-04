"""Entry point. Pass a seed to replay a map: `python main.py 1234`."""

from __future__ import annotations

import sys

import pygame

from lechery.session import Session
from lechery.settings import Settings
from lechery.ui.app import App

SIZE = (1280, 760)
FPS = 60


def main(argv: list[str]) -> int:
    session = Session.new_game(int(argv[0]) if argv else None)
    print(f"seed: {session.world.seed}")

    pygame.init()
    pygame.display.set_caption("Lechery")
    screen = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
    clock = pygame.time.Clock()

    app = App(session, SIZE, Settings.load())
    running = True
    while running:
        # Clamped so a hitch cannot tunnel the player through a wall.
        dt = min(clock.tick(FPS) / 1000.0, 1 / 30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                app.handle_event(event)

        app.update(dt)
        app.draw(screen)
        pygame.display.flip()

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
