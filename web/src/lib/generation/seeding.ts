/**
 * Deriving per-area seeds from one master seed.
 *
 * A single shared generator would couple every area to the order they were
 * generated in: add one room to the tutorial and the plains reshuffle.
 * Deriving an independent stream per area keeps each one stable no matter
 * what else changes, which matters as soon as areas start generating lazily
 * on first visit.
 */

import { Rng } from "./rng";

/**
 * A stable sub-seed for `key` under `masterSeed`.
 *
 * Hashed rather than added so that adjacent keys ("area1", "area2") give
 * unrelated streams instead of neighbouring ones.
 */
export function deriveSeed(masterSeed: number, key: string): number {
  const source = `${masterSeed}:${key}`;
  // FNV-1a, 32-bit. Cheap and well-mixed enough to decorrelate the streams.
  let hash = 0x811c9dc5;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

export function rngFor(masterSeed: number, key: string): Rng {
  return new Rng(deriveSeed(masterSeed, key));
}
