/**
 * The starter dungeon: generated layout, handcrafted bookends.
 *
 * The shape shuffles each run so the tutorial is not memorised, but the first
 * and last rooms are pinned templates -- those two carry the opening beat and
 * the hand-off to the plains, and neither survives being random.
 *
 * The prose here is placeholder. It is written to the right length and tone so
 * layout work can be judged, not to be kept.
 */

import {
  buildArea,
  type DungeonShape,
  generateDungeon,
  type Layout,
  type Rng,
  RoomTemplate,
  TemplatePool,
} from "../../generation";
import { type Area, Role } from "../../world";

export const AREA_ID = "tutorial";

export const SHAPE: DungeonShape = {
  criticalPath: [6, 8],
  branches: [2, 3],
  branchLength: [1, 2],
  bossBeforeExit: true,
  combatDensity: 0.45,
  treasureChance: 0.8,
};

export function templatePool(): TemplatePool {
  return new TemplatePool([
    new RoomTemplate("tut_entrance", "Where You Woke", {
      roles: [Role.ENTRANCE],
      unique: true,
      tags: ["indoors", "safe"],
      descriptions: [
        "You come to on cold flagstones with no memory of lying down on " +
          "them. The chamber is round, roofless, and open to a sky the wrong " +
          "colour for any hour you remember. One passage leads out.",
      ],
    }),
    new RoomTemplate("tut_hall", "Collapsed Hall", {
      roles: [Role.PASSAGE],
      weight: 2,
      tags: ["indoors"],
      descriptions: [
        "Pillars stand in two rows, or did; half have come down and lie " +
          "where they fell. Dust hangs in the air as though recently " +
          "disturbed.",
        "The ceiling has given way at the far end, letting in a shaft of " +
          "pale light and a slow trickle of soil.",
      ],
    }),
    new RoomTemplate("tut_cistern", "Dry Cistern", {
      roles: [Role.PASSAGE, Role.COMBAT],
      tags: ["indoors", "trapped"],
      descriptions: [
        "A basin sunk into the floor, empty but for a crust of salt and " +
          "something's shed skin.",
      ],
    }),
    new RoomTemplate("tut_guardroom", "Guardroom", {
      roles: [Role.COMBAT],
      weight: 1.5,
      tags: ["indoors", "trapped"],
      descriptions: [
        "Racks line the walls, their weapons long since taken. Something has " +
          "made a nest of the straw in the corner.",
        "Benches, a cold hearth, and four sets of boots left neatly by the " +
          "door. Their owners did not come back for them.",
      ],
    }),
    new RoomTemplate("tut_cache", "Storeroom", {
      roles: [Role.TREASURE],
      tags: ["indoors"],
      descriptions: [
        "Shelves, mostly bare. Mostly.",
        "A supply room the looters missed, or could not reach. One crate " +
          "remains intact.",
      ],
    }),
    new RoomTemplate("tut_shrine", "Defaced Shrine", {
      roles: [Role.TREASURE, Role.SET_PIECE],
      unique: true,
      tags: ["indoors"],
      descriptions: [
        "Someone has taken a chisel to every face on the wall relief, " +
          "patiently, one at a time. The offering bowl is not empty.",
      ],
    }),
    new RoomTemplate("tut_boss", "The Long Gallery", {
      roles: [Role.BOSS],
      unique: true,
      tags: ["indoors"],
      descriptions: [
        "The passage opens out into a gallery long enough that the far end " +
          "is dark. Something between you and it shifts its weight, and waits.",
      ],
    }),
    new RoomTemplate("tut_gate", "The Broken Gate", {
      roles: [Role.EXIT],
      unique: true,
      tags: ["indoors", "safe"],
      descriptions: [
        "The doors were torn off their hinges from the inside. Past them the " +
          "tunnel rises, and there is grass growing in the seams of the " +
          "steps -- real grass, real light. Whatever this place was, it ends " +
          "here.",
      ],
    }),
  ]);
}

/** Returns the area and the layout it came from; the carver needs both. */
export function build(rng: Rng): [Area, Layout] {
  const layout = generateDungeon(rng, SHAPE, "t");

  // Pin the bookends. The generator guarantees exactly one ENTRANCE and, for
  // a path of any length, one EXIT; a degenerate one-room layout would have
  // neither pinned, which validate() will catch loudly.
  for (const node of layout.withRole(Role.ENTRANCE)) node.templateId = "tut_entrance";
  for (const node of layout.withRole(Role.EXIT)) node.templateId = "tut_gate";
  for (const node of layout.withRole(Role.BOSS)) node.templateId = "tut_boss";

  const area = buildArea(layout, templatePool(), rng, {
    areaId: AREA_ID,
    name: "The Undercroft",
    description: "Somewhere under the plains, and older than them.",
  });
  return [area, layout];
}
