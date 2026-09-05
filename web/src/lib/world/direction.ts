/**
 * Compass directions used by room exits.
 *
 * Directions are optional: an exit can be keyed by a Direction (a physical
 * "go north") or by an arbitrary string ("descend", "crawl through the gap").
 * Keeping both in one keyspace means the UI can render them uniformly.
 */

export const Direction = {
  NORTH: "north",
  SOUTH: "south",
  EAST: "east",
  WEST: "west",
  UP: "up",
  DOWN: "down",
  IN: "in",
  OUT: "out",
} as const;

export type Direction = (typeof Direction)[keyof typeof Direction];

const OPPOSITES: Record<Direction, Direction> = {
  north: Direction.SOUTH,
  south: Direction.NORTH,
  east: Direction.WEST,
  west: Direction.EAST,
  up: Direction.DOWN,
  down: Direction.UP,
  in: Direction.OUT,
  out: Direction.IN,
};

export function opposite(direction: Direction): Direction {
  return OPPOSITES[direction];
}

export function directionLabel(direction: Direction): string {
  return direction.charAt(0).toUpperCase() + direction.slice(1);
}

export function isDirection(value: string): value is Direction {
  return value in OPPOSITES;
}

/** Normalise a direction or free-form exit name into a key. */
export function asKey(value: Direction | string): string {
  return String(value).trim().toLowerCase();
}
