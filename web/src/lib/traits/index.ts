/**
 * Traits: who a character is, and what body they are currently in.
 *
 * Identity and body are separate on purpose -- see `identity`. Every physical
 * trait carries a number for transformations to work on and a word for prose
 * and the paperdoll to read, and every change comes back as an event so it can
 * narrate itself.
 */

export * from "./scale";
export * from "./palette";
export * from "./identity";
export * from "./perception";
export * from "./traits";
export * from "./character";
