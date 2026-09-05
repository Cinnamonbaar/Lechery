/**
 * A seeded random number generator.
 *
 * JavaScript's Math.random cannot be seeded, and a game whose world is
 * generated needs the same seed to give the same map -- for reproducing a
 * bug, for sharing a run, and for tests that assert over many seeds.
 *
 * mulberry32: small, fast, and good enough for level layout. Not for
 * anything where randomness quality actually matters.
 */
export class Rng {
  private state: number;

  constructor(seed: number) {
    // Any 32-bit state works; zero is the one value that would stick.
    this.state = (seed >>> 0) || 0x9e3779b9;
  }

  /** A float in [0, 1). */
  next(): number {
    this.state = (this.state + 0x6d2b79f5) >>> 0;
    let t = this.state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }

  /** An integer in [low, high], inclusive at both ends like Python's randint. */
  int(low: number, high: number): number {
    if (high < low) return low;
    return low + Math.floor(this.next() * (high - low + 1));
  }

  /** An integer in [0, high), like Python's randrange. */
  below(high: number): number {
    return Math.floor(this.next() * high);
  }

  pick<T>(items: readonly T[]): T {
    if (items.length === 0) throw new Error("cannot pick from an empty list");
    return items[this.below(items.length)]!;
  }

  /** Weighted pick. Weights need not sum to anything in particular. */
  weighted<T>(items: readonly T[], weights: readonly number[]): T {
    const total = weights.reduce((sum, weight) => sum + Math.max(0, weight), 0);
    if (items.length === 0) throw new Error("cannot pick from an empty list");
    if (total <= 0) return this.pick(items);

    let roll = this.next() * total;
    for (let index = 0; index < items.length; index += 1) {
      roll -= Math.max(0, weights[index] ?? 0);
      if (roll <= 0) return items[index]!;
    }
    return items[items.length - 1]!;
  }

  /** Fisher-Yates, in place. */
  shuffle<T>(items: T[]): T[] {
    for (let i = items.length - 1; i > 0; i -= 1) {
      const j = this.below(i + 1);
      [items[i], items[j]] = [items[j]!, items[i]!];
    }
    return items;
  }
}
