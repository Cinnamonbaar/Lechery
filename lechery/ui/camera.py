"""Where the view sits over a room.

Two behaviours, one rule: a room that fits the window is framed whole and
still -- the fixed-camera read, where the room is a composed picture and you
see the whole threat at once. A room bigger than the window follows the
player and clamps at the edges, so a town never shows the void past its wall.

Choosing between them by measurement rather than by a flag means a room
becomes a "big" room simply by being authored bigger.
"""

from __future__ import annotations


def offset_for(
    room_size_tiles: tuple[int, int],
    player_pos: tuple[float, float],
    window_size: tuple[int, int],
    scale: int,
) -> tuple[float, float]:
    """Pixel offset from room origin to screen origin."""
    return (
        _axis(room_size_tiles[0], player_pos[0], window_size[0], scale),
        _axis(room_size_tiles[1], player_pos[1], window_size[1], scale),
    )


def _axis(room_tiles: int, player: float, window_px: int, scale: int) -> float:
    room_px = room_tiles * scale
    if room_px <= window_px:
        # Fits: centre the room and hold still.
        return (window_px - room_px) / 2
    # Larger: follow the player, but never past the room's edge.
    ideal = window_px / 2 - player * scale
    return max(min(ideal, 0.0), window_px - room_px)
