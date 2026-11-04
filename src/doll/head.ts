/** The head: a skull and a jaw, filling its box. */
import { HEAD as ID, type HeadBox } from "./ids";
import type { Raster } from "./raster";

/** Width as a fraction of height. Anime heads are rounder than real
 * ones (about 0.7); this keeps the softness the first doll had. */
export const HEAD_WIDTH = 0.87;
/** Where the jaw starts to narrow, from the crown. */
export const HEAD_JAW = 0.56;
/** Half-width of the chin, as a fraction of head width. */
export const HEAD_CHIN = 0.18;

export const headBox = (cx: number, top: number, h: number): HeadBox => ({ cx, top, h, w: h * HEAD_WIDTH });

export function drawHead(r: Raster, b: HeadBox) {
  const half = b.w / 2;
  r.ellipse(b.cx, b.top + b.h / 2, half, b.h * 0.48, ID);
  const jy = b.top + b.h * HEAD_JAW, chin = b.top + b.h;
  r.poly([[b.cx - half * 0.95, jy], [b.cx + half * 0.95, jy], [b.cx + b.w * HEAD_CHIN, chin], [b.cx - b.w * HEAD_CHIN, chin]], ID);
}
