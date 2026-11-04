/**
 * Hair, drawn around the head box -- never inside the face's rules. It can
 * grow, shrink or change style without moving an eye.
 *
 * Bangs end at the brow line at the lowest, so they frame the eyes rather
 * than cover them; side locks hang just outside the cheeks.
 */
import { HAIR_BACK, HAIR_FRONT, type HeadBox } from "./ids";
import { BROW_Y } from "./face";
import type { Raster } from "./raster";

export const STYLE_COUNT = 5;

/** How far hair stands off the skull, as a multiple of its size. */
export const HAIR_VOLUME = 1.14;
/** Where the fringe's shortest strands end, from the crown. */
export const FRINGE_TOP = 0.3;
/** Where its longest end: the brow line, so the eyes stay clear. */
export const FRINGE_END = BROW_Y;
/** Width of one strand, as a fraction of head width. */
export const HAIR_STRAND = 0.176;
/** Side locks: inner and outer edge, as fractions of head half-width. */
export const LOCK_IN = 0.94;
export const LOCK_OUT = 1.16;

/** Strand lengths, 0 shortest to 1 longest, in a fixed pattern so the fringe
 * looks cut rather than stamped -- but the same every time it is drawn. */
const LENGTHS = [0.25, 0.85, 0.1, 0.7, 1, 0.3, 0.75, 0];

/** Body anchors the long styles fall to. */
export interface Fall { shoulderY: number; chestY: number }

export function drawHairBack(r: Raster, b: HeadBox, style: number, fall: Fall) {
  const { cx, top, h, w } = b;
  const k = h / 17, mid = top + h / 2, chin = top + h;
  const hx = w * 0.61;
  if (style === 1) r.poly([[cx - hx, mid - 3 * k], [cx + hx, mid - 3 * k], [cx + hx + 0.5, chin + 1], [cx - hx - 0.5, chin + 1]], HAIR_BACK);
  if (style === 2) r.poly([[cx - hx, mid - 3 * k], [cx + hx, mid - 3 * k], [cx + hx + 1.5, fall.chestY + 9], [cx + 6, fall.chestY + 11], [cx, fall.chestY + 9], [cx - 6, fall.chestY + 11], [cx - hx - 1.5, fall.chestY + 9]], HAIR_BACK);
  if (style === 3) r.ellipse(cx + w * 0.47, mid + 9 * k, 3.4 * k, 9 * k, HAIR_BACK);
  if (style === 4) for (const s of [-1, 1]) r.poly([[cx + s * w * 0.47, mid - 6 * k], [cx + s * w * 0.81, mid - 2 * k], [cx + s * w * 0.85, fall.chestY + 7], [cx + s * w * 0.68, fall.chestY + 10], [cx + s * w * 0.57, mid + 2 * k]], HAIR_BACK);
  r.ellipse(cx, mid - 0.5 * k, (w / 2) * HAIR_VOLUME * 1.02, (h / 2) * HAIR_VOLUME * 0.91, HAIR_BACK);
}

export function drawHairFront(r: Raster, b: HeadBox, style: number, fall: Fall) {
  const { cx, top, h, w } = b;
  const mid = top + h / 2, half = w / 2;
  const strand = w * HAIR_STRAND, depth = h * 0.18;
  const fringe = (x: number, y: number) => {
    const along = (x + 0.5 - cx) / strand + 0.5;
    const phase = ((along % 1) + 1) % 1;
    const n = LENGTHS[((Math.floor(along) % 8) + 8) % 8]!;
    const tip = top + h * (FRINGE_TOP + (FRINGE_END - FRINGE_TOP) * n);
    return y + 0.5 < tip - Math.abs(phase - 0.5) * 2 * depth;
  };
  r.ellipse(cx, mid - h * 0.094, half * HAIR_VOLUME, (h / 2) * HAIR_VOLUME * 0.83, HAIR_FRONT, fringe);
  const lock = style === 0 ? mid + h * 0.18 : style === 2 ? fall.shoulderY + 4 : top + h;
  const lo = half * LOCK_OUT, li = half * LOCK_IN, y0 = mid - h * 0.18;
  r.poly([[cx - lo, y0], [cx - li, y0], [cx - li - 0.4, lock], [cx - lo + 0.2, lock - 1]], HAIR_FRONT);
  r.poly([[cx + lo, y0], [cx + li, y0], [cx + li + 0.4, lock], [cx + lo - 0.2, lock - 1]], HAIR_FRONT);
}
