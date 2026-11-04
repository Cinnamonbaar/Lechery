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
export const H = 132;

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
  const t = (Math.min(Math.max(look.height, 145), 195) - 145) / 50;

  // -- proportions ---------------------------------------------------------
  // Landmarks from the classical canons (Loomis and Richer, via Proko's
  // notes), restated as fractions of total height so they hold at any size.
  // In the 8-head figure: nipples at 2 heads, navel at 3, crotch at 4 --
  // half the height -- and knees near 6. Anime enlarges the head to 7-7.5
  // heads for an adult; below about 6 a figure starts to read as a child,
  // which an adult character must never do. Shorter people get a slightly
  // larger head for their height, as real ones do, but never leave the
  // adult range.
  const fh = 104 + t * 21;
  const heads = 6.9 + t * 0.6;
  const u = fh / heads;
  const k = u / 17; // scale for features drawn in head-sized pixels
  const top = ground - fh;
  const y = (fraction: number) => top + fh * fraction;
  const headY = top + u / 2;
  const chin = top + u;
  const shoulderY = y(0.175);
  const chestY = y(0.26);
  const waistY = y(0.37);
  const hipY = y(0.455);
  const crotchY = y(0.49); // a touch above half: anime legs run long
  const kneeY = y(0.73);
  // Widths as fractions of height too, measured across the deltoids: about
  // 0.24 of height for a man and 0.21 for a woman (Loomis's 0.29 is his
  // heroic ideal, and on an anime head it makes a linebacker). Hips run
  // about 0.17 for a straight build and match the shoulders on a curvy one,
  // which is what makes an hourglass rather than a wedge.
  const sw = fh * (0.122 - b * 0.017);
  const ww = fh * (0.08 - b * 0.02);
  const hw = fh * (0.085 + b * 0.025);
  const neck = fh * 0.028;
  const armW = fh * 0.034; // upper arm, full width
  const foreW = fh * 0.028;

  // -- behind the body ---------------------------------------------------
  const style = look.style;
  const hx = 9 * k;
  if (style === 1) poly([[cx - hx, headY - 3], [cx + hx, headY - 3], [cx + hx + 0.5, chin + 1], [cx - hx - 0.5, chin + 1]], P.HairBack);
  if (style === 2) poly([[cx - hx, headY - 3], [cx + hx, headY - 3], [cx + hx + 1.5, chestY + 9], [cx + 6, chestY + 11], [cx, chestY + 9], [cx - 6, chestY + 11], [cx - hx - 1.5, chestY + 9]], P.HairBack);
  if (style === 3) ellipse(cx + 7 * k, headY + 9, 3.4, 9, P.HairBack);
  if (style === 4) for (const s of [-1, 1]) poly([[cx + s * 7 * k, headY - 6], [cx + s * 12 * k, headY - 2], [cx + s * 12.5 * k, chestY + 7], [cx + s * 10 * k, chestY + 10], [cx + s * 8.5 * k, headY + 2]], P.HairBack);
  ellipse(cx, headY - 0.5, 8.6 * k, 8.8 * k, P.HairBack);

  // -- body ----------------------------------------------------------------
  // Legs: the thigh fills the hip, tapering to a knee, a calf with some
  // shape below it, and a slim ankle.
  const knee = fh * 0.032, calf = fh * 0.036, ankle = fh * 0.02;
  const legX = hw * 0.5; // centre line of each leg at the knee
  both([[hw, hipY], [0.4, crotchY], [legX - knee + 0.5, kneeY], [legX - ankle * 0.6, ground - 1], [legX + ankle * 1.4, ground - 1], [legX + calf, kneeY + (ground - kneeY) * 0.3], [legX + knee, kneeY], [hw * 0.92, (hipY + kneeY) / 2]], P.LegL, P.LegR);
  ellipse(cx - legX, ground - 0.8, ankle + 1.6, 1.6, P.LegL);
  ellipse(cx + legX, ground - 0.8, ankle + 1.6, 1.6, P.LegR);

  // The trapezius slopes from the neck to the shoulder rather than running
  // flat: a level line there is what reads as a coat hanger.
  const side = [[neck + (sw - neck) * 0.45, shoulderY - 0.6], [sw - armW * 0.5, shoulderY + 1.6], [sw - armW * 0.9, chestY + 1], [ww, waistY], [hw, hipY], [hw - 0.6, crotchY - 1], [0.5, crotchY + 0.5]];
  poly([[cx - neck, shoulderY - 2.4], [cx + neck, shoulderY - 2.4], ...side.map(([x, y]) => [cx + x!, y!]), ...side.reverse().map(([x, y]) => [cx - x!, y!])], P.Torso);

  poly([[cx - neck, chin - 2], [cx + neck, chin - 2], [cx + neck + 0.3, shoulderY + 0.5], [cx - neck - 0.3, shoulderY + 0.5]], P.Neck);

  // Arms: elbow at the waist, wrist at the crotch, fingertips at mid-thigh.
  // The arm hangs from the shoulder joint and angles out only as far as it
  // must to clear the waist and then the hip -- the "carrying angle" real
  // arms have, and why a curvy figure's hands sit further out.
  const shoulderX = sw - armW * 0.5;
  const elbowX = Math.max(shoulderX, ww + armW * 0.5 + 0.4);
  const wristX = Math.max(elbowX, hw + foreW * 0.5 + 0.4);
  const limb = (x0: number, y0: number, w0: number, x1: number, y1: number, w1: number) => {
    both([[x0 - w0 / 2, y0], [x0 + w0 / 2, y0], [x1 + w1 / 2, y1], [x1 - w1 / 2, y1]], P.ArmL, P.ArmR);
  };
  limb(shoulderX, shoulderY + armW * 0.6, armW, elbowX, waistY, armW * 0.85);
  limb(elbowX, waistY, armW * 0.85, wristX, crotchY, foreW * 0.75);
  // A round deltoid caps the shoulder.
  ellipse(cx - shoulderX, shoulderY + armW * 0.85, armW * 0.6, armW * 0.7, P.ArmL);
  ellipse(cx + shoulderX, shoulderY + armW * 0.85, armW * 0.6, armW * 0.7, P.ArmR);
  const hand = fh * 0.045;
  ellipse(cx - wristX, crotchY + hand * 0.9, foreW * 0.55, hand, P.ArmL);
  ellipse(cx + wristX, crotchY + hand * 0.9, foreW * 0.55, hand, P.ArmR);

  // The bust sits on the nipple line and scales with the frame, so a cup
  // size reads the same on a short character as on a tall one.
  const f = fh / 110;
  const r = (1.4 + look.bust * 0.56) * f;
  const by = chestY - 0.5 + look.bust * 0.36 * f - pose.breath;
  const bx = Math.min(1.1 + r * 0.86, sw - r * 0.45);
  if (look.bust > 0.3) {
    ellipse(cx - bx, by, r, r * 0.95, P.BustL);
    ellipse(cx + bx, by, r, r * 0.95, P.BustR);
    const cup = (s: number) => (x: number, y: number) => y + 0.5 > by - r * 0.15 && (s < 0 ? x < cx : x >= cx);
    ellipse(cx - bx, by, r + 0.35, r * 0.95 + 0.35, P.BraL, cup(-1));
    ellipse(cx + bx, by, r + 0.35, r * 0.95 + 0.35, P.BraR, cup(1));
  }

  poly([[cx - hw + 0.4, hipY + 0.5], [cx + hw - 0.4, hipY + 0.5], [cx + hw - 1.4, crotchY - 1], [cx + 1.6, crotchY + 2], [cx - 1.6, crotchY + 2], [cx - hw + 1.4, crotchY - 1]], P.Briefs);
  if (look.endowment > 0.3) ellipse(cx, crotchY - 0.2, (1.3 + look.endowment * 0.13) * f, (1.5 + look.endowment * 0.2) * f, P.Bulge);

  // -- head ----------------------------------------------------------------
  ellipse(cx, headY, 7.4 * k, 8.2 * k, P.Head);
  poly([[cx - 7 * k, headY + 1], [cx + 7 * k, headY + 1], [cx + 2.6 * k, chin], [cx - 2.6 * k, chin]], P.Head);

  const fringe = (x: number, y: number) => y < headY - 2 || (y < headY + 1 && Math.abs(((x - cx + 12) % 4) - 2) > 0.6 + (y - headY + 2) * 0.5);
  ellipse(cx, headY - 1.6, 8.4 * k, 8 * k, P.HairFront, fringe);
  const lock = style === 0 ? headY + 3 : style === 2 ? shoulderY + 4 : chin;
  const lo = 8.6 * k, li = 6.6 * k;
  poly([[cx - lo, headY - 3], [cx - li, headY - 3], [cx - li - 0.4, lock], [cx - lo + 0.2, lock - 1]], P.HairFront);
  poly([[cx + lo, headY - 3], [cx + li, headY - 3], [cx + li + 0.4, lock], [cx + lo - 0.2, lock - 1]], P.HairFront);

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
        // Selective outline: the light comes from the top left, so where the
        // figure lies below or to the right of this pixel the edge is lit
        // and takes the part's own shadow tone; on the far sides it takes
        // the darkest. A flat black line all round is what makes pixel art
        // look like a sticker.
        const lit = at(x + 1, y) || at(x, y + 1);
        const n = lit || at(x - 1, y) || at(x, y - 1);
        if (n) set(i, material(n)[lit ? 1 : 0]);
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
