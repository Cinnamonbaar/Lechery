import { describe, expect, it } from "vitest";

import { cameraFor } from "./render";
import { Tile, TileMap } from "../space/tiles";
import { RoomMap } from "../space/carve";

const roomMap = (width: number, height: number) =>
  new RoomMap("r", new TileMap(width, height, Tile.FLOOR), new Map());

describe("cameraFor", () => {
  it("covers the view, leaving no dead space", () => {
    const camera = cameraFor(roomMap(19, 13), 390, 340, [9.5, 6.5]);
    expect(19 * camera.scale).toBeGreaterThanOrEqual(390);
    expect(13 * camera.scale).toBeGreaterThanOrEqual(340);
  });

  it("scrolls the axis that overflows and centres the one that fits", () => {
    // Wide pane, so the room's height is the constraint: it fills vertically
    // and the view slides along the room's width.
    const camera = cameraFor(roomMap(40, 13), 800, 400, [30, 6.5]);
    expect(camera.y).toBeCloseTo(0);
    expect(camera.x).toBeGreaterThan(0);
  });

  it("keeps the camera inside the room at the edges", () => {
    const room = roomMap(19, 13);
    const camera = cameraFor(room, 390, 340, [0, 0]);
    expect(camera.x).toBeGreaterThanOrEqual(0);
    expect(camera.y).toBeGreaterThanOrEqual(0);

    const far = cameraFor(room, 390, 340, [19, 13]);
    expect(far.x + 390 / far.scale).toBeLessThanOrEqual(19.001);
    expect(far.y + 340 / far.scale).toBeLessThanOrEqual(13.001);
  });
});
