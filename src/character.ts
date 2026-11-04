/** Who the player is making, and how it maps onto the doll. */
import { EYES, HAIR, ORIGINS, SKIN, STYLES } from "./content";
import type { Look } from "./doll";

export interface Character {
  name: string;
  pronouns: number;
  origin: number;
  height: number;
  build: number;
  bust: number;
  endowment: number;
  skin: number;
  hair: number;
  eyes: number;
  style: number;
}

export const fresh = (): Character => ({
  name: "", pronouns: 0, origin: 0, height: 166, build: 0.6, bust: 4, endowment: 0,
  skin: 1, hair: 0, eyes: 3, style: 2,
});

export const look = (c: Character): Look => ({
  height: c.height, build: c.build, bust: c.bust, endowment: c.endowment,
  skin: SKIN[c.skin]![1], hair: HAIR[c.hair]![1], eyes: EYES[c.eyes]![1], style: c.style,
});

const pick = (n: number) => Math.floor(Math.random() * n);

/** A whole random person, keeping the name: a name is chosen, not rolled. */
export const roll = (c: Character): Character => ({
  ...c,
  origin: pick(ORIGINS.length), height: 148 + pick(44), build: Math.random(),
  bust: pick(2) ? pick(11) : 0, endowment: pick(3) ? 0 : pick(11),
  skin: pick(SKIN.length), hair: pick(HAIR.length), eyes: pick(EYES.length),
  style: pick(STYLES.length),
});

// The draft survives a reload: people spend a long time in creation
// screens, and losing that to a closed tab is the worst first impression.
const KEY = "lechery:draft";

export function load(): Character {
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) ?? "null");
    if (saved && typeof saved === "object") return { ...fresh(), ...saved };
  } catch {}
  return fresh();
}

export function save(c: Character) {
  try { localStorage.setItem(KEY, JSON.stringify(c)); } catch {}
}
