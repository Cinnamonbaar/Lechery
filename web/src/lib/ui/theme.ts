/**
 * Reading the theme from CSS.
 *
 * The canvas cannot use a CSS custom property, but every other surface in the
 * game can -- so rather than keep a second palette in TypeScript, the renderer
 * reads the same custom properties the stylesheet defines. Retheme the game by
 * editing theme.css and the world view follows.
 */

export interface WorldPalette {
  floor: string;
  floorAlt: string;
  wall: string;
  wallTop: string;
  doorway: string;
  trap: string;
  portal: string;
  player: string;
  playerEdge: string;
  void: string;
}

const FALLBACK: WorldPalette = {
  floor: "#2b2a33",
  floorAlt: "#31303a",
  wall: "#17161d",
  wallTop: "#3d3b48",
  doorway: "#4a4356",
  trap: "#6d3a5d",
  portal: "#b58a4a",
  player: "#8d8a99",
  playerEdge: "#c9c5d6",
  void: "#0d0c11",
};

const PROPERTY: Record<keyof WorldPalette, string> = {
  floor: "--world-floor",
  floorAlt: "--world-floor-alt",
  wall: "--world-wall",
  wallTop: "--world-wall-top",
  doorway: "--world-doorway",
  trap: "--world-trap",
  portal: "--world-portal",
  player: "--world-player",
  playerEdge: "--world-player-edge",
  void: "--world-void",
};

/** Resolve the world palette from `element`'s computed style. */
export function worldPalette(element: Element | null = null): WorldPalette {
  if (typeof getComputedStyle !== "function") return { ...FALLBACK };
  const target = element ?? document.documentElement;
  const style = getComputedStyle(target);
  const palette = { ...FALLBACK };
  for (const key of Object.keys(PROPERTY) as (keyof WorldPalette)[]) {
    const value = style.getPropertyValue(PROPERTY[key]).trim();
    if (value) palette[key] = value;
  }
  return palette;
}
