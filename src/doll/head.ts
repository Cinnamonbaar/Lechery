/** The head: one measured outline, filling its box. */
import { smooth } from "./body";
import { HEAD as ID, type HeadBox } from "./ids";
import type { Raster } from "./raster";

/** Half-width of the head every 5% from crown to chin, in thousandths of
 * its height: the outline of the owner's anime references (all three
 * figures of the four-figure sheet, averaged). A wide cranium to 40%, then
 * one long taper through the cheek to a pointed chin. Below the temples the
 * sheet's face line steps in behind the ears; drawn without them that step
 * pinches the temples (an alien's head), so the cheek here runs on from the
 * cranium and the ears fill the rest. */
const OUTLINE = [0, 183, 253, 300, 332, 355, 368, 377, 378, 371, 358, 346, 332, 316, 296, 273, 250, 222, 180, 115, 20];

/** Width as a fraction of height, at the widest: 0.76 measured. */
export const HEAD_WIDTH = 0.756;

export const headBox = (cx: number, top: number, h: number): HeadBox => ({ cx, top, h, w: h * HEAD_WIDTH });

export function drawHead(r: Raster, b: HeadBox) {
  const side = smooth(OUTLINE.map((v, i) => [v * b.h / 1e3, b.top + b.h * i / 20]));
  // Ears, from 45% to 62% on the sheet, standing just off the cheek.
  for (const s of [-1, 1]) r.ellipse(b.cx + s * b.h * 0.355, b.top + b.h * 0.54, b.h * 0.045, b.h * 0.085, ID);
  r.poly([...side.map(([x, y]) => [b.cx + x!, y!]), ...side.reverse().map(([x, y]) => [b.cx - x!, y!])], ID);
}
