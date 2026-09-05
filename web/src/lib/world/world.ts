/** The World: the room registry and the movement rules that act on it. */

import { Area } from "./area";
import type { Direction } from "./direction";
import type { Exit } from "./exits";
import type { Room } from "./room";

/**
 * The outcome of an attempted move.
 *
 * Returned rather than thrown because a refused move is ordinary gameplay,
 * not an error: the UI wants a message to print either way.
 */
export interface MoveResult {
  readonly ok: boolean;
  readonly message: string;
  readonly room?: Room;
  readonly previous?: Room;
  readonly exit?: Exit;
}

/**
 * Owns every area and room, and is the only thing that moves an actor.
 *
 * Rooms hold ids rather than object references, so this class is what turns
 * an id into a room. That indirection is what lets content modules define
 * rooms in any order and reference each other freely.
 */
export class World {
  readonly areas = new Map<string, Area>();
  private readonly roomsById = new Map<string, Room>();
  currentRoom: Room | null = null;

  constructor(
    /**
     * The master seed every area's layout was derived from. Kept on the world
     * so a save file can record it and rebuild the same map.
     */
    readonly seed: number | null = null,
  ) {}

  // -- registration -------------------------------------------------------

  addArea(area: Area): Area {
    if (this.areas.has(area.id)) throw new Error(`Duplicate area id ${area.id}`);
    this.areas.set(area.id, area);
    for (const room of area) {
      if (this.roomsById.has(room.id)) {
        throw new Error(`Duplicate room id ${room.id}`);
      }
      this.roomsById.set(room.id, room);
    }
    return area;
  }

  // -- lookup -------------------------------------------------------------

  room(id: string): Room {
    const found = this.roomsById.get(id);
    if (!found) throw new Error(`No room registered with id ${id}`);
    return found;
  }

  area(id: string): Area {
    const found = this.areas.get(id);
    if (!found) throw new Error(`No area registered with id ${id}`);
    return found;
  }

  areaOf(room: Room): Area | undefined {
    return room.areaId ? this.areas.get(room.areaId) : undefined;
  }

  get rooms(): Room[] {
    return [...this.roomsById.values()];
  }

  has(roomId: string): boolean {
    return this.roomsById.has(roomId);
  }

  // -- movement -----------------------------------------------------------

  /**
   * Put the actor in a room directly, ignoring exits.
   *
   * For starting the game, teleports, and scripted scene changes.
   */
  place(room: Room | string, actor: unknown = null): MoveResult {
    const destination = typeof room === "string" ? this.room(room) : room;
    const previous = this.currentRoom ?? undefined;
    previous?.leave(actor);
    this.currentRoom = destination;
    destination.enter(actor);
    return { ok: true, message: "", room: destination, previous };
  }

  /** Attempt to travel from the current room along `key`. */
  move(key: Direction | string, actor: unknown = null): MoveResult {
    const origin = this.currentRoom;
    if (!origin) return { ok: false, message: "You are nowhere." };

    const exit = origin.exitFor(key);
    if (!exit) return { ok: false, message: "You can't go that way." };

    if (!exit.isOpen(actor)) {
      return { ok: false, message: exit.blockedMessage, exit };
    }

    if (!this.has(exit.target)) {
      throw new Error(
        `Exit ${exit.keyString} from room ${origin.id} points at ` +
          `unregistered room ${exit.target}`,
      );
    }

    const destination = this.room(exit.target);
    origin.leave(actor);
    this.currentRoom = destination;
    destination.enter(actor);
    return {
      ok: true,
      message: `You go ${exit.displayLabel.toLowerCase()}.`,
      room: destination,
      previous: origin,
      exit,
    };
  }

  // -- integrity ----------------------------------------------------------

  /**
   * Report structural problems in the map.
   *
   * Cheap to run on startup and in tests; catches the failure mode this
   * design invites, which is an exit naming a room id that never got
   * registered (a typo, or a content module that was not imported).
   */
  validate(): string[] {
    const problems: string[] = [];
    for (const room of this.rooms) {
      for (const exit of room.exits.values()) {
        if (!this.has(exit.target)) {
          problems.push(`${room.id}: exit ${exit.keyString} -> unknown room ${exit.target}`);
        } else if (exit.target === room.id) {
          problems.push(`${room.id}: exit ${exit.keyString} leads to itself`);
        }
      }
    }
    for (const area of this.areas.values()) {
      if (area.entryRoomId && !area.rooms.has(area.entryRoomId)) {
        problems.push(`${area.id}: entry room ${area.entryRoomId} is not in the area`);
      }
    }
    return problems;
  }
}
