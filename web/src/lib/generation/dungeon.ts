/**
 * A dungeon layout generator: critical path plus branches.
 *
 * The algorithm is deliberately not a maze. Mazes are hostile to a game where
 * the player reads prose in every room -- they generate long stretches of
 * nothing. Instead it carves one guaranteed route from entrance to exit (the
 * critical path), then hangs short dead-end branches off it for optional
 * rewards. That gives a shape you can reason about: the player cannot get
 * lost for long, and every dead end is a promise of something worth finding.
 */

import { Role } from "../world/roles";
import { Layout, Node, type Position, STEPS } from "./layout";
import type { Rng } from "./rng";

/** Tuning for `generateDungeon`. All lengths are in rooms. */
export interface DungeonShape {
  /** Rooms on the guaranteed entrance-to-exit route, inclusive of both. */
  criticalPath: readonly [number, number];
  /** How many optional dead-end branches to attempt. */
  branches: readonly [number, number];
  /** Rooms per branch. */
  branchLength: readonly [number, number];
  /** Give the last critical-path room before the exit a BOSS role. */
  bossBeforeExit: boolean;
  /** Chance that a non-special critical-path room is a COMBAT room. */
  combatDensity: number;
  /** Chance a branch dead end holds treasure rather than a fight. */
  treasureChance: number;
}

export const DEFAULT_SHAPE: DungeonShape = {
  criticalPath: [6, 9],
  branches: [2, 4],
  branchLength: [1, 2],
  bossBeforeExit: false,
  combatDensity: 0.5,
  treasureChance: 0.75,
};

/** Sequential node ids, so a layout's ids are stable for a given seed. */
class Counter {
  private count = 0;
  constructor(private readonly prefix: string) {}
  next(): string {
    return `${this.prefix}${this.count++}`;
  }
}

/**
 * Unoccupied orthogonal neighbours, shuffled.
 *
 * Only empty cells are returned, so the walk never creates a loop. Every
 * layout this produces is a tree, which is what keeps dead ends meaningful.
 */
function freeNeighbours(layout: Layout, position: Position, rng: Rng): Position[] {
  const options: Position[] = [];
  for (const [[dx, dy]] of STEPS) {
    const candidate: Position = [position[0] + dx, position[1] + dy];
    if (layout.isFree(candidate)) options.push(candidate);
  }
  return rng.shuffle(options);
}

/** A self-avoiding random walk from the entrance. */
function carveCriticalPath(
  layout: Layout,
  shape: DungeonShape,
  rng: Rng,
  counter: Counter,
): Node[] {
  const targetLength = rng.int(shape.criticalPath[0], shape.criticalPath[1]);
  const start = layout.add(new Node(counter.next(), [0, 0], Role.ENTRANCE));
  const path = [start];

  while (path.length < targetLength) {
    const current = path[path.length - 1]!;
    const options = freeNeighbours(layout, current.position, rng);
    if (options.length === 0) {
      // Walked into a corner. Back up and try a different turn; if the
      // whole path is boxed in, stop short rather than loop forever.
      if (path.length === 1) break;
      path.pop();
      continue;
    }
    const node = layout.add(new Node(counter.next(), options[0]!));
    layout.connect(current, node);
    path.push(node);
  }

  return path;
}

function assignPathRoles(path: Node[], shape: DungeonShape, rng: Rng): void {
  path[0]!.role = Role.ENTRANCE;
  if (path.length < 2) return;
  path[path.length - 1]!.role = Role.EXIT;

  let middle = path.slice(1, -1);
  if (shape.bossBeforeExit && middle.length) {
    middle[middle.length - 1]!.role = Role.BOSS;
    middle = middle.slice(0, -1);
  }

  for (const node of middle) {
    node.role = rng.next() < shape.combatDensity ? Role.COMBAT : Role.PASSAGE;
  }
}

function carveSpur(
  layout: Layout,
  root: Node,
  length: number,
  rng: Rng,
  counter: Counter,
): Node[] {
  const spur: Node[] = [];
  let current = root;
  for (let step = 0; step < length; step += 1) {
    const options = freeNeighbours(layout, current.position, rng);
    if (options.length === 0) break;
    const node = layout.add(new Node(counter.next(), options[0]!));
    layout.connect(current, node);
    spur.push(node);
    current = node;
  }
  return spur;
}

/**
 * Hang dead-end spurs off the critical path.
 *
 * Branch roots are drawn from the middle of the path: branching off the
 * entrance makes the first choice meaningless, and off the exit makes the
 * reward pointless once you have already finished.
 */
function carveBranches(
  layout: Layout,
  path: Node[],
  shape: DungeonShape,
  rng: Rng,
  counter: Counter,
): void {
  const candidates = path.slice(1, -1).length ? path.slice(1, -1) : path;
  const attempts = rng.int(shape.branches[0], shape.branches[1]);

  for (let index = 0; index < attempts; index += 1) {
    const root = rng.pick(candidates);
    const length = rng.int(shape.branchLength[0], shape.branchLength[1]);
    const spur = carveSpur(layout, root, length, rng, counter);
    if (!spur.length) continue;
    const tip = spur[spur.length - 1]!;
    tip.role = rng.next() < shape.treasureChance ? Role.TREASURE : Role.COMBAT;
  }
}

/** Build a dungeon layout. Same rng seed, same layout. */
export function generateDungeon(
  rng: Rng,
  shape: Partial<DungeonShape> = {},
  prefix = "n",
): Layout {
  const full: DungeonShape = { ...DEFAULT_SHAPE, ...shape };
  const layout = new Layout();
  const counter = new Counter(prefix);

  const path = carveCriticalPath(layout, full, rng, counter);
  assignPathRoles(path, full, rng);
  carveBranches(layout, path, full, rng, counter);
  return layout;
}
