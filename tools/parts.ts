/**
 * The parts sheet: each part of the doll drawn on its own, with the guide
 * lines its proportions are built on, so one part can be tuned without the
 * others in the way. Development only -- nothing here ships.
 *
 *   npm run parts -- [outdir]
 *
 * Writes head.png (head and face, with facial thirds, eye line and the rule
 * of fifths), hair.png (each style alone, then on the head) and body.png.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { ALL, BODY, draw, FACE, H, HAIR_BACK_LAYER, HAIR_FRONT_LAYER, HEAD_LAYER, layout, R, STYLE_COUNT, W, type Look } from "../src/doll";
import { BROW_Y, EYE_Y, MOUTH_Y, NOSE_Y } from "../src/doll/face";
import { FRINGE_END } from "../src/doll/hair";
import { png } from "./png";

const dir = process.argv[2] ?? "parts-out";
mkdirSync(dir, { recursive: true });

const base: Look = { height: 168, build: 0.5, bust: 4, endowment: 0, skin: "#f3d2b8", hair: "#3a2a3f", eyes: "#4f7bb8", style: 2 };
const pose = { blink: false, breath: 0 };
const BG = [22, 26, 38, 255];

type Rgba = [number, number, number, number];
interface Panel { look: Look; layers: number; box: [x: number, y: number, w: number, h: number]; guides?: boolean }

/** Lay panels out in a row, each cropped to its box (base units) and zoomed. */
function sheet(file: string, panels: Panel[], zoom: number) {
  const cell = (p: Panel) => [Math.round(p.box[2] * R * zoom), Math.round(p.box[3] * R * zoom)] as const;
  const gap = 12;
  const width = panels.reduce((s, p) => s + cell(p)[0] + gap, gap);
  const height = Math.max(...panels.map((p) => cell(p)[1])) + gap * 2;
  const img = new Uint8Array(width * height * 4);
  for (let i = 0; i < width * height; i++) img.set(BG, i * 4);
  const dot = (x: number, y: number, c: Rgba) => {
    if (x < 0 || y < 0 || x >= width || y >= height) return;
    const i = (y * width + x) * 4, a = c[3] / 255;
    for (let k = 0; k < 3; k++) img[i + k] = Math.round(img[i + k]! * (1 - a) + c[k]! * a);
  };

  let left = gap;
  for (const p of panels) {
    const out = new Uint8ClampedArray(W * H * 4);
    draw(p.look, pose, out, p.layers);
    const [cw, ch] = cell(p);
    const s = zoom; // output pixels per raster pixel
    for (let y = 0; y < ch; y++)
      for (let x = 0; x < cw; x++) {
        const X = Math.floor(p.box[0] * R + x / s), Y = Math.floor(p.box[1] * R + y / s);
        if (X < 0 || Y < 0 || X >= W || Y >= H) continue;
        const q = (Y * W + X) * 4;
        if (out[q + 3]) dot(left + x, gap + y, [out[q]!, out[q + 1]!, out[q + 2]!, 255]);
      }
    if (p.guides) {
      // Lines in base units, mapped into this panel.
      const toX = (bx: number) => Math.round(left + (bx - p.box[0]) * R * s);
      const toY = (by: number) => Math.round(gap + (by - p.box[1]) * R * s);
      const hline = (by: number, c: Rgba) => { for (let x = 0; x < cw; x++) dot(left + x, toY(by), c); };
      const vline = (bx: number, c: Rgba) => { for (let y = 0; y < ch; y++) dot(toX(bx), gap + y, c); };
      const { head } = layout(p.look);
      const y = (f: number) => head.top + head.h * f;
      const gold: Rgba = [216, 194, 143, 200], cyan: Rgba = [90, 200, 230, 170], pink: Rgba = [240, 110, 160, 170];
      // Crown and chin, and the facial thirds: hairline? brow, nose, chin.
      hline(head.top, gold); hline(y(1), gold);
      hline(y(BROW_Y), cyan); hline(y(NOSE_Y), cyan);
      hline(y(EYE_Y), pink); hline(y(MOUTH_Y), [180, 140, 220, 160]);
      hline(y(FRINGE_END), [255, 255, 255, 60]);
      // The rule of fifths, across the head's width.
      for (let i = 0; i <= 5; i++) vline(head.cx - head.w / 2 + (head.w * i) / 5, [90, 200, 230, 90]);
    }
    left += cw + gap;
  }
  writeFileSync(join(dir, file), png(img, width, height));
}

const headCrop = (look: Look): [number, number, number, number] => {
  const { head } = layout(look);
  return [head.cx - head.w * 0.85, head.top - head.h * 0.2, head.w * 1.7, head.h * 1.45];
};

sheet("head.png", [
  { look: base, layers: HEAD_LAYER, box: headCrop(base), guides: true },
  { look: base, layers: HEAD_LAYER | FACE, box: headCrop(base), guides: true },
  { look: base, layers: HEAD_LAYER | FACE, box: headCrop(base) },
], 3);

const styles = Array.from({ length: STYLE_COUNT }, (_, style) => ({ ...base, style }));
const tall = (look: Look): [number, number, number, number] => {
  const { head } = layout(look);
  return [head.cx - head.w * 1.1, head.top - head.h * 0.25, head.w * 2.2, head.h * 3.2];
};
sheet("hair.png", [
  ...styles.map((look) => ({ look, layers: HAIR_BACK_LAYER | HAIR_FRONT_LAYER, box: tall(look) })),
  ...styles.map((look) => ({ look, layers: ALL & ~BODY, box: tall(look), guides: true })),
], 1.5);

sheet("body.png", [
  { look: { ...base, build: 0 }, layers: BODY, box: [0, 0, 64, 132] },
  { look: { ...base, build: 1, bust: 7 }, layers: BODY, box: [0, 0, 64, 132] },
  { look: { ...base, build: 1, bust: 7 }, layers: ALL, box: [0, 0, 64, 132] },
], 1);

console.log(`wrote head.png, hair.png, body.png to ${dir}`);
