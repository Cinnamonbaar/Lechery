import { describe, expect, it } from "vitest";
import { draw, H, W, type Look } from "./doll";

const look: Look = { height: 168, build: 0.5, bust: 4, endowment: 0, skin: "#f1c9a8", hair: "#3a2a3f", eyes: "#4f7bb8", style: 2 };
const pose = { blink: false, breath: 0 };

function render(l: Look) {
  const out = new Uint8ClampedArray(W * H * 4);
  draw(l, pose, out);
  return out;
}

const rowsUsed = (out: Uint8ClampedArray) => {
  let first = H;
  for (let i = 3; i < out.length; i += 4) if (out[i]) { first = Math.floor(i / 4 / W); break; }
  return H - first;
};

const opaque = (out: Uint8ClampedArray) => {
  let n = 0;
  for (let i = 3; i < out.length; i += 4) if (out[i]) n++;
  return n;
};

describe("draw", () => {
  it("draws every hair style at every extreme without throwing", () => {
    for (let style = 0; style < 5; style++)
      for (const height of [145, 195])
        for (const v of [0, 1])
          expect(() => render({ ...look, style, height, build: v, bust: v * 10, endowment: v * 10 })).not.toThrow();
  });

  it("a taller character takes more of the frame", () => {
    expect(rowsUsed(render({ ...look, height: 190 }))).toBeGreaterThan(rowsUsed(render({ ...look, height: 150 })));
  });

  it("stays inside the frame at the tallest", () => {
    expect(rowsUsed(render({ ...look, height: 195, style: 0 }))).toBeLessThan(H);
  });

  it("bust size changes the drawing, and flat draws no bra", () => {
    const flat = render({ ...look, bust: 0 }), full = render({ ...look, bust: 10 });
    expect(full.some((v, i) => v !== flat[i])).toBe(true);
    expect(opaque(full)).toBeGreaterThanOrEqual(opaque(flat));
  });

});
