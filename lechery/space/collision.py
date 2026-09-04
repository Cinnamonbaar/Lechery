"""Axis-separated AABB collision against a tilemap.

Movement is resolved one axis at a time. This is the standard trick and the
reason is worth stating: resolving both axes together makes a body running
along a wall snag on every tile seam, because the diagonal move is rejected
whole. Solving x, then y, lets a blocked diagonal degrade into a slide.
"""

from __future__ import annotations

from dataclasses import dataclass

from .tiles import TileMap

#: World units per tile. One tile is one unit; pixels are the renderer's
#: problem, so nothing in this module knows about them.
TILE = 1.0


@dataclass(frozen=True)
class Hit:
    """What a move ran into, if anything."""

    x: bool = False
    y: bool = False

    @property
    def any(self) -> bool:
        return self.x or self.y


def move_and_collide(
    tilemap: TileMap,
    position: tuple[float, float],
    half_extents: tuple[float, float],
    delta: tuple[float, float],
) -> tuple[tuple[float, float], Hit]:
    """Move an axis-aligned box, stopping it at solid tiles.

    `position` is the box centre. Returns the resolved centre and which axes
    were blocked.
    """
    x, y = position
    dx, dy = delta

    x, hit_x = _sweep_axis(tilemap, x, y, half_extents, dx, axis=0)
    y, hit_y = _sweep_axis(tilemap, x, y, half_extents, dy, axis=1)
    return (x, y), Hit(hit_x, hit_y)


def _sweep_axis(
    tilemap: TileMap,
    x: float,
    y: float,
    half_extents: tuple[float, float],
    delta: float,
    *,
    axis: int,
) -> tuple[float, bool]:
    """Move along one axis, snapping flush to the first solid tile hit."""
    current = x if axis == 0 else y
    if delta == 0.0:
        return current, False

    target = current + delta
    candidate = (target, y) if axis == 0 else (x, target)
    if not overlaps_solid(tilemap, candidate, half_extents):
        return target, False

    # Snap flush against the blocking tile rather than refusing the move, so
    # a body can rest exactly on a wall instead of jittering a fraction away.
    half = half_extents[axis]
    if delta > 0:
        edge = target + half
        snapped = float(int(edge)) - half
    else:
        edge = target - half
        snapped = float(int(edge) + 1) + half

    candidate = (snapped, y) if axis == 0 else (x, snapped)
    if overlaps_solid(tilemap, candidate, half_extents):
        return current, True
    return snapped, True


def overlaps_solid(
    tilemap: TileMap, position: tuple[float, float], half_extents: tuple[float, float]
) -> bool:
    """Whether a box at `position` intersects any solid tile."""
    left, top, right, bottom = box_bounds(position, half_extents)
    #: `- 1e-9` keeps a box whose edge sits exactly on a tile boundary from
    #: claiming to touch the next tile along.
    for ty in range(int(top), int(bottom - 1e-9) + 1):
        for tx in range(int(left), int(right - 1e-9) + 1):
            if tilemap.is_solid(tx, ty):
                return True
    return False


def box_bounds(
    position: tuple[float, float], half_extents: tuple[float, float]
) -> tuple[float, float, float, float]:
    x, y = position
    hx, hy = half_extents
    return (x - hx, y - hy, x + hx, y + hy)
