/**
 * Assembling a new game world.
 *
 * Area *content* lives in `content/areas`; this module owns the world map --
 * which areas exist, how they join, and where the portals between them sit.
 * When a new area branches off the hub it is registered here and nowhere else.
 */

import { rngFor } from "../generation";
import { buildLevel, type Level } from "../space";
import { Direction, Role, World } from "../world";
import * as plains from "./areas/plains";
import * as tutorial from "./areas/tutorial";

const AREA_MODULES = [tutorial, plains] as const;

/** Where a new game begins. */
export const START_AREA = tutorial.AREA_ID;

export interface BuiltWorld {
  readonly world: World;
  readonly levels: Map<string, Level>;
}

/**
 * Build a fresh world and its floorplans.
 *
 * The same seed always yields the same map, layout and carving alike.
 */
export function newWorld(seed: number | null = null): BuiltWorld {
  const masterSeed = seed ?? Math.floor(Math.random() * 2 ** 31);

  const world = new World(masterSeed);
  const levels = new Map<string, Level>();

  const areas = AREA_MODULES.map((module) => {
    const [area] = module.build(rngFor(masterSeed, module.AREA_ID));
    world.addArea(area);
    return area;
  });

  // Rooms are carved after every area is joined, because a room's doorways
  // are cut from its exits -- carving earlier would miss the exits that join
  // one area to the next.
  joinAreas(world);
  for (const area of areas) {
    levels.set(area.id, buildLevel(area, rngFor(masterSeed, `${area.id}:carve`)));
  }

  placePortals(world, levels);

  const problems = world.validate();
  if (problems.length) {
    throw new Error(
      `generated an invalid world (seed ${masterSeed}):\n  ${problems.join("\n  ")}`,
    );
  }
  return { world, levels };
}

/**
 * Give every non-compass link something physical to step on.
 *
 * A link the player cannot reach on foot is worse than no link, so the portals
 * are derived from the exits rather than written out by hand: any exit whose
 * key is not a wall direction gets one.
 */
function placePortals(world: World, levels: Map<string, Level>): void {
  const walls: readonly string[] = [
    Direction.NORTH,
    Direction.SOUTH,
    Direction.EAST,
    Direction.WEST,
  ];
  for (const room of world.rooms) {
    for (const exit of room.exits.values()) {
      if (walls.includes(exit.keyString)) continue;
      if (room.areaId === null) continue;
      levels.get(room.areaId)?.addPortal(room.id, exit.target, exit.displayLabel);
    }
  }
}

/**
 * Stitch the area graph together.
 *
 * Areas are joined by role rather than by room id, because a generated area's
 * exit room has a different id every run.
 */
function joinAreas(world: World): void {
  const dungeonExit = world.area(tutorial.AREA_ID).firstWithRole(Role.EXIT);
  const hubEntrance = world.area(plains.AREA_ID).entryRoom;
  if (!dungeonExit || !hubEntrance) {
    throw new Error("the starter dungeon and the hub must both be reachable");
  }
  dungeonExit.connect(Direction.UP, hubEntrance, { label: "Climb toward the light" });
}
