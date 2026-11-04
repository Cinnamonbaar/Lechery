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

/**
 * The art is laid out in base units on a 64x132 frame, and drawn R times
 * finer. Proportions live in base units, so changing R sharpens the doll
 * without moving a single landmark -- the face included, which is built
 * from shapes like the body rather than placed pixel by pixel.
 */
export const R = 4;
const BW = 64, BH = 132;
export const W = BW * R;
const OUTLINE = Math.max(1, R / 2);
const SHADE = R, LIGHT = Math.max(1, R / 2);
export const H = BH * R;

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

/** 0 is the first, stylised doll; 1 the anatomical canon. See measure(). */
export const MIX = 0.5;

/**
 * Two complete sets of measurements, and a blend between them.
 *
 * STYLISED is the first doll: a fixed 17-pixel head and a short frame, so
 * 4.7-6.6 heads tall, with a long torso, short legs and narrow shoulders.
 *
 * CANON is measured from the classical figure canons (Loomis and Richer,
 * via Proko's notes), restated as fractions of height so it holds at any
 * size: 6.9-7.5 heads, nipples, waist and hips at their landmarks, crotch
 * at a touch above half, shoulders and hips at measured widths.
 *
 * MIX chooses between them -- 0 is the first, 1 the canon -- so the look is
 * tuned by eye with one number instead of by guessing a dozen.
 */
export function measure(look: Pick<Look, "height" | "build">, blend = MIX) {
  const t = (Math.min(Math.max(look.height, 145), 195) - 145) / 50;
  const b = look.build;
  const stylised = {
    fh: 80 + t * 32, u: 17,
    shoulder: 20, chest: 0.16, waist: 0.34, hip: 0.46, crotch: 0.54, knee: 0.77,
    sw: 8.4 - b * 1.6, ww: 5.8 - b * 1.7, hw: 6 + b * 3.8,
    neck: 2, armW: 3.2, foreW: 2, kneeW: 1.4, calf: 1.6, ankle: 1.15, hand: 2,
  };
  const cfh = 104 + t * 21, cu = cfh / (6.9 + t * 0.6);
  const canon = {
    fh: cfh, u: cu,
    shoulder: cfh * 0.175,
    // As fractions of the body below the chin, to blend with the first set.
    chest: (cfh * 0.26 - cu) / (cfh - cu), waist: (cfh * 0.37 - cu) / (cfh - cu),
    hip: (cfh * 0.455 - cu) / (cfh - cu), crotch: (cfh * 0.49 - cu) / (cfh - cu),
    knee: (cfh * 0.73 - cu) / (cfh - cu),
    sw: cfh * (0.122 - b * 0.017), ww: cfh * (0.08 - b * 0.02), hw: cfh * (0.085 + b * 0.025),
    neck: cfh * 0.028, armW: cfh * 0.034, foreW: cfh * 0.028,
    kneeW: cfh * 0.032, calf: cfh * 0.036, ankle: cfh * 0.02, hand: cfh * 0.045,
  };
  type Body = typeof canon;
  const m = {} as Body;
  for (const key in canon) {
    const k = key as keyof Body;
    m[k] = stylised[k] + (canon[k] - stylised[k]) * blend;
  }

  return m;
}

export function draw(look: Look, pose: Pose, out: Uint8ClampedArray, blend = MIX): void {
  const ids = new Uint8Array(W * H);
  // The figure's bounding box, so shading skips the empty frame around it.
  let minX = W, maxX = 0, minY = H, maxY = 0;
  const put = (x: number, y: number, id: number) => {
    if (x < 0 || x >= W || y < 0 || y >= H) return;
    ids[y * W + x] = id;
    if (x < minX) minX = x; if (x > maxX) maxX = x;
    if (y < minY) minY = y; if (y > maxY) maxY = y;
  };
  // Shapes take base units and rasterise at full resolution. `keep` gets a
  // base-unit position whose +0.5 is the pixel centre, as it always did.
  const ellipse = (
    cx: number, cy: number, rx: number, ry: number, id: number,
    keep: (x: number, y: number) => boolean = () => true,
  ) => {
    for (let Y = Math.floor((cy - ry) * R); Y <= (cy + ry) * R; Y++)
      for (let X = Math.floor((cx - rx) * R); X <= (cx + rx) * R; X++) {
        const x = (X + 0.5) / R, y = (Y + 0.5) / R;
        const dx = (x - cx) / rx, dy = (y - cy) / ry;
        if (dx * dx + dy * dy <= 1 && keep(x - 0.5, y - 0.5)) put(X, Y, id);
      }
  };
  // Scanline fill: for each row, find where the edges cross the pixel
  // centres and fill between pairs of crossings -- one sum per row per edge
  // rather than a test per pixel, which at 4x is the difference between a
  // smooth slider and a stuttering one.
  const crossings: number[] = [];
  const poly = (pts: number[][], id: number) => {
    let y0 = Infinity, y1 = -Infinity;
    for (const p of pts) { y0 = Math.min(y0, p[1]!); y1 = Math.max(y1, p[1]!); }
    for (let Y = Math.floor(y0 * R); Y <= y1 * R; Y++) {
      const py = (Y + 0.5) / R;
      crossings.length = 0;
      for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
        const a = pts[i]!, b = pts[j]!;
        if (a[1]! > py !== b[1]! > py)
          crossings.push(((b[0]! - a[0]!) * (py - a[1]!)) / (b[1]! - a[1]!) + a[0]!);
      }
      crossings.sort((p, q) => p - q);
      for (let c = 0; c + 1 < crossings.length; c += 2)
        // Pixel centres strictly inside the span, matching the old test.
        for (let X = Math.ceil(crossings[c]! * R - 0.5); X + 0.5 < crossings[c + 1]! * R; X++) put(X, Y, id);
    }
  };
  // A shape and its mirror image about the centre line.
  const both = (pts: number[][], left: number, right: number) => {
    poly(pts.map(([x, y]) => [cx - x!, y!]), left);
    poly(pts.map(([x, y]) => [cx + x!, y!]), right);
  };

  const cx = BW / 2;
  const ground = BH - 3;

  // -- proportions: see measure() ----------------------------------------
  const m = measure(look, blend);
  const fh = m.fh, u = m.u;
  const k = u / 17; // scale for features drawn in head-sized pixels
  const top = ground - fh;
  const headY = top + u / 2;
  const chin = top + u;
  const L = ground - chin;
  const shoulderY = top + m.shoulder;
  const chestY = chin + L * m.chest;
  const waistY = chin + L * m.waist;
  const hipY = chin + L * m.hip;
  const crotchY = chin + L * m.crotch;
  const kneeY = chin + L * m.knee;
  const { sw, ww, hw, neck, armW, foreW } = m;

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
  const knee = m.kneeW, calf = m.calf, ankle = m.ankle;
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
  const hand = m.hand;
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

  // Bangs: the cap covers the crown, and below it the hair falls in pointed
  // strands across the forehead, each one ending in a tip at brow level.
  // Strand lengths vary by a fixed pattern, so the fringe looks cut rather
  // than stamped -- but the same every time it is drawn.
  const strand = 2.6 * k;
  const LENGTHS = [0.4, 1.4, 0.2, 1.1, 1.6, 0.5, 1.2, 0.1];
  const fringe = (x: number, y: number) => {
    if (y < headY - 3) return true;
    const along = (x + 0.5 - cx) / strand + 0.5;
    const phase = ((along % 1) + 1) % 1;
    const n = LENGTHS[((Math.floor(along) % 8) + 8) % 8]!;
    return y + 0.5 < headY - 0.6 + n - Math.abs(phase - 0.5) * 2 * 3;
  };
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
  for (let y = Math.max(0, minY - OUTLINE); y <= Math.min(H - 1, maxY + OUTLINE); y++)
    for (let x = Math.max(0, minX - OUTLINE); x <= Math.min(W - 1, maxX + OUTLINE); x++) {
      const i = y * W + x, id = ids[i]!;
      if (id) {
        // Shadow and highlight bands keep their width in base units, so the
        // shading reads the same at any resolution.
        const m = material(id);
        let tone = m[2];
        for (let d = 1; d <= SHADE; d++)
          if (at(x + d, y) !== id || at(x, y + d) !== id) { tone = m[1]; break; }
        if (tone === m[2])
          for (let d = 1; d <= LIGHT; d++)
            if (at(x - d, y) !== id || at(x, y - d) !== id) { tone = m[3]; break; }
        set(i, tone);
      } else {
        // Selective outline: the light comes from the top left, so where the
        // figure lies below or to the right of this pixel the edge is lit
        // and takes the part's own shadow tone; on the far sides it takes
        // the darkest. A flat black line all round is what makes pixel art
        // look like a sticker.
        // At higher resolution the outline thickens with it, so it stays
        // about the weight it was at the original size.
        for (let d = 1; d <= OUTLINE; d++) {
          const lit = at(x + d, y) || at(x, y + d);
          const n = lit || at(x - d, y) || at(x, y - d);
          if (n) { set(i, material(n)[lit ? 1 : 0]); break; }
        }
      }
    }

  // -- face, drawn over the shading at full resolution ----------------------
  // Shapes in base units, like the body, so the face sharpens with R instead
  // of being redrawn for it. Each eye: a white opening, an iris in three
  // bands with a pupil, a heavy upper lid with a flick at the outer corner,
  // a soft lower lash, and two highlights on the side the light comes from.
  // Blush is hatched in short diagonal strokes, as anime draws it.
  const paint = (x0: number, y0: number, x1: number, y1: number, pick: (x: number, y: number) => Rgb | null) => {
    for (let Y = Math.floor(y0 * R); Y < y1 * R; Y++)
      for (let X = Math.floor(x0 * R); X < x1 * R; X++) {
        if (X < 0 || X >= W || Y < 0 || Y >= H) continue;
        const c = pick((X + 0.5) / R, (Y + 0.5) / R);
        if (c) set(Y * W + X, c);
      }
  };
  const inside = (x: number, y: number, ex: number, ey: number, rx: number, ry: number) =>
    ((x - ex) / rx) ** 2 + ((y - ey) / ry) ** 2 <= 1;

  const iris = ramp(look.eyes);
  const deep = mix(iris[1], INK, 0.35);
  const pupil = mix(iris[0], INK, 0.45);
  const white = hex("#f6f2f8"), shade = hex("#d6cfe0"), shine = hex("#ffffff");
  const lash = mix(INK, skin[1], 0.45);
  const brow = mix(hair[1], INK, 0.25);
  const blush = mix(skin[2], hex("#ff6f86"), 0.45);
  const ey = headY + 1.5;
  const erx = 1.55 * k, ery = 1.9 * k;

  for (const side of [-1, 1]) {
    const ex = cx + side * 3.8 * k;
    const outer = side; // +1: the outer corner is to the right
    // Brow: a thin arc, dipping toward the outer end.
    paint(ex - 2.2 * k, ey - 4.5, ex + 2.2 * k, ey - 2, (x, y) => {
      const u = (x - ex) / (2 * k);
      const arc = ey - 3.6 - (1 - u * u) * 0.5 + Math.max(0, u * outer) * 0.6;
      return Math.abs(u) < 1 && Math.abs(y - arc) < 0.22 ? brow : null;
    });
    if (pose.blink) {
      paint(ex - 2 * k, ey - 1, ex + 2 * k, ey + 2, (x, y) => {
        const u = (x - ex) / (1.7 * k);
        return Math.abs(u) < 1 && Math.abs(y - (ey + 0.5 + u * u * 0.5)) < 0.28 ? INK : null;
      });
      continue;
    }
    paint(ex - 2.4 * k, ey - 2.8, ex + 2.4 * k, ey + 2.6, (x, y) => {
      const open = inside(x, y, ex, ey, erx, ery);
      // The upper lid: a thick band hugging the top of the opening, with a
      // flick out past the outer corner.
      const lid = inside(x, y, ex, ey - 0.15, erx + 0.35, ery + 0.25) && y < ey - ery * 0.45;
      const flick = (x - ex) * outer > erx * 0.6 && (x - ex) * outer < erx + 0.9 &&
        Math.abs(y - (ey - ery * 0.55 - ((x - ex) * outer - erx * 0.6) * 0.35)) < 0.3;
      if (lid || flick) return INK;
      if (!open) {
        // Lower lash, under the outer half only.
        const below = inside(x, y, ex, ey, erx, ery + 0.3) && y > ey + ery * 0.5;
        return below && (x - ex) * outer > -0.2 ? lash : null;
      }
      const ix = ex - side * 0.05, iy = ey + 0.15;
      if (inside(x, y, ex - 0.55 * k, ey - 0.45, 0.42 * k, 0.42 * k)) return shine;
      if (inside(x, y, ex + 0.55 * k, ey + 0.85, 0.22 * k, 0.22 * k)) return shine;
      if (inside(x, y, ix, iy, 1.15 * k, ery * 0.86)) {
        if (inside(x, y, ix, iy + 0.1, 0.45 * k, 0.8)) return pupil;
        const v = (y - (iy - ery)) / (ery * 2);
        return v < 0.35 ? deep : v < 0.72 ? iris[2] : iris[3];
      }
      return y < ey - ery * 0.2 ? shade : white;
    });
    // Blush: three short diagonal strokes on the cheek.
    paint(ex - 2 * k, ey + 2.2, ex + 2 * k, ey + 3.6, (x, y) => {
      const d = ((x - ex + 2 * k) - (ey + 3.4 - y)) / (1.15 * k);
      return Math.abs(d - Math.round(d)) < 0.12 && Math.round(d) >= 1 && Math.round(d) <= 3 ? blush : null;
    });
  }

  // Nose: a small shadow on the far side from the light. Mouth: a short,
  // soft line, darker at its centre.
  paint(cx + 0.1, ey + 3.1, cx + 0.45, ey + 3.45, () => skin[1]);
  const my = chin - 2.4;
  const lip = mix(skin[1], hex("#b03050"), 0.45), corner = mix(skin[1], hex("#b03050"), 0.2);
  paint(cx - 0.75, my - 0.14, cx + 0.75, my + 0.14, (x) => (Math.abs(x - cx) < 0.35 ? lip : corner));
}
