/**
 * The drawing machinery every part shares.
 *
 * Parts rasterise shapes into a buffer of part ids; `shade` then colours
 * the buffer by one rule: a pixel whose neighbour below or to the right is
 * a different part takes the shadow tone, one whose neighbour above or to
 * the left is takes the highlight, and empty pixels touching the figure
 * become its outline. That rule is what makes a pile of ellipses read as
 * pixel art, and why a part can be any size at all.
 *
 * Shapes are given in base units on a 64x132 frame and rasterised R times
 * finer, so proportions never depend on resolution.
 */

export const R = 4;
export const BW = 64, BH = 132;
export const W = BW * R, H = BH * R;
const OUTLINE = Math.max(1, R / 2);
const SHADE = R, LIGHT = Math.max(1, R / 2);

export type Rgb = [number, number, number];
export type Ramp = [outline: Rgb, dark: Rgb, base: Rgb, light: Rgb];

export const hex = (h: string): Rgb => {
  const n = parseInt(h.slice(1), 16);
  return [n >> 16, (n >> 8) & 255, n & 255];
};

export const mix = (a: Rgb, b: Rgb, t: number): Rgb =>
  [0, 1, 2].map((i) => Math.round(a[i]! + (b[i]! - a[i]!) * t)) as Rgb;

// Shadows lean purple and highlights warm, the way anime colouring does,
// rather than simply darkening and lightening.
const SHADOW = hex("#3b2752");
const GLOW = hex("#fff4e0");
export const INK = hex("#1c1222");

export function ramp(base: string): Ramp {
  const b = hex(base);
  return [mix(b, INK, 0.7), mix(b, SHADOW, 0.38), b, mix(b, GLOW, 0.3)];
}

export type Raster = ReturnType<typeof raster>;

export function raster(out: Uint8ClampedArray) {
  const ids = new Uint8Array(W * H);
  // The figure's bounding box, so shading skips the empty frame around it.
  let minX = W, maxX = 0, minY = H, maxY = 0;
  const put = (x: number, y: number, id: number) => {
    if (x < 0 || x >= W || y < 0 || y >= H) return;
    ids[y * W + x] = id;
    if (x < minX) minX = x; if (x > maxX) maxX = x;
    if (y < minY) minY = y; if (y > maxY) maxY = y;
  };

  // `keep` gets a base-unit position whose +0.5 is the pixel centre.
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

  // Scanline fill: per row, find where the edges cross the pixel centres
  // and fill between pairs -- one sum per row per edge rather than a test
  // per pixel, which at 4x keeps the slider spring smooth on a phone.
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
        for (let X = Math.ceil(crossings[c]! * R - 0.5); X + 0.5 < crossings[c + 1]! * R; X++) put(X, Y, id);
    }
  };

  /** A shape and its mirror image about x = cx. */
  const both = (cx: number, pts: number[][], left: number, right: number) => {
    poly(pts.map(([x, y]) => [cx - x!, y!]), left);
    poly(pts.map(([x, y]) => [cx + x!, y!]), right);
  };

  const at = (x: number, y: number) => (x < 0 || x >= W || y < 0 || y >= H ? 0 : ids[y * W + x]!);
  const set = (i: number, c: Rgb) => {
    out[i * 4] = c[0]; out[i * 4 + 1] = c[1]; out[i * 4 + 2] = c[2]; out[i * 4 + 3] = 255;
  };

  /** Colour every part, then outline the figure by the light. */
  const shade = (material: (id: number) => Ramp) => {
    out.fill(0);
    for (let y = Math.max(0, minY - OUTLINE); y <= Math.min(H - 1, maxY + OUTLINE); y++)
      for (let x = Math.max(0, minX - OUTLINE); x <= Math.min(W - 1, maxX + OUTLINE); x++) {
        const i = y * W + x, id = ids[i]!;
        if (id) {
          // Bands keep their width in base units, so shading reads the
          // same at any resolution.
          const m = material(id);
          let tone = m[2];
          for (let d = 1; d <= SHADE; d++)
            if (at(x + d, y) !== id || at(x, y + d) !== id) { tone = m[1]; break; }
          if (tone === m[2])
            for (let d = 1; d <= LIGHT; d++)
              if (at(x - d, y) !== id || at(x, y - d) !== id) { tone = m[3]; break; }
          set(i, tone);
        } else {
          // Selective outline: where the figure lies below or right of this
          // pixel, the edge faces the light and takes the part's shadow
          // tone; on the far sides, the darkest.
          for (let d = 1; d <= OUTLINE; d++) {
            const lit = at(x + d, y) || at(x, y + d);
            const n = lit || at(x - d, y) || at(x, y - d);
            if (n) { set(i, material(n)[lit ? 1 : 0]); break; }
          }
        }
      }
  };

  /** Paint straight over the shading, unshaded: for the face. */
  const paint = (x0: number, y0: number, x1: number, y1: number, pick: (x: number, y: number) => Rgb | null) => {
    for (let Y = Math.floor(y0 * R); Y < y1 * R; Y++)
      for (let X = Math.floor(x0 * R); X < x1 * R; X++) {
        if (X < 0 || X >= W || Y < 0 || Y >= H) continue;
        const c = pick((X + 0.5) / R, (Y + 0.5) / R);
        if (c) set(Y * W + X, c);
      }
  };

  /** The part at a base-unit position, for painting that depends on it. */
  const id = (x: number, y: number) => at(Math.floor(x * R), Math.floor(y * R));

  return { ellipse, poly, both, shade, paint, id };
}
