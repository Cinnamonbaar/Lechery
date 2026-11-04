/**
 * The paperdoll, drawn from numbers.
 *
 * Every part is rasterised into a buffer of part ids, then shaded and
 * outlined automatically: a pixel whose neighbour below or to the right
 * belongs to a different part takes the shadow tone, one whose neighbour
 * above or to the left does takes the highlight, and empty pixels touching
 * the figure become its outline. That one rule is what makes a pile of
 * ellipses read as pixel art -- and it means a body part can be any size at
 * all, because nothing here is a fixed sprite.
 */

export const W = 64;
export const H = 120;

export interface Look {
  /** Centimetres. */
  height: number;
  /** 0 straight, 1 curvy. */
  build: number;
  /** 0 flat, rising. */
  bust: number;
  /** 0 none, rising. */
  endowment: number;
  skin: string;
  hair: string;
  eyes: string;
  style: number;
}

/** What changes between frames without the look changing. */
export interface Pose {
  blink: boolean;
  /** 0 or 1: the chest rises a pixel on the in-breath. */
  breath: number;
}

type Rgb = [number, number, number];
type Ramp = [outline: Rgb, dark: Rgb, base: Rgb, light: Rgb];

const hex = (h: string): Rgb => {
  const n = parseInt(h.slice(1), 16);
  return [n >> 16, (n >> 8) & 255, n & 255];
};

const mix = (a: Rgb, b: Rgb, t: number): Rgb =>
  [0, 1, 2].map((i) => Math.round(a[i]! + (b[i]! - a[i]!) * t)) as Rgb;

// Shadows lean purple and highlights warm, the way anime colouring does,
// rather than simply darkening and lightening.
const SHADOW = hex("#3b2752");
const GLOW = hex("#fff4e0");
const INK = hex("#1c1222");

export function ramp(base: string): Ramp {
  const b = hex(base);
  return [mix(b, INK, 0.7), mix(b, SHADOW, 0.38), b, mix(b, GLOW, 0.3)];
}

// Part ids. Distinct ids for parts of one colour are what draw the lines
// between them: an arm against a torso, one breast against the other.
const enum P {
  HairBack = 1, LegL, LegR, Torso, Neck, BustL, BustR, ArmL, ArmR,
  Briefs, Bulge, BraL, BraR, Head, HairFront,
}

const CLOTH = "#e9e4f2";

export function draw(look: Look, pose: Pose, out: Uint8ClampedArray): void {
  const ids = new Uint8Array(W * H);
  const put = (x: number, y: number, id: number) => {
    if (x >= 0 && x < W && y >= 0 && y < H) ids[y * W + x] = id;
  };
  const ellipse = (
    cx: number, cy: number, rx: number, ry: number, id: number,
    keep: (x: number, y: number) => boolean = () => true,
  ) => {
    for (let y = Math.floor(cy - ry); y <= cy + ry; y++)
      for (let x = Math.floor(cx - rx); x <= cx + rx; x++) {
        const dx = (x + 0.5 - cx) / rx, dy = (y + 0.5 - cy) / ry;
        if (dx * dx + dy * dy <= 1 && keep(x, y)) put(x, y, id);
      }
  };
  const poly = (pts: number[][], id: number) => {
    const ys = pts.map((p) => p[1]!), xs = pts.map((p) => p[0]!);
    for (let y = Math.floor(Math.min(...ys)); y <= Math.max(...ys); y++)
      for (let x = Math.floor(Math.min(...xs)); x <= Math.max(...xs); x++) {
        const px = x + 0.5, py = y + 0.5;
        let inside = false;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
          const [xi, yi] = pts[i]!, [xj, yj] = pts[j]!;
          if (yi! > py !== yj! > py && px < ((xj! - xi!) * (py - yi!)) / (yj! - yi!) + xi!)
            inside = !inside;
        }
        if (inside) put(x, y, id);
      }
  };
  // A shape and its mirror image about the centre line.
  const both = (pts: number[][], left: number, right: number) => {
    poly(pts.map(([x, y]) => [cx - x!, y!]), left);
    poly(pts.map(([x, y]) => [cx + x!, y!]), right);
  };

  const cx = W / 2;
  const ground = H - 3;
  const b = look.build;
  const fh = 80 + ((Math.min(Math.max(look.height, 145), 195) - 145) / 50) * 32;
  const top = ground - fh;
  const hh = 17;
  const headY = top + hh / 2;
  const chin = top + hh;
  const L = ground - chin;
  const shoulderY = chin + 3;
  const chestY = chin + L * 0.16;
  const waistY = chin + L * 0.34;
  const hipY = chin + L * 0.46;
  const crotchY = chin + L * 0.54;
  const kneeY = chin + L * 0.77;
  const sw = 8.4 - b * 1.6;
  const ww = 5.8 - b * 1.7;
  const hw = 6 + b * 3.8;

  // -- behind the body ---------------------------------------------------
  const style = look.style;
  if (style === 1) poly([[cx - 9, headY - 3], [cx + 9, headY - 3], [cx + 9.5, chin + 1], [cx - 9.5, chin + 1]], P.HairBack);
  if (style === 2) poly([[cx - 9, headY - 3], [cx + 9, headY - 3], [cx + 10.5, chestY + 9], [cx + 6, chestY + 11], [cx, chestY + 9], [cx - 6, chestY + 11], [cx - 10.5, chestY + 9]], P.HairBack);
  if (style === 3) ellipse(cx + 7, headY + 9, 3.4, 9, P.HairBack);
  if (style === 4) for (const s of [-1, 1]) poly([[cx + s * 7, headY - 6], [cx + s * 12, headY - 2], [cx + s * 12.5, chestY + 7], [cx + s * 10, chestY + 10], [cx + s * 8.5, headY + 2]], P.HairBack);
  ellipse(cx, headY - 0.5, 8.6, 8.8, P.HairBack);

  // -- body ----------------------------------------------------------------
  const thigh = hw * 0.62 + 0.6;
  both([[hw, hipY], [0.4, crotchY], [1.1, kneeY], [1.4, ground - 1], [3.7, ground - 1], [4.3, kneeY + 6], [3.9, kneeY], [thigh + 0.4, (hipY + kneeY) / 2]], P.LegL, P.LegR);
  ellipse(cx - 3, ground - 0.8, 2.6, 1.6, P.LegL);
  ellipse(cx + 3, ground - 0.8, 2.6, 1.6, P.LegR);

  const side = [[sw, shoulderY + 1], [sw - 0.8, chestY + 1], [ww, waistY], [hw, hipY], [hw - 0.6, crotchY - 1], [0.5, crotchY + 0.5]];
  poly([[cx, shoulderY - 1], ...side.map(([x, y]) => [cx + x!, y!]), ...side.reverse().map(([x, y]) => [cx - x!, y!])], P.Torso);

  poly([[cx - 2, chin - 2], [cx + 2, chin - 2], [cx + 2.2, shoulderY + 0.5], [cx - 2.2, shoulderY + 0.5]], P.Neck);

  const wrist = hw + 2.4;
  both([[sw + 0.6, shoulderY], [sw - 2.6, shoulderY + 2], [wrist - 2, crotchY], [wrist, crotchY], [sw + 1.2, shoulderY + 4]], P.ArmL, P.ArmR);
  ellipse(cx - wrist + 1, crotchY + 1.6, 1.6, 2, P.ArmL);
  ellipse(cx + wrist - 1, crotchY + 1.6, 1.6, 2, P.ArmR);

  const by = chestY + 1.5 + look.bust * 0.36 - pose.breath;
  const r = 1.4 + look.bust * 0.56;
  const bx = Math.min(1.1 + r * 0.86, sw - r * 0.45);
  if (look.bust > 0.3) {
    ellipse(cx - bx, by, r, r * 0.95, P.BustL);
    ellipse(cx + bx, by, r, r * 0.95, P.BustR);
    const cup = (s: number) => (x: number, y: number) => y + 0.5 > by - r * 0.15 && (s < 0 ? x < cx : x >= cx);
    ellipse(cx - bx, by, r + 0.35, r * 0.95 + 0.35, P.BraL, cup(-1));
    ellipse(cx + bx, by, r + 0.35, r * 0.95 + 0.35, P.BraR, cup(1));
  }

  poly([[cx - hw + 0.4, hipY + 0.5], [cx + hw - 0.4, hipY + 0.5], [cx + hw - 1.4, crotchY - 1], [cx + 1.4, crotchY + 2], [cx - 1.4, crotchY + 2], [cx - hw + 1.4, crotchY - 1]], P.Briefs);
  if (look.endowment > 0.3) ellipse(cx, crotchY - 0.2, 1.3 + look.endowment * 0.13, 1.5 + look.endowment * 0.2, P.Bulge);

  // -- head ----------------------------------------------------------------
  ellipse(cx, headY, 7.4, 8.2, P.Head);
  poly([[cx - 7, headY + 1], [cx + 7, headY + 1], [cx + 2.6, chin], [cx - 2.6, chin]], P.Head);

  const fringe = (x: number, y: number) => y < headY - 2 || (y < headY + 1 && Math.abs(((x - cx + 12) % 4) - 2) > 0.6 + (y - headY + 2) * 0.5);
  ellipse(cx, headY - 1.6, 8.4, 8, P.HairFront, fringe);
  const lock = style === 0 ? headY + 3 : style === 2 ? shoulderY + 4 : chin;
  poly([[cx - 8.6, headY - 3], [cx - 6.6, headY - 3], [cx - 7, lock], [cx - 8.4, lock - 1]], P.HairFront);
  poly([[cx + 8.6, headY - 3], [cx + 6.6, headY - 3], [cx + 7, lock], [cx + 8.4, lock - 1]], P.HairFront);

  // -- colour --------------------------------------------------------------
  const skin = ramp(look.skin), hair = ramp(look.hair), cloth = ramp(CLOTH);
  const material = (id: number): Ramp =>
    id === P.HairBack || id === P.HairFront ? hair
      : id >= P.Briefs && id <= P.BraR ? cloth : skin;

  const at = (x: number, y: number) => (x < 0 || x >= W || y < 0 || y >= H ? 0 : ids[y * W + x]!);
  const set = (i: number, c: Rgb) => {
    out[i * 4] = c[0]; out[i * 4 + 1] = c[1]; out[i * 4 + 2] = c[2]; out[i * 4 + 3] = 255;
  };
  out.fill(0);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const i = y * W + x, id = ids[i]!;
      if (id) {
        const m = material(id);
        set(i, at(x + 1, y) !== id || at(x, y + 1) !== id ? m[1] : at(x - 1, y) !== id || at(x, y - 1) !== id ? m[3] : m[2]);
      } else {
        const n = at(x + 1, y) || at(x - 1, y) || at(x, y + 1) || at(x, y - 1);
        if (n) set(i, material(n)[0]);
      }
    }

  // -- face, drawn straight in, unshaded -------------------------------------
  const px = (x: number, y: number, c: Rgb) => set(Math.round(y) * W + Math.round(x), c);
  const iris = ramp(look.eyes);
  const ey = Math.round(headY + 1);
  for (const s of [-1, 1]) {
    const outer = cx + s * 5 - (s > 0 ? 1 : 0);
    const inner = outer - s * 2;
    const cols = [outer, outer - s, inner];
    if (pose.blink) {
      for (const x of cols) px(x, ey + 1, skin[0]);
      continue;
    }
    for (const x of cols) px(x, ey - 1, INK);
    px(outer + s, ey - 1, INK);
    px(outer, ey, hex("#f4f0f6"));
    px(outer, ey + 1, hex("#f4f0f6"));
    px(outer - s, ey, iris[1]); px(inner, ey, iris[1]);
    px(outer - s, ey + 1, iris[2]); px(inner, ey + 1, iris[2]);
    px(outer - s, ey + 2, iris[3]); px(inner, ey + 2, iris[3]);
    px(outer - s, ey, hex("#ffffff"));
    px(outer, ey - 3, hair[1]); px(outer - s, ey - 3, hair[1]);
    px(outer - s * 0.4, ey + 4, mix(skin[2], hex("#ff7a8a"), 0.35));
  }
  px(cx - 0.5, chin - 3, mix(skin[1], hex("#b03050"), 0.4));
  px(cx + 0.5, chin - 3, mix(skin[1], hex("#b03050"), 0.4));
}
