/**
 * The paperdoll, assembled from parts that are each built in their own
 * box: the body from its measurements, the head in a box above it, the face
 * inside that box by face rules alone, and the hair around it. Parts can be
 * drawn on their own -- see tools/parts.ts -- to tune one without the
 * others getting in the way.
 */
import { drawBody, landmarks, MIX } from "./body";
import { drawFace } from "./face";
import { drawHairBack, drawHairFront } from "./hair";
import { drawHead, headBox } from "./head";
import { BRA_R, BRIEFS, HAIR_BACK, HAIR_FRONT, type Look, type Pose } from "./ids";
import { BH, BW, ramp, raster } from "./raster";

export { H, R, W, ramp } from "./raster";
export { MIX, measure } from "./body";
export { STYLE_COUNT } from "./hair";
export type { Look, Pose } from "./ids";

/** Layers as bit flags: numbers minify, names would ship in full. */
export const HAIR_BACK_LAYER = 1, BODY = 2, HEAD_LAYER = 4, FACE = 8, HAIR_FRONT_LAYER = 16, ALL = 31;

const CLOTH = "#e9e4f2";

/** Where the parts go, for drawing and for tools that put guides on them. */
export function layout(look: Look, blend?: number) {
  const a = landmarks(look, blend ?? MIX, BW / 2, BH - 3);
  return { ...a, head: headBox(a.cx, a.top, a.m.u) };
}

export function draw(look: Look, pose: Pose, out: Uint8ClampedArray, blend?: number, layers = ALL): void {
  const r = raster(out);
  const a = layout(look, blend);
  if (layers & HAIR_BACK_LAYER) drawHairBack(r, a.head, look.style, a);
  if (layers & BODY) drawBody(r, a, look, pose);
  if (layers & HEAD_LAYER) drawHead(r, a.head);
  if (layers & HAIR_FRONT_LAYER) drawHairFront(r, a.head, look.style, a);

  const skin = ramp(look.skin), hair = ramp(look.hair), cloth = ramp(CLOTH);
  r.shade((id) => (id === HAIR_BACK || id === HAIR_FRONT ? hair : id >= BRIEFS && id <= BRA_R ? cloth : skin));
  if (layers & FACE) drawFace(r, a.head, look, pose, skin, hair);
}
