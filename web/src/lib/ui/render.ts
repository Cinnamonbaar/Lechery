/**
 * Drawing a room.
 *
 * Rooms that fit the viewport are framed whole with a fixed camera; rooms
 * bigger than it scroll to follow the player. One code path decides which by
 * comparing sizes, because "town" and "dungeon room" differ only in how big
 * they were authored.
 */

import type { RoomMap } from "../space/carve";
import type { Portal } from "../space/level";
import { Tile } from "../space/tiles";
import type { WorldPalette } from "./theme";

/** Tiles across the short axis the camera tries to keep in view. */
export const TARGET_TILES = 13;

export interface Camera {
  /** Device pixels per tile. */
  readonly scale: number;
  /** Top-left of the view, in tile units. */
  readonly x: number;
  readonly y: number;
}

/**
 * Choose a camera for a room.
 *
 * The scale comes from the *view*, not the room, so the player pawn is the
 * same size on screen everywhere; a room bigger than the view then scrolls
 * rather than zooming out, which is what makes a town feel bigger than a
 * corridor instead of just more distant.
 */
export function cameraFor(
  roomMap: RoomMap,
  viewWidth: number,
  viewHeight: number,
  focus: readonly [number, number],
): Camera {
  const [width, height] = roomMap.size;
  const short = Math.min(viewWidth, viewHeight);
  const scale = Math.max(8, short / TARGET_TILES);

  const tilesAcross = viewWidth / scale;
  const tilesDown = viewHeight / scale;

  const axis = (span: number, room: number, centre: number): number => {
    if (room <= span) return (room - span) / 2; // framed whole, centred
    return Math.max(0, Math.min(room - span, centre - span / 2));
  };

  return {
    scale,
    x: axis(tilesAcross, width, focus[0]),
    y: axis(tilesDown, height, focus[1]),
  };
}

export interface DrawOptions {
  readonly roomMap: RoomMap;
  readonly camera: Camera;
  readonly palette: WorldPalette;
  readonly player: readonly [number, number];
  readonly playerRadius: number;
  readonly facing: number;
  readonly portals?: readonly Portal[];
  /** Milliseconds since the session began, for the little idle animations. */
  readonly time?: number;
}

export function drawRoom(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  options: DrawOptions,
): void {
  const { roomMap, camera, palette } = options;
  const { scale } = camera;

  context.fillStyle = palette.void;
  context.fillRect(0, 0, width, height);

  const left = Math.floor(camera.x);
  const top = Math.floor(camera.y);
  const right = Math.ceil(camera.x + width / scale);
  const bottom = Math.ceil(camera.y + height / scale);

  const screenX = (tileX: number) => (tileX - camera.x) * scale;
  const screenY = (tileY: number) => (tileY - camera.y) * scale;

  for (let y = top; y < bottom; y += 1) {
    for (let x = left; x < right; x += 1) {
      const tile = roomMap.tilemap.get(x, y);
      if (tile === Tile.VOID) continue;

      // A checker on the floor gives the eye something to judge movement
      // against; without it a big empty room reads as not scrolling at all.
      let fill: string;
      if (tile === Tile.WALL) fill = palette.wall;
      else if (tile === Tile.DOORWAY) fill = palette.doorway;
      else if (tile === Tile.TRAP) fill = palette.trap;
      else fill = (x + y) % 2 === 0 ? palette.floor : palette.floorAlt;

      context.fillStyle = fill;
      // Ceil the span so neighbouring tiles never leave a seam at
      // fractional scales.
      context.fillRect(
        Math.floor(screenX(x)),
        Math.floor(screenY(y)),
        Math.ceil(scale) + 1,
        Math.ceil(scale) + 1,
      );

      // A lighter cap on any wall whose southern face is exposed: enough
      // depth cue to read the room's shape at a glance.
      if (tile === Tile.WALL && roomMap.tilemap.get(x, y + 1) !== Tile.WALL) {
        context.fillStyle = palette.wallTop;
        context.fillRect(
          Math.floor(screenX(x)),
          Math.floor(screenY(y + 1)) - Math.ceil(scale * 0.18),
          Math.ceil(scale) + 1,
          Math.ceil(scale * 0.18),
        );
      }
    }
  }

  for (const portal of options.portals ?? []) {
    const pulse = 0.55 + 0.2 * Math.sin((options.time ?? 0) / 320);
    context.save();
    context.globalAlpha = pulse;
    context.fillStyle = palette.portal;
    context.beginPath();
    context.ellipse(
      screenX(portal.tile[0] + 0.5),
      screenY(portal.tile[1] + 0.5),
      scale * 0.42,
      scale * 0.28,
      0,
      0,
      Math.PI * 2,
    );
    context.fill();
    context.restore();
  }

  drawPawn(context, options, screenX, screenY);
}

/**
 * The player: an anonymous grey silhouette.
 *
 * Deliberately not a portrait. What the character actually looks like changes
 * constantly and belongs to the paperdoll; the pawn only has to say "you are
 * here, and facing that way".
 */
function drawPawn(
  context: CanvasRenderingContext2D,
  options: DrawOptions,
  screenX: (tileX: number) => number,
  screenY: (tileY: number) => number,
): void {
  const { palette, camera, player, playerRadius, facing } = options;
  const cx = screenX(player[0]);
  const cy = screenY(player[1]);
  const radius = playerRadius * camera.scale;

  context.save();
  context.globalAlpha = 0.35;
  context.fillStyle = "#000";
  context.beginPath();
  context.ellipse(cx, cy + radius * 0.75, radius * 1.05, radius * 0.45, 0, 0, Math.PI * 2);
  context.fill();
  context.restore();

  // Body: a capsule, taller than wide, so facing reads without a face.
  context.fillStyle = palette.player;
  context.beginPath();
  context.ellipse(cx, cy - radius * 0.15, radius * 0.85, radius * 1.25, 0, 0, Math.PI * 2);
  context.fill();

  context.fillStyle = palette.playerEdge;
  context.beginPath();
  context.ellipse(cx, cy - radius * 1.15, radius * 0.62, radius * 0.62, 0, 0, Math.PI * 2);
  context.fill();

  // A nub in the facing direction: the only movement cue the pawn has.
  context.beginPath();
  context.ellipse(
    cx + Math.cos(facing) * radius * 0.9,
    cy - radius * 1.15 + Math.sin(facing) * radius * 0.45,
    radius * 0.2,
    radius * 0.2,
    0,
    0,
    Math.PI * 2,
  );
  context.fill();
}
