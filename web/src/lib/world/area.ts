/** Areas: named regions that own a set of rooms. */

import { Role } from "./roles";
import { Room, type RoomOptions } from "./room";

/**
 * A region of the map.
 *
 * Areas exist so that region-wide properties have somewhere to live --
 * ambient track, encounter table, danger rating, a corruption modifier --
 * without every room carrying a copy.
 */
export class Area {
  /** Rooms keyed by room id, in insertion order. */
  readonly rooms = new Map<string, Room>();
  /** Room the player arrives at when entering the area from elsewhere. */
  entryRoomId: string | null = null;
  readonly tags = new Set<string>();

  constructor(
    readonly id: string,
    readonly name: string,
    readonly description = "",
  ) {}

  /** Adopt a room into this area. */
  add(room: Room): Room {
    if (this.rooms.has(room.id)) {
      throw new Error(`Area ${this.id} already has a room ${room.id}`);
    }
    room.areaId = this.id;
    this.rooms.set(room.id, room);
    // An explicit ENTRANCE always wins; otherwise the first room added is
    // the entry point, which is right for small handmade areas.
    if (this.entryRoomId === null || room.role === Role.ENTRANCE) {
      this.entryRoomId = room.id;
    }
    return room;
  }

  /** Construct a plain Room and adopt it in one call. */
  makeRoom(id: string, name: string, options: RoomOptions = {}): Room {
    return this.add(new Room(id, name, options));
  }

  room(id: string): Room {
    const found = this.rooms.get(id);
    if (!found) throw new Error(`No room ${id} in area ${this.id}`);
    return found;
  }

  /**
   * Every room in the area serving `role`.
   *
   * This is how the rest of the game addresses a generated area: an exit
   * room has no stable id when the layout is random, but it always has a role.
   */
  roomsWithRole(role: Role): Room[] {
    return [...this.rooms.values()].filter((room) => room.role === role);
  }

  firstWithRole(role: Role): Room | undefined {
    return [...this.rooms.values()].find((room) => room.role === role);
  }

  get entryRoom(): Room | undefined {
    return this.entryRoomId ? this.rooms.get(this.entryRoomId) : undefined;
  }

  get size(): number {
    return this.rooms.size;
  }

  [Symbol.iterator](): IterableIterator<Room> {
    return this.rooms.values();
  }
}
