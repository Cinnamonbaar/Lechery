/**
 * The plains: the hub. Fully handcrafted, same pipeline as the dungeon.
 *
 * Every node here pins a template and every position is chosen by hand, so the
 * "generator" does no generating -- it just dresses and wires. That is the
 * point: the hub gets the builder's exit-wiring and id-namespacing for free
 * without inheriting any randomness.
 *
 * Later areas branch off the crossroads. Keeping the hub small and its exits
 * explicit is what makes adding a spoke a two-line change.
 */

import {
  buildArea,
  Layout,
  Node,
  type Position,
  type Rng,
  RoomTemplate,
  TemplatePool,
} from "../../generation";
import { type Area, Role } from "../../world";

export const AREA_ID = "plains";

interface Place {
  readonly id: string;
  readonly position: Position;
  readonly role: Role;
  readonly templateId: string;
}

export const PLACES: readonly Place[] = [
  { id: "undergate", position: [0, 2], role: Role.ENTRANCE, templateId: "plains_undergate" },
  { id: "crossroads", position: [0, 1], role: Role.PASSAGE, templateId: "plains_crossroads" },
  { id: "road_west", position: [-1, 1], role: Role.PASSAGE, templateId: "plains_road" },
  { id: "gate", position: [0, 0], role: Role.PASSAGE, templateId: "plains_gate" },
  { id: "square", position: [1, 0], role: Role.HAVEN, templateId: "town_square" },
];

/** Undirected edges between the places above. */
export const ROADS: readonly (readonly [string, string])[] = [
  ["undergate", "crossroads"],
  ["crossroads", "road_west"],
  ["crossroads", "gate"],
  ["gate", "square"],
];

export function templatePool(): TemplatePool {
  return new TemplatePool([
    new RoomTemplate("plains_undergate", "The Sunken Door", {
      roles: [Role.ENTRANCE],
      tags: ["outdoors", "safe"],
      descriptions: [
        "You come up out of the dark into grass to your knees and a sky that " +
          "goes on without interruption in every direction. Behind you the " +
          "stair drops back down into the hill. Ahead the land is flat, and " +
          "green, and enormous.",
      ],
    }),
    new RoomTemplate("plains_crossroads", "The Crossroads", {
      size: [37, 23],
      tags: ["outdoors", "safe"],
      descriptions: [
        "Two cart tracks meet in the grass and a leaning post marks the spot, " +
          "its signboards long since taken for firewood. North stands a " +
          "walled town. The western road runs off toward nothing you can make " +
          "out from here.",
      ],
    }),
    new RoomTemplate("plains_road", "The Western Road", {
      tags: ["outdoors"],
      descriptions: [
        "The track thins to a footpath and then to an idea of a footpath. " +
          "Whatever is out this way, it is further than one day's walk.",
      ],
    }),
    new RoomTemplate("plains_gate", "Town Gate", {
      tags: ["outdoors", "safe"],
      descriptions: [
        "The wall is high, well kept, and manned -- the first evidence you " +
          "have seen that anyone in this place expects to be here tomorrow. " +
          "The gate stands open.",
      ],
    }),
    new RoomTemplate("town_square", "Market Square", {
      roles: [Role.HAVEN],
      // Larger than the screen on purpose: the town is where the camera stops
      // framing a room and starts following the player. Everything else about
      // it carves identically.
      size: [49, 33],
      tags: ["indoors", "safe", "town"],
      descriptions: [
        "Stalls, a well, and a good deal of noise. People here look at you " +
          "the way people look at weather coming in off the plain: with " +
          "interest, and no particular alarm.",
      ],
    }),
  ]);
}

export function layout(): Layout {
  const hub = new Layout();
  for (const place of PLACES) {
    const node = hub.add(new Node(place.id, place.position, place.role));
    node.templateId = place.templateId;
  }
  for (const [a, b] of ROADS) hub.connect(a, b);
  return hub;
}

export function build(rng: Rng): [Area, Layout] {
  const hub = layout();
  const area = buildArea(hub, templatePool(), rng, {
    areaId: AREA_ID,
    name: "The Plains",
    description: "Open country, and the town that sits in the middle of it.",
  });
  return [area, hub];
}
