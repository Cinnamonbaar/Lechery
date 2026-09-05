import { describe, expect, it } from "vitest";

import { MovementInput, stickVector } from "./input";

describe("MovementInput", () => {
  it("sums held keys", () => {
    const input = new MovementInput();
    input.keyDown("KeyW");
    input.keyDown("KeyD");
    expect(input.vector).toEqual([1, -1]);
    input.keyUp("KeyW");
    expect(input.vector).toEqual([1, 0]);
  });

  it("ignores keys it does not use", () => {
    const input = new MovementInput();
    expect(input.keyDown("KeyQ")).toBe(false);
    expect(input.active).toBe(false);
  });

  it("adds the stick to the keys", () => {
    const input = new MovementInput();
    input.stick = [0.5, 0];
    input.keyDown("ArrowDown");
    expect(input.vector).toEqual([0.5, 1]);
    input.clear();
    expect(input.vector).toEqual([0, 0]);
  });
});

describe("stickVector", () => {
  it("has a dead zone", () => {
    expect(stickVector(2, 0, 60)).toEqual([0, 0]);
  });

  it("is analogue up to the edge and clamped past it", () => {
    const [x] = stickVector(30, 0, 60);
    expect(x).toBeCloseTo(0.5);
    expect(stickVector(600, 0, 60)[0]).toBeCloseTo(1);
  });
});
