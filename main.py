"""Entry point: open a window and walk around the test map."""

from __future__ import annotations

import sys

import pygame

from lechery.content.testmap import build_world
from lechery.ui.roomview import RoomView

SIZE = (900, 620)
FPS = 60


def main() -> int:
    world = build_world()
    problems = world.validate()
    if problems:
        for problem in problems:
            print(f"map error: {problem}", file=sys.stderr)
        return 1

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
    raise SystemExit(main())
