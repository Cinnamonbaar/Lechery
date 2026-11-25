/**
 * Hair as clumps, after Slynyrd's pixel anime hair (Pixelblog 29, the
 * "77 - Anime Hair" sheet, at nearly our head size): one flat mass of
 * colour with an outline, its clumps told apart by thin dark strand lines,
 * not by shading each clump. Locks flow from a cowlick or parting. Each
 * style is its own set of locks with its own fringe and silhouette -- spiky
 * tufts, a blunt cut, a centre parting, a side sweep -- so hair is not a
 * cap that follows the skull.
 *
 * Locks are in hundredths of head height from the crown's centre: root,
 * bend, tip, width at the root, and how much of that width the tip keeps
 * (0 a point, 1 a blunt cut). Every lock gets its own part id, so the
 * strand lines can be drawn where one clump meets another.
 */
import { BROW_Y } from "./face";
import { BACK_LOCKS, FRONT_LOCKS, HAIR_BACK, HAIR_FRONT, type HeadBox } from "./ids";
import type { Raster } from "./raster";

export const STYLE_COUNT = 5;

/** The fringe's lowest point between the eyes: the brow line. */
export const FRINGE_END = BROW_Y;

/** Body anchors the long styles fall to. */
export interface Fall { shoulderY: number; chestY: number }

type Lock = number[];

/** The same lock on the other side. */
const flip = (l: Lock): Lock => l.map((v, i) => (i < 6 && !(i & 1) ? -v : v));
const pair = (...ls: Lock[]) => ls.flatMap((l) => [l, flip(l)]);

interface Style {
  /** Where the crown mass ends and the face shows, from the crown. */
  line: number;
  back: Lock[];
  /** In front of the face, drawn in order: framing locks, then fringe. */
  front: Lock[];
}

/** `c` is the chest, in hundredths of head height. */
function style(n: number, c: number): Style {
  const nape = pair([-25, 30, -48, 50, -42, 70, 22]);
  return [
    // Short: tousled, swept from a parting on the right; pointed tufts at
    // varied lengths, forehead showing between, tufts flaring at the cheeks.
    { line: 0.3, back: nape, front: [
      ...pair([-30, 20, -44, 40, -48, 62, 14]),
      [16, 2, 22, 18, 18, 34, 10], [20, 0, 32, 20, 34, 48, 16],
      [-10, 4, -30, 14, -40, 38, 16], [0, 2, -14, 16, -24, 42, 18], [10, 0, 8, 22, -2, 45, 18],
    ] },
    // Bob: a blunt fringe cut straight at the brow, and sides that flare
    // past the head and turn in under the jaw.
    { line: 0.3, back: pair([-10, 10, -60, 45, -46, 92, 40], [-20, 30, -50, 70, -30, 96, 30]), front: [
      ...pair([-34, 22, -48, 58, -34, 90, 16, 0.2]),
      ...pair([-28, 8, -31, 24, -32, 36, 14, 0.7], [-14, 4, -16, 22, -16, 40, 15, 0.85]), [0, 2, 0, 22, 0, 41, 15, 0.85],
    ] },
    // Long: parted in the centre, no fringe -- the forehead shows and the
    // hair sweeps aside to frame the face, then falls past the shoulders.
    { line: 0.1, back: pair([-10, 10, -62, 60, -50, c + 20, 46], [-20, 40, -55, c - 20, -34, c + 30, 36]), front: [
      ...pair([-34, 30, -48, 80, -40, c, 18], [-3, 1, -24, 12, -38, 54, 22]),
    ] },
    // Ponytail: one big lock swept across from a side parting, the rest
    // pulled back into a tail behind the head.
    { line: 0.3, back: [...nape, [26, 10, 84, 30, 50, c + 10, 34], [24, 12, 46, 6, 50, 26, 18]], front: [
      [-32, 16, -40, 36, -38, 54, 12], [28, 4, 36, 20, 34, 44, 12], [24, 0, -6, 8, -34, 42, 30],
    ] },
    // Twintails: the classic split fringe -- a long centre point between
    // the eyes, shorter clumps either side, long locks framing the cheeks.
    { line: 0.3, back: [...nape, ...pair([-30, 14, -84, 40, -54, c + 30, 32], [-28, 14, -46, 6, -48, 26, 16])], front: [
      ...pair([-22, 8, -32, 26, -32, 54, 13], [-10, 4, -15, 20, -18, 36, 14]), [0, 4, 0, 24, 0, 44, 14],
    ] },
  ][n]!;
}

function draw(r: Raster, b: HeadBox, list: Lock[], id: number) {
  const k = b.h / 100;
  list.forEach((l) => {
    const [x0, y0, x1, y1, x2, y2, w] = l.map((v) => v * k) as [number, number, number, number, number, number, number];
    const blunt = l[7] ?? 0;
    const left: number[][] = [], right: number[][] = [];
    for (let i = 0; i <= 12; i++) {
      const t = i / 12, s = 1 - t;
      const x = s * s * x0 + 2 * s * t * x1 + t * t * x2, y = s * s * y0 + 2 * s * t * y1 + t * t * y2;
      const dx = s * (x1 - x0) + t * (x2 - x1), dy = s * (y1 - y0) + t * (y2 - y1), d = Math.hypot(dx, dy) || 1;
      const hw = (w / 2) * (blunt + (1 - blunt) * s ** 0.7);
      left.push([b.cx + x - (dy / d) * hw, b.top + y + (dx / d) * hw]);
      right.push([b.cx + x + (dy / d) * hw, b.top + y - (dx / d) * hw]);
    }
    r.poly([...left, ...right.reverse()], id++);
  });
}

const fallOf = (b: HeadBox, f: Fall) => ((f.chestY - b.top) / b.h) * 100;

export function drawHairBack(r: Raster, b: HeadBox, n: number, fall: Fall) {
  // The mass behind the head stands off the skull: volume.
  r.ellipse(b.cx, b.top + b.h * 0.4, b.h * 0.45, b.h * 0.45, HAIR_BACK);
  draw(r, b, style(n, fallOf(b, fall)).back, BACK_LOCKS);
}

export function drawHairFront(r: Raster, b: HeadBox, n: number, fall: Fall) {
  const s = style(n, fallOf(b, fall));
  // The crown, standing off the skull, down to the hairline.
  r.ellipse(b.cx, b.top + b.h * 0.38, b.h * 0.43, b.h * 0.44, HAIR_FRONT, (_, y) => y < b.top + b.h * s.line);
  draw(r, b, s.front, FRONT_LOCKS);
}
