/** Turning a Layout plus a TemplatePool into a real Area. */

import { Area } from "../world/area";
import { Role } from "../world/roles";
import { directionBetween, type Layout } from "./layout";
import type { Rng } from "./rng";
import type { TemplatePool } from "./templates";

export interface BuildAreaOptions {
  areaId: string;
  name: string;
  description?: string;
}

/**
 * Dress every node in `layout` with a room and wire up the exits.
 *
 * Room ids are namespaced with the area id (`tutorial:n3`) so that two
 * generated areas cannot collide in the World's global room registry.
 */
export function buildArea(
  layout: Layout,
  pool: TemplatePool,
  rng: Rng,
  { areaId, name, description = "" }: BuildAreaOptions,
): Area {
  pool.reset();
  const area = new Area(areaId, name, description);

  for (const node of layout) {
    const template = node.templateId ? pool.get(node.templateId) : pool.pick(node.role, rng);
    const room = template.build(`${areaId}:${node.id}`, node.role, rng);
    room.position = node.position;
    area.add(room);
  }

  for (const node of layout) {
    const room = area.room(`${areaId}:${node.id}`);
    for (const neighbour of layout.neighbours(node)) {
      const direction = directionBetween(node.position, neighbour.position);
      if (direction === null) {
        throw new Error(
          `Nodes ${node.id} and ${neighbour.id} are linked but not adjacent; ` +
            `layout.validate() would have caught this`,
        );
      }
      // Each node writes only its own outgoing exit; the neighbour writes
      // the return leg when its own turn comes.
      room.link(direction, `${areaId}:${neighbour.id}`);
    }
  }

  const entrance = layout.withRole(Role.ENTRANCE);
  if (entrance.length) area.entryRoomId = `${areaId}:${entrance[0]!.id}`;
  return area;
}
