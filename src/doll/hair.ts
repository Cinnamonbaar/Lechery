/**
 * Hair as clumps, the way anime hair is drawn: a parting, a few locks of
 * varied width and length fanning from it, each a tapered curve ending in a
 * point. A style is its own set of locks with its own silhouette -- a bob
 * flares and turns in at the jaw, long hair falls past the shoulders -- so
 * hair is not a cap that follows the skull. (AnimeOutline, Skyrye: clumps,
 * not strands; varied sizes; volume off the skull; see docs/art.md.)
 *
 * Locks are given in hundredths of head height from the crown's centre,
 * as root, bend and tip, then width at the root. Neighbouring locks take
 * alternate part ids, so the shading draws the shadow line between clumps.
 * The fringe ends at the brow between the eyes; longer locks frame them.
 */
import { BROW_Y } from "./face";
import { HAIR_BACK, HAIR_BACK_LOCK, HAIR_FRONT, HAIR_LOCK, type HeadBox } from "./ids";
import type { Raster } from "./raster";

export const STYLE_COUNT = 5;

/** The fringe's lowest point between the eyes: the brow line. */
export const FRINGE_END = BROW_Y;

/** Body anchors the long styles fall to. */
export interface Fall { shoulderY: number; chestY: number }

type Lock = number[];

/** The same lock on the other side. */
const flip = (l: Lock): Lock => l.map((v, i) => (i < 6 && !(i & 1) ? -v : v));
const pair = (l: Lock) => [l, flip(l)];

/** Fringe from a parting just right of centre: framing locks at the
 * temples first, the big centre clump last, on top. */
const FRINGE: Lock[] = [
  [-8, 4, -32, 18, -35, 56, 15],
  [24, 6, 40, 24, 36, 58, 13],
  [2, 2, -16, 16, -22, 44, 14],
  [16, 4, 28, 18, 27, 36, 12],
  [-4, 4, -8, 18, -12, 32, 10],
  [10, 2, 14, 18, 12, 44, 13],
  [5, 0, 0, 22, -3, 46, 16],
];

/** Locks for a style: behind the body, and in front beside the face.
 * `c` is the chest, in the same hundredths of head height. */
function locks(style: number, c: number): [Lock[], Lock[]] {
  const short = pair([-25, 30, -48, 50, -42, 70, 22]), side = pair([-30, 22, -41, 42, -37, 62, 12]);
  return [
    [
      short,
      [...pair([-10, 10, -60, 45, -46, 92, 40]), ...pair([-20, 30, -50, 70, -30, 96, 30])],
      [...pair([-10, 10, -62, 60, -50, c + 20, 46]), ...pair([-20, 40, -55, c - 20, -34, c + 30, 36])],
      [...short, [26, 10, 84, 30, 50, c + 10, 34], [24, 12, 46, 6, 50, 26, 18]],
      [...short, ...pair([-30, 14, -84, 40, -54, c + 30, 32]), ...pair([-28, 14, -46, 6, -48, 26, 16])],
    ][style]!,
    [side, pair([-30, 24, -44, 55, -34, 88, 14]), pair([-30, 24, -44, 70, -42, c, 16]), side, side][style]!,
  ];
}

function draw(r: Raster, b: HeadBox, list: Lock[], ids: number[]) {
  const k = b.h / 100;
  list.forEach((l, n) => {
    const [x0, y0, x1, y1, x2, y2, w] = l.map((v) => v * k) as [number, number, number, number, number, number, number];
    const left: number[][] = [], right: number[][] = [];
    for (let i = 0; i <= 12; i++) {
      const t = i / 12, s = 1 - t;
      const x = s * s * x0 + 2 * s * t * x1 + t * t * x2, y = s * s * y0 + 2 * s * t * y1 + t * t * y2;
      const dx = s * (x1 - x0) + t * (x2 - x1), dy = s * (y1 - y0) + t * (y2 - y1), d = Math.hypot(dx, dy) || 1;
      // Full at the root, narrowing to a point: a clump, not a ribbon.
      const hw = (w / 2) * s ** 0.7;
      left.push([b.cx + x - (dy / d) * hw, b.top + y + (dx / d) * hw]);
      right.push([b.cx + x + (dy / d) * hw, b.top + y - (dx / d) * hw]);
    }
    r.poly([...left, ...right.reverse()], ids[n & 1]!);
  });
}

export function drawHairBack(r: Raster, b: HeadBox, style: number, fall: Fall) {
  // The mass behind the head stands off the skull: volume.
  r.ellipse(b.cx, b.top + b.h * 0.4, b.h * 0.45, b.h * 0.45, HAIR_BACK);
  draw(r, b, locks(style, ((fall.chestY - b.top) / b.h) * 100)[0], [HAIR_BACK, HAIR_BACK_LOCK]);
}

export function drawHairFront(r: Raster, b: HeadBox, style: number, fall: Fall) {
  // The crown, standing off the skull, down to where the fringe takes over.
  r.ellipse(b.cx, b.top + b.h * 0.38, b.h * 0.43, b.h * 0.44, HAIR_FRONT, (_, y) => y < b.top + b.h * 0.3);
  draw(r, b, [...locks(style, ((fall.chestY - b.top) / b.h) * 100)[1], ...FRINGE], [HAIR_LOCK, HAIR_FRONT]);
}
