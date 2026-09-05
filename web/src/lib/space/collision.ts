/**
 * Axis-separated AABB collision against a tilemap.
 *
 * Movement is resolved one axis at a time. This is the standard trick and the
 * reason is worth stating: resolving both axes together makes a body running
 * along a wall snag on every tile seam, because the diagonal move is rejected
 * whole. Solving x, then y, lets a blocked diagonal degrade into a slide.
 */

import type { TileMap } from "./tiles";

export type Point = readonly [number, number];

/** What a move ran into, if anything. */
export interface Hit {
  readonly x: boolean;
  readonly y: boolean;
}

export function boxBounds(
  position: Point,
  halfExtents: Point,
): [number, number, number, number] {
  return [
    position[0] - halfExtents[0],
    position[1] - halfExtents[1],
    position[0] + halfExtents[0],
    position[1] + halfExtents[1],
  ];
}

/** Whether a box at `position` intersects any solid tile. */
export function overlapsSolid(
  tilemap: TileMap,
  position: Point,
  halfExtents: Point,
): boolean {
  const [left, top, right, bottom] = boxBounds(position, halfExtents);
  // The epsilon keeps a box whose edge sits exactly on a tile boundary from
  // claiming to touch the next tile along.
  const epsilon = 1e-9;
  for (let ty = Math.floor(top); ty <= Math.floor(bottom - epsilon); ty += 1) {
    for (let tx = Math.floor(left); tx <= Math.floor(right - epsilon); tx += 1) {
      if (tilemap.isSolidAt(tx, ty)) return true;
    }
  }
  return false;
}

/** Move along one axis, snapping flush to the first solid tile hit. */
function sweepAxis(
  tilemap: TileMap,
  x: number,
  y: number,
  halfExtents: Point,
  delta: number,
  axis: 0 | 1,
): [number, boolean] {
  const current = axis === 0 ? x : y;
  if (delta === 0) return [current, false];

  const target = current + delta;
  let candidate: Point = axis === 0 ? [target, y] : [x, target];
  if (!overlapsSolid(tilemap, candidate, halfExtents)) return [target, false];

  // Snap flush against the blocking tile rather than refusing the move, so a
  // body can rest exactly on a wall instead of jittering a fraction away.
  const half = halfExtents[axis]!;
  let snapped: number;
  if (delta > 0) {
    snapped = Math.floor(target + half) - half;
  } else {
    snapped = Math.floor(target - half) + 1 + half;
  }

  candidate = axis === 0 ? [snapped, y] : [x, snapped];
  if (overlapsSolid(tilemap, candidate, halfExtents)) return [current, true];
  return [snapped, true];
}

/**
 * Move an axis-aligned box, stopping it at solid tiles.
 *
 * `position` is the box centre. Returns the resolved centre and which axes
 * were blocked.
 */
export function moveAndCollide(
  tilemap: TileMap,
  position: Point,
  halfExtents: Point,
  delta: Point,
): [Point, Hit] {
  const [x, blockedX] = sweepAxis(tilemap, position[0], position[1], halfExtents, delta[0], 0);
  const [y, blockedY] = sweepAxis(tilemap, x, position[1], halfExtents, delta[1], 1);
  return [[x, y], { x: blockedX, y: blockedY }];
}
