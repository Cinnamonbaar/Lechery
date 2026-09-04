"""The player's on-map body: a grey shadowed humanoid.

Deliberately anonymous. The character's appearance changes constantly and is
the paperdoll view's job -- putting any of it here would mean regenerating a
sprite every time a trait changed, and would fight the top-down read, where
what matters is where a body is and which way it is facing, not what it looks
like. So: a silhouette, drawn once and rotated.
"""

from __future__ import annotations

import math

import pygame

SHADOW = (0, 0, 0, 90)
BODY = (108, 108, 118)
BODY_EDGE = (58, 58, 66)
HEAD = (138, 138, 148)


def build_silhouette(size: int) -> pygame.Surface:
    """Draw a humanoid seen from above, facing east (0 radians).

    Cached by the caller and rotated per frame; rebuilding this every frame
    would be the single most expensive thing on screen.
    """
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    centre = size / 2

    # Shoulders: an ellipse wider across the body than along the facing.
    shoulder = pygame.Rect(0, 0, size * 0.52, size * 0.66)
    shoulder.center = (centre, centre)
    pygame.draw.ellipse(surface, BODY, shoulder)
    pygame.draw.ellipse(surface, BODY_EDGE, shoulder, width=max(1, size // 24))

    # Head, pushed forward along the facing so the direction reads at a
    # glance even when the body is still.
    radius = size * 0.17
    pygame.draw.circle(surface, HEAD, (centre + size * 0.08, centre), radius)
    pygame.draw.circle(surface, BODY_EDGE, (centre + size * 0.08, centre), radius, width=max(1, size // 28))
    return surface


def draw_actor(
    surface: pygame.Surface,
    silhouette: pygame.Surface,
    screen_pos: tuple[float, float],
    facing: float,
    scale: float,
) -> None:
    """Blit a shadow and the rotated silhouette at `screen_pos`."""
    x, y = screen_pos

    shadow = pygame.Surface((int(scale * 0.7), int(scale * 0.4)), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, SHADOW, shadow.get_rect())
    surface.blit(shadow, shadow.get_rect(center=(x, y + scale * 0.18)))

    # pygame rotates counter-clockwise and screen y grows downward, so the
    # angle has to be negated to match the world's facing convention.
    rotated = pygame.transform.rotate(silhouette, -math.degrees(facing))
    surface.blit(rotated, rotated.get_rect(center=(x, y)))
