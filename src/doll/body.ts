/**
 * The body below the head, drawn as smooth curves through silhouettes
 * measured from the owner's chosen anime references (see profiles.ts and
 * docs/art.md). The build slider blends from the male figure (0) through a
 * female one (0.5) to the curviest (1).
 */
import { ARM_L, ARM_R, BRA_L, BRA_R, BRIEFS, BULGE, BUST_L, BUST_R, LEG_L, LEG_R, TORSO, type Look, type Pose } from "./ids";
import { PROFILES, SAMPLES, sampleT, type Profile } from "./profiles";
import type { Raster } from "./raster";

/** Head height as a fraction of total height: 7.3 heads, as measured. */
export const HEAD_FRACTION = 0.137;
/** How far the head sits below the top of the figure, as a fraction of
 * height: the crown dips so the chin lands near the reference's 0.145 and
 * the neck is not drawn out. */
export const HEAD_DROP = 0.012;
/** The first sample at which an arm hangs from the shoulder. */
const ARM_TOP = 3;

type Curves = { body: number[]; aOut: number[]; aIn: number[]; lOut: number[]; lIn: number[]; armpit: number; crotch: number; hand: number };

/** A profile with every curve defined at every sample, so profiles blend. */
function fill(p: Profile): Curves {
  const aw = p.armOut[p.armpit]! - p.armIn[p.armpit]!;
  let hand = p.armpit;
  while (hand + 1 < SAMPLES && p.armOut[hand + 1]) hand++;
  const c: Curves = { body: [], aOut: [], aIn: [], lOut: [], lIn: [], armpit: p.armpit, crotch: p.crotch, hand };
  for (let i = 0; i < SAMPLES; i++) {
    const t = p.torso[i]!, top = p.torso[Math.max(i, ARM_TOP)]!;
    // Above the armpit the measured width includes the arms; the body is
    // what is left once the arm's width comes off it.
    c.body.push(i < ARM_TOP ? t : i < p.armpit ? t - aw + 4 : i < p.crotch ? t : p.torso[p.crotch - 1]!);
    c.aOut.push(i < p.armpit ? top : p.armOut[Math.min(i, hand)]!);
    c.aIn.push(i < p.armpit ? top - aw : p.armIn[Math.min(i, hand)]!);
    c.lOut.push(i < p.crotch ? c.body[i]! : p.legOut[i]!);
    c.lIn.push(i < p.crotch ? 0 : p.legIn[i]!);
  }
  return c;
}

const FILLED = PROFILES.map(fill);

/** Blend the measured figures for a build, 0 straight to 1 curvy. */
function curves(build: number): Curves {
  const at = Math.min(Math.max(build, 0), 1) * (FILLED.length - 1);
  const a = FILLED[Math.floor(at)]!, b = FILLED[Math.min(Math.floor(at) + 1, FILLED.length - 1)]!, w = at - Math.floor(at);
  const mix = (x: number[], y: number[]) => x.map((v, i) => v + (y[i]! - v) * w);
  const c: Curves = {
    body: mix(a.body, b.body), aOut: mix(a.aOut, b.aOut), aIn: mix(a.aIn, b.aIn),
    lOut: mix(a.lOut, b.lOut), lIn: mix(a.lIn, b.lIn),
    armpit: a.armpit + (b.armpit - a.armpit) * w, crotch: a.crotch + (b.crotch - a.crotch) * w, hand: Math.min(a.hand, b.hand),
  };
  // The hand is where the measured edges are noisiest (fingers); a light
  // smoothing keeps it a hand rather than a fringe.
  for (const k of ["aOut", "aIn"] as const) {
    const s = c[k].slice();
    for (let i = Math.ceil(c.armpit); i < c.hand; i++) s[i] = (c[k][i - 1]! + 2 * c[k][i]! + c[k][i + 1]!) / 4;
    c[k] = s;
  }
  return c;
}

/** Halve the spacing of a polyline with a Catmull-Rom midpoint per segment,
 * so curves through the samples read as curves, not facets. */
export function smooth(pts: number[][]): number[][] {
  const out: number[][] = [];
  for (let i = 0; i < pts.length; i++) {
    const p1 = pts[i]!, p2 = pts[i + 1];
    out.push(p1);
    if (!p2) break;
    const p0 = pts[i - 1] ?? p1, p3 = pts[i + 2] ?? p2;
    out.push([(-p0[0]! + 9 * p1[0]! + 9 * p2[0]! - p3[0]!) / 16, (p1[1]! + p2[1]!) / 2]);
  }
  return out;
}

/** Where everything is, in base units. Parts are drawn from this. */
export function landmarks(look: Look, cx: number, ground: number) {
  const t = (Math.min(Math.max(look.height, 145), 195) - 145) / 50;
  const fh = 96 + t * 28, top = ground - fh, u = fh * HEAD_FRACTION;
  const c = curves(look.build);
  const y = (f: number) => top + fh * f;
  return {
    cx, ground, top, fh, u, c, crown: top + fh * HEAD_DROP, chin: top + fh * HEAD_DROP + u,
    shoulderY: y(0.19), chestY: y(0.26), waistY: y(0.34), hipY: y(0.47),
    crotchY: y(sampleT(c.crotch)), kneeY: y(0.67),
  };
}

export type Landmarks = ReturnType<typeof landmarks>;

export function drawBody(r: Raster, a: Landmarks, look: Look, pose: Pose) {
  const { cx, top, fh, c, chestY, crotchY } = a;
  const X = (v: number) => (v / 1000) * fh, Y = (i: number) => top + fh * sampleT(i);
  // Width of a curve at any height, between samples.
  const at = (k: number[], f: number) => {
    const i = (f - 0.14) / 0.02, j = Math.floor(i);
    return X(k[j]! + ((k[j + 1] ?? k[j]!) - k[j]!) * (i - j));
  };
  const side = (pts: number[][]) => smooth(pts);
  const mirror = (pts: number[][], left: number, right: number) => {
    r.poly(pts.map(([x, y]) => [cx + x!, y!]), right);
    r.poly(pts.map(([x, y]) => [cx - x!, y!]), left);
  };

  // The groin V of the owner's references: from the hip side at 44% straight
  // down to the crotch (measured 0.44-0.455, meeting at 0.50). The torso
  // ends on it and the legs start above it, so their seam is that line.
  const V = (0.44 - sampleT(0)) / 0.02;

  // Legs: outer edge down, inner edge back up, from the hips to the soles.
  const c0 = V - 1, last = SAMPLES - 1;
  const outer: number[][] = [], inner: number[][] = [];
  for (let i = c0; i <= last; i++) { outer.push([X(c.lOut[i]!), Y(i)]); inner.push([X(c.lIn[i]!), Y(i)]); }
  mirror([...side(outer), ...side(inner).reverse()], LEG_L, LEG_R);

  // The torso, neck to crotch, as one shape: the shoulder slope, chest,
  // waist and hips are all the measured curve.
  // The neck starts up under the jaw, so no seam shows between them.
  const body: number[][] = [[X(c.body[0]!), a.chin - a.u * 0.2]];
  for (let i = 0; i <= V; i++) body.push([X(c.body[i]!), Y(i)]);
  const right = [...side(body), [0.4, crotchY]];
  r.poly([...right, ...right.slice().reverse().map(([x, y]) => [-x!, y!])].map(([x, y]) => [cx + x!, y!]), TORSO);

  // Arms: from the shoulder to the fingertips. The top is a dome that
  // continues the measured shoulder slope -- the deltoid -- rather than a
  // flat cut, which reads as a square shoulder.
  const ao: number[][] = [], ai: number[][] = [];
  for (let i = ARM_TOP; i <= c.hand; i++) { ao.push([X(c.aOut[i]!), Y(i)]); ai.push([X(c.aIn[i]!), Y(i)]); }
  const o0 = ao[0]!, i0 = ai[0]!;
  ao.unshift([o0[0]! * 0.55 + i0[0]! * 0.45, o0[1]! - fh * 0.016]);
  ai.unshift([i0[0]!, i0[1]! - fh * 0.009]);
  mirror([...side(ao), ...side(ai).reverse()], ARM_L, ARM_R);

  // The bust sits on the chest line and scales with the frame, so a cup
  // size reads the same on a short character as on a tall one.
  const f = fh / 110, chest = at(c.body, 0.27);
  const rad = (1.4 + look.bust * 0.56) * f;
  const by = chestY + look.bust * 0.36 * f - pose.breath;
  const bx = Math.min(1.1 + rad * 0.86, chest - rad * 0.45);
  if (look.bust > 0.3) {
    r.ellipse(cx - bx, by, rad, rad * 0.95, BUST_L);
    r.ellipse(cx + bx, by, rad, rad * 0.95, BUST_R);
    const cup = (s: number) => (x: number, y: number) => y + 0.5 > by - rad * 0.15 && (s < 0 ? x < cx : x >= cx);
    r.ellipse(cx - bx, by, rad + 0.35, rad * 0.95 + 0.35, BRA_L, cup(-1));
    r.ellipse(cx + bx, by, rad + 0.35, rad * 0.95 + 0.35, BRA_R, cup(1));
  }

  // Briefs: a low band at 43%, the leg openings along the groin V.
  const bt = 0.43, hipW = at(c.body, bt), vW = at(c.body, 0.44);
  r.poly([[cx - hipW + 0.3, top + fh * bt], [cx + hipW - 0.3, top + fh * bt], [cx + vW - 0.3, Y(V)], [cx + 1.2, crotchY], [cx - 1.2, crotchY], [cx - vW + 0.3, Y(V)]], BRIEFS);
  if (look.endowment > 0.3) r.ellipse(cx, crotchY - 0.2, (1.3 + look.endowment * 0.13) * f, (1.5 + look.endowment * 0.2) * f, BULGE);
}
