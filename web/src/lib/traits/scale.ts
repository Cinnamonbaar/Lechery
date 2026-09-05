/**
 * Numbers that also know what they are called.
 *
 * Every physical trait is a number a transformation can do arithmetic on, and
 * a word prose and the paperdoll can read. Without this layer every piece of
 * content invents its own thresholds, and they drift: one scene calls 150cm
 * "short" and the next calls it "tiny".
 *
 * A Scale owns that mapping once.
 */

/** One named stretch of a scale. `upper` is exclusive. */
export interface Band {
  readonly label: string;
  readonly upper: number;
  /** Optional adjective for prose that needs one ("a tall woman"). */
  readonly adjective?: string;
}

export class Scale {
  constructor(
    readonly name: string,
    readonly minimum: number,
    readonly maximum: number,
    readonly bands: readonly Band[],
    readonly unit = "",
  ) {}

  clamp(value: number): number {
    return Math.max(this.minimum, Math.min(this.maximum, value));
  }

  /** The band a value falls in. The last band catches everything above. */
  bandFor(value: number): Band {
    for (const band of this.bands) {
      if (value < band.upper) return band;
    }
    return this.bands[this.bands.length - 1]!;
  }

  label(value: number): string {
    return this.bandFor(value).label;
  }

  adjective(value: number): string {
    const band = this.bandFor(value);
    return band.adjective || band.label;
  }

  /**
   * Which band, as a number. Comparing bands is how content asks whether a
   * change was a step up or down without knowing the labels.
   */
  index(value: number): number {
    return this.bands.indexOf(this.bandFor(value));
  }

  format(value: number): string {
    if (!this.unit) return this.label(value);
    return `${Math.round(value)}${this.unit} (${this.label(value)})`;
  }
}

/**
 * Adults only. The floor is enforced by the trait model, not just described
 * here, so no code path can produce a character below it.
 */
export const MINIMUM_AGE = 18;

export const AGE = new Scale("age", MINIMUM_AGE, 90, [
  { label: "young adult", upper: 26 },
  { label: "adult", upper: 40 },
  { label: "middle-aged", upper: 60 },
  { label: "old", upper: 999 },
]);

export const HEIGHT = new Scale(
  "height",
  120,
  230,
  [
    { label: "very short", upper: 150, adjective: "diminutive" },
    { label: "short", upper: 163 },
    { label: "average height", upper: 178, adjective: "average" },
    { label: "tall", upper: 193 },
    { label: "towering", upper: 999, adjective: "immense" },
  ],
  "cm",
);

/**
 * Chest development, as a cup index: 0 is flat, rising from there. Kept as a
 * number rather than a letter so transformations can step it up and down.
 */
export const BUST = new Scale("bust", 0, 12, [
  { label: "flat", upper: 1 },
  { label: "small", upper: 3 },
  { label: "modest", upper: 5 },
  { label: "full", upper: 7 },
  { label: "large", upper: 9 },
  { label: "very large", upper: 999 },
]);

/**
 * Cup letters by bust index, so the panel can show "C cup" rather than a
 * vague word. Index 0 is flat; the list runs as far as the scale does.
 */
export const CUP_LETTERS = [
  "AA", "A", "B", "C", "D", "DD", "E", "F", "G", "H", "I", "J", "K",
] as const;

/** A bra-cup label for a bust index: "flat", "B cup", ... */
export function cupSize(value: number): string {
  const index = Math.round(value);
  if (index <= 0) return "flat";
  const letter = CUP_LETTERS[Math.min(index, CUP_LETTERS.length - 1)]!;
  return `${letter} cup`;
}

/**
 * Length in centimetres; zero means absent, which is a real state in a game
 * about bodies changing, not a missing value.
 */
export const PHALLUS = new Scale(
  "phallus",
  0,
  45,
  [
    { label: "absent", upper: 1 },
    { label: "small", upper: 12 },
    { label: "average", upper: 18 },
    { label: "large", upper: 25 },
    { label: "very large", upper: 999 },
  ],
  "cm",
);

export const SCALES: Record<string, Scale> = Object.fromEntries(
  [AGE, HEIGHT, BUST, PHALLUS].map((scale) => [scale.name, scale]),
);

export function scaleFor(name: string): Scale | undefined {
  return SCALES[name];
}
