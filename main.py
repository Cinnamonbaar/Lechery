"""Entry point: open a window and play.

Pass a seed to replay a particular map: `python main.py 1234`.
"""

from __future__ import annotations

import sys

import pygame

from lechery.content.game import new_game
from lechery.ui.roomview import RoomView

SIZE = (900, 620)
FPS = 60


def main(argv: list[str]) -> int:
    seed = int(argv[0]) if argv else None
    world = new_game(seed)
    print(f"seed: {world.seed}")

    pygame.init()
    pygame.display.set_caption("Lechery")
    screen = pygame.display.set_mode(SIZE)
    clock = pygame.time.Clock()

    view = RoomView(world, SIZE)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                view.handle_event(event)

        view.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
