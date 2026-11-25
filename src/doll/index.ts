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
import { BRA_R, BRIEFS, FRONT_LOCKS, HAIR_BACK, HAIR_FRONT, mass, type Look, type Pose } from "./ids";
import { BH, BW, hex, INK, mix, R, ramp, raster, type Ramp } from "./raster";

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
  const front = (id: number) => mass(id) === HAIR_FRONT;
  r.shade((id) => (mass(id) === HAIR_BACK ? back : front(id) ? hair : id >= BRIEFS && id <= BRA_R ? cloth : skin), mass,
    // Hair takes a thin shadow edge: a thick one where it meets the face
    // reads as a helmet's rim (Slynyrd's hair has none).
    (id) => (id === HAIR_FRONT ? R / 2 : R),
    // catches light only on its outer edge, and lies over the face.
    (id) => id === HAIR_FRONT);

  const { cx, top, h } = a.head, shine = mix(hair[3], hex("#ffffff"), 0.35);
  // Strand lines: a thin dark line wherever one lock lies on another, which
  // is what tells the clumps apart (the crown mass draws none).
  const lock = (id: number) => id >= FRONT_LOCKS;
  r.paint(0, top - h * 0.2, BW, BH, (x, y) => {
    const id = r.id(x, y), e = 1 / R;
    // Not up in the crown, where every lock starts and lines would scribble.
    if (!lock(id) || y < top + h * 0.14) return null;
    const n = [r.id(x + e, y), r.id(x, y + e)].find((m) => lock(m) && m !== id && mass(m) === mass(id));
    return n ? (mass(id) === HAIR_BACK ? back : hair)[0] : null;
  });
  r.paint(cx - h, top - h * 0.2, cx + h, top + h * 0.6, (x, y) => {
    // The angel ring: a broken band of shine that curves with the skull,
    // across the clumps rather than along them.
    const dx = (x - cx) / (h * 0.42), dy = (y - top - h * 0.42) / (h * 0.46), d = Math.hypot(dx, dy);
    return front(r.id(x, y)) && d > 0.72 && d < 0.79 && dy < -0.35 && Math.sin(Math.atan2(dy, dx) * 7) > -0.6 ? shine : null;
  });
  if (layers & FACE) drawFace(r, a.head, look, pose, skin, hair);
}
