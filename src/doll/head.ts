/** The head: one measured outline, filling its box. */
import { smooth } from "./body";
import { HEAD as ID, type HeadBox } from "./ids";
import type { Raster } from "./raster";

/** Half-width of the head every 5% from crown to chin, in thousandths of
 * its height: the outline of the owner's anime references (all three
 * figures of the four-figure sheet, averaged; ears left out). A wide
 * cranium to 40%, then one long taper through the cheek to a pointed chin
 * -- an egg, not a circle on a block. */
const OUTLINE = [0, 183, 253, 300, 332, 355, 368, 377, 378, 362, 337, 329, 316, 305, 288, 269, 251, 224, 178, 110, 20];

/** Width as a fraction of height, at the widest: 0.76 measured. */
export const HEAD_WIDTH = 0.756;

export const headBox = (cx: number, top: number, h: number): HeadBox => ({ cx, top, h, w: h * HEAD_WIDTH });

export function drawHead(r: Raster, b: HeadBox) {
  const side = smooth(OUTLINE.map((v, i) => [v * b.h / 1e3, b.top + b.h * i / 20]));
  r.poly([...side.map(([x, y]) => [b.cx + x!, y!]), ...side.reverse().map(([x, y]) => [b.cx - x!, y!])], ID);
}
