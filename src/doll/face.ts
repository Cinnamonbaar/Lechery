/**
 * The face, placed in the head box by face-proportion rules and nothing
 * else -- hair is drawn around the box and cannot move it.
 *
 * The rules (Loomis's head; anime drawing guides):
 * - Facial thirds: hairline to brow, brow to the base of the nose, and nose
 *   to chin are equal. Anime keeps the brow and pulls the nose and mouth a
 *   little lower, toward a small chin.
 * - Eyes sit on or just below the head's midline; anime draws them lower
 *   and larger than real ones.
 * - Rule of fifths: a head is about five eye-widths across, with one eye-
 *   width between the eyes. Anime eyes are larger, so a little under five.
 * - The nose is a small shadow; the mouth sits just below it.
 */
import type { HeadBox, Look, Pose } from "./ids";
import { hex, INK, mix, ramp, type Raster, type Ramp, type Rgb } from "./raster";

/** Placement measured from Slynyrd's anime heads (Pixelblog 29, crown 0,
 * chin 1): eye 0.19 of head width; the gap a little under his 0.29W,
 * since our measured head is narrower than his and the lid flick needs room. */
/** Eye centre, from the crown, as a fraction of head height. */
export const EYE_Y = 0.525;
/** Eye width as a fraction of head width: 1/5 is real, anime larger. */
export const EYE_W = 0.19;
/** Space between the eyes, in eye widths. */
export const EYE_GAP = 1.4;
/** Eye height as a fraction of its width. */
export const EYE_TALL = 1.22;
/** Brow line: the second third. */
export const BROW_Y = 0.4;
export const NOSE_Y = 0.7;
export const MOUTH_Y = 0.825;
/** Mouth width as a fraction of head width. */
export const MOUTH_W = 0.1;

export function drawFace(r: Raster, b: HeadBox, look: Look, pose: Pose, skin: Ramp, hair: Ramp) {
  const inside = (x: number, y: number, ex: number, ey: number, rx: number, ry: number) =>
    ((x - ex) / rx) ** 2 + ((y - ey) / ry) ** 2 <= 1;

  const iris = ramp(look.eyes);
  const deep = mix(iris[1], INK, 0.35);
  const pupil = mix(iris[0], INK, 0.45);
  const white = hex("#f6f2f8"), shade = hex("#d6cfe0"), shine = hex("#ffffff");
  const lash = mix(INK, skin[1], 0.45);
  const brow = mix(hair[1], INK, 0.25);
  const blush = mix(skin[2], hex("#ff6f86"), 0.45);

  const cx = b.cx;
  const ew = b.w * EYE_W;
  const erx = ew / 2, ery = erx * EYE_TALL;
  const ey = b.top + b.h * EYE_Y;
  const browY = b.top + b.h * BROW_Y;

  for (const side of [-1, 1]) {
    // Centres one eye-width apart at the gap, so each sits gap/2 + 1/2 out.
    const ex = cx + side * ew * (EYE_GAP / 2 + 0.5);
    // Brow: a thin arc on the brow line, dipping toward the outer end.
    r.paint(ex - ew * 0.75, browY - 1, ex + ew * 0.75, browY + 1.2, (x, y) => {
      const u = (x - ex) / (ew * 0.68);
      const arc = browY - (1 - u * u) * 0.5 + Math.max(0, u * side) * 0.6;
      return Math.abs(u) < 1 && Math.abs(y - arc) < 0.22 ? brow : null;
    });
    if (pose.blink) {
      r.paint(ex - ew, ey - 1, ex + ew, ey + 2, (x, y) => {
        const u = (x - ex) / (erx * 1.1);
        return Math.abs(u) < 1 && Math.abs(y - (ey + 0.5 + u * u * 0.5)) < 0.28 ? INK : null;
      });
      continue;
    }
    r.paint(ex - ew * 0.8, ey - ery - 1, ex + ew * 0.8, ey + ery + 0.8, (x, y): Rgb | null => {
      const open = inside(x, y, ex, ey, erx, ery);
      // The upper lid: a thick band hugging the top of the opening, with a
      // flick out past the outer corner.
      const lid = inside(x, y, ex, ey - 0.15, erx + 0.35, ery + 0.25) && y < ey - ery * 0.45;
      const flick = (x - ex) * side > erx * 0.6 && (x - ex) * side < erx + 0.9 &&
        Math.abs(y - (ey - ery * 0.55 - ((x - ex) * side - erx * 0.6) * 0.35)) < 0.3;
      if (lid || flick) return INK;
      if (!open) {
        // Lower lash, under the outer half only.
        const below = inside(x, y, ex, ey, erx, ery + 0.3) && y > ey + ery * 0.5;
        return below && (x - ex) * side > -0.2 ? lash : null;
      }
      // Highlights toward the light, top left, whichever eye this is.
      if (inside(x, y, ex - ew * 0.18, ey - ery * 0.24, ew * 0.135, ew * 0.135)) return shine;
      if (inside(x, y, ex + ew * 0.18, ey + ery * 0.45, ew * 0.07, ew * 0.07)) return shine;
      const iy = ey + 0.15;
      if (inside(x, y, ex, iy, ew * 0.37, ery * 0.86)) {
        if (inside(x, y, ex, iy + 0.1, ew * 0.145, ery * 0.42)) return pupil;
        const v = (y - (iy - ery)) / (ery * 2);
        return v < 0.35 ? deep : v < 0.72 ? iris[2] : iris[3];
      }
      return y < ey - ery * 0.2 ? shade : white;
    });
    // Blush: three short diagonal strokes on the cheek, under the eye.
    const by = ey + ery + 0.7;
    r.paint(ex - ew * 0.65, by - 0.7, ex + ew * 0.65, by + 0.7, (x, y) => {
      const d = (x - ex + ew * 0.65 - (by + 0.7 - y)) / (ew * 0.37);
      return Math.abs(d - Math.round(d)) < 0.12 && Math.round(d) >= 1 && Math.round(d) <= 3 ? blush : null;
    });
  }

  // Nose: a small shadow on the far side from the light. Mouth: a short,
  // soft line, darker at its centre.
  const ny = b.top + b.h * NOSE_Y;
  r.paint(cx + 0.1, ny - 0.17, cx + 0.45, ny + 0.17, () => skin[1]);
  const my = b.top + b.h * MOUTH_Y, mw = (b.w * MOUTH_W) / 2;
  const lip = mix(skin[1], hex("#b03050"), 0.45), corner = mix(skin[1], hex("#b03050"), 0.2);
  r.paint(cx - mw, my - 0.14, cx + mw, my + 0.14, (x) => (Math.abs(x - cx) < mw * 0.47 ? lip : corner));
}
