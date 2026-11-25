/**
 * Part ids. Distinct ids for parts of one colour are what draw the lines
 * between them: an arm against a torso, one breast against the other.
 * Plain constants rather than an enum, so they survive per-file compiling.
 */
export const HAIR_BACK = 1, LEG_L = 2, LEG_R = 3, TORSO = 4, NECK = 5,
  BUST_L = 6, BUST_R = 7, ARM_L = 8, ARM_R = 9, BRIEFS = 10, BULGE = 11,
  BRA_L = 12, BRA_R = 13, HEAD = 14, HAIR_FRONT = 15,
  /** Every hair lock has its own id from these up, so the lines between
   * clumps can be found; for shading they all count as one mass. */
  FRONT_LOCKS = 20, BACK_LOCKS = 60;

/** The mass a part belongs to: all front hair is one, all back hair one. */
export const mass = (id: number) =>
  id === HAIR_FRONT || (id >= FRONT_LOCKS && id < BACK_LOCKS) ? HAIR_FRONT : id === HAIR_BACK || id >= BACK_LOCKS ? HAIR_BACK : id;

export interface Look {
  /** Centimetres. */
  height: number;
  /** 0 straight, 1 curvy. */
  build: number;
  /** 0 flat, rising. */
  bust: number;
  /** 0 none, rising. */
  endowment: number;
  skin: string;
  hair: string;
  eyes: string;
  style: number;
}

/** What changes between frames without the look changing. */
export interface Pose {
  blink: boolean;
  /** 0 or 1: the chest rises a pixel on the in-breath. */
  breath: number;
}

/**
 * The head's box, which the head, face and hair are all placed inside.
 * The face is positioned by face rules alone; hair is drawn around the
 * box and can never push the face.
 */
export interface HeadBox {
  cx: number;
  top: number;
  /** Height, crown to chin. */
  h: number;
  /** Width, cheek to cheek. */
  w: number;
}
