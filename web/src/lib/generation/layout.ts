/**
 * Layouts: the abstract shape of an area, before it has any content.
 *
 * A Layout is a graph of nodes on a grid. It knows how many rooms there are,
 * how they connect, and what each one is *for* -- and nothing about prose,
 * enemies or items. Keeping the shape separate from the content is what lets
 * one generator serve every area in the game.
 */

import { Direction } from "../world/direction";
import { Role } from "../world/roles";

/** Grid coordinate. +x is east, +y is south. */
export type Position = readonly [number, number];

/** Which Direction you travel to go from a position to an adjacent one. */
export const STEPS: readonly [Position, Direction][] = [
  [[0, -1], Direction.NORTH],
  [[0, 1], Direction.SOUTH],
  [[1, 0], Direction.EAST],
  [[-1, 0], Direction.WEST],
];

/** The compass direction from `origin` to an orthogonally adjacent cell. */
export function directionBetween(origin: Position, target: Position): Direction | null {
  const dx = target[0] - origin[0];
  const dy = target[1] - origin[1];
  for (const [[sx, sy], direction] of STEPS) {
    if (sx === dx && sy === dy) return direction;
  }
  return null;
}

const positionKey = (position: Position): string => `${position[0]},${position[1]}`;

/** One room-to-be. */
export class Node {
  /** Ids of adjacent nodes. Edges are stored on both nodes. */
  readonly links = new Set<string>();
  /**
   * Pins this node to a specific room template, bypassing random choice.
   * This is how a handcrafted room lives inside a generated layout.
   */
  templateId: string | null = null;
  /** Generator-specific extras the builder may consult. */
  readonly data = new Map<string, unknown>();

  constructor(
    readonly id: string,
    readonly position: Position,
    public role: Role = Role.PASSAGE,
  ) {}

  get degree(): number {
    return this.links.size;
  }

  get isDeadEnd(): boolean {
    return this.degree <= 1;
  }
}

/** A graph of nodes, addressable by id or by grid position. */
export class Layout {
  readonly nodes = new Map<string, Node>();
  private readonly byPosition = new Map<string, string>();

  // -- building -----------------------------------------------------------

  add(node: Node): Node {
    if (this.nodes.has(node.id)) throw new Error(`Duplicate node id ${node.id}`);
    const key = positionKey(node.position);
    if (this.byPosition.has(key)) {
      throw new Error(`Two nodes occupy ${key}`);
    }
    this.nodes.set(node.id, node);
    this.byPosition.set(key, node.id);
    return node;
  }

  /** Link two nodes both ways. */
  connect(a: string | Node, b: string | Node): void {
    const first = typeof a === "string" ? this.node(a) : a;
    const second = typeof b === "string" ? this.node(b) : b;
    if (first === second) throw new Error(`Node ${first.id} cannot link to itself`);
    first.links.add(second.id);
    second.links.add(first.id);
  }

  // -- lookup -------------------------------------------------------------

  node(id: string): Node {
    const found = this.nodes.get(id);
    if (!found) throw new Error(`No node ${id} in layout`);
    return found;
  }

  at(position: Position): Node | undefined {
    const id = this.byPosition.get(positionKey(position));
    return id ? this.nodes.get(id) : undefined;
  }

  isFree(position: Position): boolean {
    return !this.byPosition.has(positionKey(position));
  }

  neighbours(node: Node): Node[] {
    return [...node.links].map((id) => this.node(id));
  }

  withRole(role: Role): Node[] {
    return [...this.nodes.values()].filter((node) => node.role === role);
  }

  deadEnds(): Node[] {
    return [...this.nodes.values()].filter((node) => node.isDeadEnd);
  }

  /** (minX, minY, maxX, maxY) of occupied cells. */
  get bounds(): [number, number, number, number] {
    const nodes = [...this.nodes.values()];
    if (nodes.length === 0) return [0, 0, 0, 0];
    const xs = nodes.map((node) => node.position[0]);
    const ys = nodes.map((node) => node.position[1]);
    return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
  }

  get size(): number {
    return this.nodes.size;
  }

  [Symbol.iterator](): IterableIterator<Node> {
    return this.nodes.values();
  }

  // -- integrity ----------------------------------------------------------

  /**
   * Whether every node is reachable from any other.
   *
   * A generator that produces an unreachable room has produced a bug the
   * player will find eventually; this makes it a test failure instead.
   */
  isConnected(): boolean {
    if (this.nodes.size === 0) return true;
    const start = this.nodes.keys().next().value as string;
    const seen = new Set([start]);
    const frontier = [start];
    while (frontier.length) {
      const current = this.node(frontier.pop()!);
      for (const neighbour of current.links) {
        if (!seen.has(neighbour)) {
          seen.add(neighbour);
          frontier.push(neighbour);
        }
      }
    }
    return seen.size === this.nodes.size;
  }

  validate(): string[] {
    const problems: string[] = [];
    for (const node of this.nodes.values()) {
      for (const otherId of node.links) {
        const other = this.nodes.get(otherId);
        if (!other) {
          problems.push(`${node.id}: links to unknown node ${otherId}`);
          continue;
        }
        if (!other.links.has(node.id)) {
          problems.push(`${node.id} -> ${otherId}: link is not mutual`);
        }
        if (directionBetween(node.position, other.position) === null) {
          problems.push(`${node.id} -> ${otherId}: linked nodes are not adjacent`);
        }
      }
    }
    if (!this.isConnected()) problems.push("layout is not fully connected");
    return problems;
  }
}
