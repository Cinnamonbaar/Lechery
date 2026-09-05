/**
 * Named colours that carry their pixels with them.
 *
 * Hair and eye colour are read by prose ("ash blonde") and by the paperdoll
 * (an RGB triple). Keeping both on one object means the two can never disagree
 * -- the alternative is a colour name table in the model and a second colour
 * table in the renderer, drifting apart.
 */

export interface Colour {
  readonly name: string;
  readonly rgb: readonly [number, number, number];
  /** Groups colours for prose that wants the family, not the shade. */
  readonly family: string;
}

const colour = (
  name: string,
  rgb: [number, number, number],
  family: string,
): Colour => ({ name, rgb, family });

export const HAIR_COLOURS: readonly Colour[] = [
  colour("black", [28, 26, 30], "dark"),
  colour("raven", [40, 38, 52], "dark"),
  colour("dark brown", [58, 42, 32], "brown"),
  colour("chestnut", [96, 60, 38], "brown"),
  colour("auburn", [124, 58, 34], "red"),
  colour("copper", [168, 84, 38], "red"),
  colour("ginger", [196, 112, 52], "red"),
  colour("ash blonde", [188, 172, 140], "blonde"),
  colour("golden blonde", [216, 182, 104], "blonde"),
  colour("platinum", [226, 220, 206], "pale"),
  colour("white", [238, 236, 234], "pale"),
  colour("silver", [176, 178, 186], "pale"),
];

export const EYE_COLOURS: readonly Colour[] = [
  colour("dark brown", [58, 40, 28], "brown"),
  colour("hazel", [122, 96, 46], "brown"),
  colour("amber", [176, 124, 42], "warm"),
  colour("green", [78, 118, 74], "cool"),
  colour("grey", [132, 136, 142], "cool"),
  colour("blue", [86, 122, 160], "cool"),
  colour("pale blue", [150, 182, 206], "cool"),
  colour("violet", [122, 96, 158], "uncanny"),
  colour("red", [156, 62, 58], "uncanny"),
  colour("gold", [206, 172, 76], "uncanny"),
];

const BY_NAME = new Map<string, Colour>();
for (const item of [...HAIR_COLOURS, ...EYE_COLOURS]) {
  // Hair and eyes share some names; first registration wins, which is the
  // hair one. Callers that care pass a Colour rather than a name.
  if (!BY_NAME.has(item.name)) BY_NAME.set(item.name, item);
}

export function findColour(name: string): Colour {
  const found = BY_NAME.get(name);
  if (!found) throw new Error(`Unknown colour ${JSON.stringify(name)}`);
  return found;
}

/** Look a colour up within one palette, so "dark brown" eyes stay eyes. */
export function fromPalette(palette: readonly Colour[], name: string): Colour {
  const found = palette.find((item) => item.name === name);
  if (!found) throw new Error(`Unknown colour ${JSON.stringify(name)}`);
  return found;
}

export function rgbCss(colour: Colour): string {
  const [r, g, b] = colour.rgb;
  return `rgb(${r}, ${g}, ${b})`;
}
