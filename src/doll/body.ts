/** The body below the head: measurements, then torso, limbs and clothes. */
import { ARM_L, ARM_R, BRA_L, BRA_R, BRIEFS, BULGE, BUST_L, BUST_R, LEG_L, LEG_R, NECK, TORSO, type Look, type Pose } from "./ids";
import type { Raster } from "./raster";

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

/** Where everything is, in base units. Parts are drawn from this. */
export function landmarks(look: Look, blend: number, cx: number, ground: number) {
  const m = measure(look, blend);
  const top = ground - m.fh, chin = top + m.u, L = ground - chin;
  return {
    m, cx, ground, top, chin,
    shoulderY: top + m.shoulder,
    chestY: chin + L * m.chest,
    waistY: chin + L * m.waist,
    hipY: chin + L * m.hip,
    crotchY: chin + L * m.crotch,
    kneeY: chin + L * m.knee,
  };
}

export type Landmarks = ReturnType<typeof landmarks>;

export function drawBody(r: Raster, a: Landmarks, look: Look, pose: Pose) {
  const { m, cx, ground, chin, shoulderY, chestY, waistY, hipY, crotchY, kneeY } = a;
  const { sw, ww, hw, neck, armW, foreW } = m;
  const both = (pts: number[][], left: number, right: number) => r.both(cx, pts, left, right);

  // Legs: the thigh fills the hip, tapering to a knee, a calf with some
  // shape below it, and a slim ankle.
  const knee = m.kneeW, calf = m.calf, ankle = m.ankle;
  const legX = hw * 0.5;
  both([[hw, hipY], [0.4, crotchY], [legX - knee + 0.5, kneeY], [legX - ankle * 0.6, ground - 1], [legX + ankle * 1.4, ground - 1], [legX + calf, kneeY + (ground - kneeY) * 0.3], [legX + knee, kneeY], [hw * 0.92, (hipY + kneeY) / 2]], LEG_L, LEG_R);
  r.ellipse(cx - legX, ground - 0.8, ankle + 1.6, 1.6, LEG_L);
  r.ellipse(cx + legX, ground - 0.8, ankle + 1.6, 1.6, LEG_R);

  // The trapezius slopes from the neck to the shoulder rather than running
  // flat: a level line there is what reads as a coat hanger.
  const side = [[neck + (sw - neck) * 0.45, shoulderY - 0.6], [sw - armW * 0.5, shoulderY + 1.6], [sw - armW * 0.9, chestY + 1], [ww, waistY], [hw, hipY], [hw - 0.6, crotchY - 1], [0.5, crotchY + 0.5]];
  r.poly([[cx - neck, shoulderY - 2.4], [cx + neck, shoulderY - 2.4], ...side.map(([x, y]) => [cx + x!, y!]), ...side.reverse().map(([x, y]) => [cx - x!, y!])], TORSO);
  r.poly([[cx - neck, chin - 2], [cx + neck, chin - 2], [cx + neck + 0.3, shoulderY + 0.5], [cx - neck - 0.3, shoulderY + 0.5]], NECK);

  // Arms: elbow at the waist, wrist at the crotch, fingertips at mid-thigh,
  // angling out only as far as they must to clear the waist and the hip.
  const shoulderX = sw - armW * 0.5;
  const elbowX = Math.max(shoulderX, ww + armW * 0.5 + 0.4);
  const wristX = Math.max(elbowX, hw + foreW * 0.5 + 0.4);
  const limb = (x0: number, y0: number, w0: number, x1: number, y1: number, w1: number) =>
    both([[x0 - w0 / 2, y0], [x0 + w0 / 2, y0], [x1 + w1 / 2, y1], [x1 - w1 / 2, y1]], ARM_L, ARM_R);
  limb(shoulderX, shoulderY + armW * 0.6, armW, elbowX, waistY, armW * 0.85);
  limb(elbowX, waistY, armW * 0.85, wristX, crotchY, foreW * 0.75);
  r.ellipse(cx - shoulderX, shoulderY + armW * 0.85, armW * 0.6, armW * 0.7, ARM_L);
  r.ellipse(cx + shoulderX, shoulderY + armW * 0.85, armW * 0.6, armW * 0.7, ARM_R);
  r.ellipse(cx - wristX, crotchY + m.hand * 0.9, foreW * 0.55, m.hand, ARM_L);
  r.ellipse(cx + wristX, crotchY + m.hand * 0.9, foreW * 0.55, m.hand, ARM_R);

  // The bust sits on the nipple line and scales with the frame, so a cup
  // size reads the same on a short character as on a tall one.
  const f = m.fh / 110;
  const rad = (1.4 + look.bust * 0.56) * f;
  const by = chestY - 0.5 + look.bust * 0.36 * f - pose.breath;
  const bx = Math.min(1.1 + rad * 0.86, sw - rad * 0.45);
  if (look.bust > 0.3) {
    r.ellipse(cx - bx, by, rad, rad * 0.95, BUST_L);
    r.ellipse(cx + bx, by, rad, rad * 0.95, BUST_R);
    const cup = (s: number) => (x: number, y: number) => y + 0.5 > by - rad * 0.15 && (s < 0 ? x < cx : x >= cx);
    r.ellipse(cx - bx, by, rad + 0.35, rad * 0.95 + 0.35, BRA_L, cup(-1));
    r.ellipse(cx + bx, by, rad + 0.35, rad * 0.95 + 0.35, BRA_R, cup(1));
  }

  r.poly([[cx - hw + 0.4, hipY + 0.5], [cx + hw - 0.4, hipY + 0.5], [cx + hw - 1.4, crotchY - 1], [cx + 1.6, crotchY + 2], [cx - 1.6, crotchY + 2], [cx - hw + 1.4, crotchY - 1]], BRIEFS);
  if (look.endowment > 0.3) r.ellipse(cx, crotchY - 0.2, (1.3 + look.endowment * 0.13) * f, (1.5 + look.endowment * 0.2) * f, BULGE);
}
