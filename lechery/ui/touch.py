"""An on-screen movement stick, for playing without a keyboard.

Drawn only when the layout expects touch, or when the player has forced it
on. It is a floating stick: it appears wherever the finger lands inside its
zone rather than at a fixed spot, because a fixed stick means looking down
to find it, and on a small screen the thumb is already covering it.
"""

from __future__ import annotations

import math
from typing import Optional

import pygame

from .metrics import px

BASE = (210, 205, 215, 46)
BASE_EDGE = (220, 214, 226, 78)
KNOB = (222, 216, 228, 130)

#: Finger travel, in pixels, for full input.
RADIUS = 62

#: How much of the window's lower-left quadrant listens for the stick.
ZONE_FRACTION = (0.5, 0.55)


class Thumbstick:
    """Reports a direction vector from a drag in its zone."""

    def __init__(self) -> None:
        self.origin: Optional[tuple[float, float]] = None
        self.current: Optional[tuple[float, float]] = None
        self.finger: Optional[int] = None

    # -- input ------------------------------------------------------------

    def zone(self, window: tuple[int, int]) -> pygame.Rect:
        width, height = window
        zone_w = int(width * ZONE_FRACTION[0])
        zone_h = int(height * ZONE_FRACTION[1])
        return pygame.Rect(0, height - zone_h, zone_w, zone_h)

    def handle_event(self, event: pygame.event.Event, window: tuple[int, int]) -> bool:
        """Consume touch or mouse drags in the stick's zone."""
        position, finger, phase = _read(event, window)
        if phase is None:
            return False

        if phase == "down":
            if self.origin is None and self.zone(window).collidepoint(position):
                self.origin = position
                self.current = position
                self.finger = finger
                return True
            return False

        if self.finger != finger:
            return False

        if phase == "move":
            self.current = position
            return True

        self.origin = self.current = self.finger = None
        return True

    # -- output -----------------------------------------------------------

    @property
    def active(self) -> bool:
        return self.origin is not None

    def direction(self) -> tuple[float, float]:
        """A vector of magnitude 0..1. Zero when the stick is not held."""
        if self.origin is None or self.current is None:
            return (0.0, 0.0)
        dx = self.current[0] - self.origin[0]
        dy = self.current[1] - self.origin[1]
        distance = math.hypot(dx, dy)
        if distance < px(6):  # a dead zone, so a tap is not a twitch
            return (0.0, 0.0)
        radius = px(RADIUS)
        scale = min(distance, radius) / distance
        return (dx * scale / radius, dy * scale / radius)

    # -- drawing ----------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if self.origin is None or self.current is None:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(overlay, BASE, self.origin, px(RADIUS))
        pygame.draw.circle(overlay, BASE_EDGE, self.origin, px(RADIUS), width=px(2))

        dx, dy = self.direction()
        knob = (self.origin[0] + dx * px(RADIUS), self.origin[1] + dy * px(RADIUS))
        pygame.draw.circle(overlay, KNOB, knob, px(RADIUS) * 0.38)
        surface.blit(overlay, (0, 0))


def _read(
    event: pygame.event.Event, window: tuple[int, int]
) -> tuple[tuple[float, float], object, Optional[str]]:
    """Normalise touch and mouse events into (position, id, phase).

    Touch events carry normalised coordinates; mouse events carry pixels.
    Handling both here means the stick works under a finger on a phone and
    under a cursor on a desktop, which is also how it gets tested.
    """
    if event.type == pygame.FINGERDOWN:
        return ((event.x * window[0], event.y * window[1]), event.finger_id, "down")
    if event.type == pygame.FINGERMOTION:
        return ((event.x * window[0], event.y * window[1]), event.finger_id, "move")
    if event.type == pygame.FINGERUP:
        return ((event.x * window[0], event.y * window[1]), event.finger_id, "up")
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        return (event.pos, "mouse", "down")
    if event.type == pygame.MOUSEMOTION:
        return (event.pos, "mouse", "move")
    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        return (event.pos, "mouse", "up")
    return ((0.0, 0.0), None, None)
