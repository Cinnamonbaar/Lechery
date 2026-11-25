/**
 * The paperdoll, assembled from parts that are each built in their own
 * box: the body from its measurements, the head in a box above it, the face
 * inside that box by face rules alone, and the hair around it. Parts can be
 * drawn on their own -- see tools/parts.ts -- to tune one without the
 * others getting in the way.
 */
import { drawBody, landmarks } from "./body";
import { drawFace } from "./face";
import { drawHairBack, drawHairFront } from "./hair";
import { drawHead, headBox } from "./head";
import { BRA_R, BRIEFS, HAIR_BACK, HAIR_BACK_LOCK, HAIR_FRONT, HAIR_LOCK, HEAD, type Look, type Pose } from "./ids";
import { BH, BW, hex, INK, mix, ramp, raster, type Ramp } from "./raster";

export { H, R, W, ramp } from "./raster";
export { STYLE_COUNT } from "./hair";
export type { Look, Pose } from "./ids";

/** Layers as bit flags: numbers minify, names would ship in full. */
export const HAIR_BACK_LAYER = 1, BODY = 2, HEAD_LAYER = 4, FACE = 8, HAIR_FRONT_LAYER = 16, ALL = 31;

const CLOTH = "#e9e4f2";

/** Where the parts go, for drawing and for tools that put guides on them. */
export function layout(look: Look) {
  const a = landmarks(look, BW / 2, BH - 3);
  return { ...a, head: headBox(a.cx, a.top, a.u) };
}

export function draw(look: Look, pose: Pose, out: Uint8ClampedArray, layers = ALL): void {
  const r = raster(out);
  const a = layout(look);
  if (layers & HAIR_BACK_LAYER) drawHairBack(r, a.head, look.style, a);
  if (layers & BODY) drawBody(r, a, look, pose);
  if (layers & HEAD_LAYER) drawHead(r, a.head);
  if (layers & HAIR_FRONT_LAYER) drawHairFront(r, a.head, look.style, a);

  const skin = ramp(look.skin), hair = ramp(look.hair), cloth = ramp(CLOTH);
  // Hair behind the head sits in its shadow: one tone darker throughout.
  const back: Ramp = [hair[0], mix(hair[1], INK, 0.25), hair[1], hair[2]];
  const front = (id: number) => id === HAIR_FRONT || id === HAIR_LOCK;
  r.shade((id) => (id === HAIR_BACK || id === HAIR_BACK_LOCK ? back : front(id) ? hair : id >= BRIEFS && id <= BRA_R ? cloth : skin));

  const { cx, top, h } = a.head, shine = mix(hair[3], hex("#ffffff"), 0.35);
  r.paint(cx - h, top - h * 0.2, cx + h, top + h, (x, y) => {
    // The fringe's shadow on the face, cast down and right from the light.
    if (r.id(x, y) === HEAD && front(r.id(x - 0.3, y - 1.1))) return skin[1];
    // The angel ring: a broken band of shine that curves with the skull,
    // across the clumps rather than along them.
    const dx = (x - cx) / (h * 0.42), dy = (y - top - h * 0.42) / (h * 0.46), d = Math.hypot(dx, dy);
    return front(r.id(x, y)) && d > 0.72 && d < 0.79 && dy < -0.35 && Math.sin(Math.atan2(dy, dx) * 7) > -0.6 ? shine : null;
  });
  if (layers & FACE) drawFace(r, a.head, look, pose, skin, hair);
}
