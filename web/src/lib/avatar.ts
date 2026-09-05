/**
 * Driving the dynamic-avatar-drawer from the game's traits.
 *
 * The library (vendored unmodified under public/vendor, LGPL v3) draws a stack
 * of canvases into a DOM element. This module owns two things and nothing
 * else: loading it, and the mapping from our traits to its dimensions. Its
 * dimensions are in its own units and ranges; ours are in centimetres and cup
 * sizes. Everything that translates between the two lives here, so neither
 * model has to know about the other.
 */

import { BUST, PHALLUS, type Scale } from "./traits/scale";
import type { Character } from "./traits/character";
import { NUDE } from "./traits/perception";

/** The library's own canvas size. The view scales this to fit its box. */
export const NATIVE_SIZE = [700, 1200] as const;

/**
 * `fem` is the library's core stat: "how overall feminine their appearance
 * is; influences a lot of dimensions". Range 0-11, average 5.
 */
const FEM_LOW = 0;
const FEM_HIGH = 11;

const SCRIPT_URL = "vendor/dynamic-avatar-drawer/da.js";

export interface AvatarPayload {
  readonly name: string;
  readonly fem: number;
  readonly basedim: Record<string, number>;
}

// -- the mapping ----------------------------------------------------------

/** Put a trait on one of the library's ranges, proportionally. */
function scaled(value: number, scale: Scale, low: number, high: number): number {
  const span = scale.maximum - scale.minimum;
  if (span <= 0) return low;
  const fraction = (value - scale.minimum) / span;
  return low + Math.max(0, Math.min(1, fraction)) * (high - low);
}

/**
 * The library's `fem` stat, from how the character reads.
 *
 * A happy coincidence: their core stat and our perception model are the same
 * idea. Ours runs -1 to +1 and already accounts for build, so it maps straight
 * onto their 0-11 without inventing anything. Read undressed, because this is
 * the body the drawing shows.
 */
export function femininity(character: Character): number {
  const score = character.presentation(NUDE).score; // -1 .. +1
  return FEM_LOW + ((score + 1) / 2) * (FEM_HIGH - FEM_LOW);
}

/** RGB 0-255 to hue (0-360), saturation and lightness (0-100). */
export function rgbToHsl(
  rgb: readonly [number, number, number],
): [number, number, number] {
  const [r, g, b] = [rgb[0] / 255, rgb[1] / 255, rgb[2] / 255];
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const lightness = (max + min) / 2;
  const delta = max - min;
  if (delta === 0) return [0, 0, lightness * 100];

  const saturation = delta / (1 - Math.abs(2 * lightness - 1));
  let hue: number;
  if (max === r) hue = ((g - b) / delta) % 6;
  else if (max === g) hue = (b - r) / delta + 2;
  else hue = (r - g) / delta + 4;
  hue *= 60;
  if (hue < 0) hue += 360;
  return [hue, saturation * 100, lightness * 100];
}

/**
 * Every library dimension we currently have an opinion about.
 *
 * Deliberately partial. The library has thirty-odd dimensions and we have six
 * traits; anything not named here keeps the library's own default, which is a
 * sensible average rather than a zero.
 */
export function dimensions(character: Character): Record<string, number> {
  const traits = character.traits;
  const [hue, saturation, lightness] = rgbToHsl(traits.get("hair_colour").rgb);
  return {
    // Their height is in centimetres too, so this one is a straight copy.
    height: traits.maybe("height", 170),
    // Cup index onto their 0-100ish scale.
    breastSize: scaled(traits.maybe("bust", 0), BUST, 0, 100),
    penisSize: scaled(traits.maybe("phallus", 0), PHALLUS, 0, 100),
    hairHue: hue,
    hairSaturation: saturation,
    hairLightness: lightness,
  };
}

/** What the library needs to build a player. */
export function payload(character: Character): AvatarPayload {
  return {
    name: character.name,
    fem: femininity(character),
    basedim: dimensions(character),
  };
}

/**
 * What the drawing depends on, as a comparable string.
 *
 * Compared rather than subscribed to: a trait changed by a path that forgot to
 * notify cannot leave a stale drawing.
 */
export function signature(character: Character): string {
  const data = payload(character);
  const dims = Object.entries(data.basedim)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}=${value.toFixed(3)}`);
  return [data.name, data.fem.toFixed(3), ...dims].join("|");
}

// -- loading the library --------------------------------------------------

interface DaLibrary {
  load(): Promise<unknown>;
  getCanvasGroup(id: string, size: { width: number; height: number }): HTMLElement;
  draw(group: HTMLElement, player: unknown, view: unknown): Promise<unknown>;
  Player: new (options: unknown) => unknown;
}

declare global {
  // eslint-disable-next-line no-var
  var da: DaLibrary | undefined;
}

let loading: Promise<DaLibrary> | null = null;

/**
 * Load and initialise the library, once per page.
 *
 * Injected rather than imported: it is a plain browser script that assigns a
 * global, and keeping it out of the bundle is also what keeps it replaceable,
 * which the LGPL requires of us.
 */
export function loadAvatarLibrary(): Promise<DaLibrary> {
  if (loading) return loading;
  loading = new Promise<DaLibrary>((resolve, reject) => {
    if (typeof document === "undefined") {
      reject(new Error("no document"));
      return;
    }
    if (globalThis.da) {
      resolve(globalThis.da);
      return;
    }
    const script = document.createElement("script");
    script.src = new URL(SCRIPT_URL, document.baseURI).toString();
    script.onload = () => {
      const library = globalThis.da;
      if (!library) {
        reject(new Error("da.js loaded but defined nothing"));
        return;
      }
      library.load().then(() => resolve(library), reject);
    };
    script.onerror = () => reject(new Error("da.js failed to load"));
    document.head.appendChild(script);
  });
  return loading;
}

/** The view options the game draws with; it prints its own name and stats. */
export const VIEW = {
  transparentBackground: true,
  printAdditionalInfo: false,
  printHeight: false,
  printVitals: false,
  renderShoeSideView: false,
  offsetX: 0,
  offsetY: 0,
} as const;

/**
 * One mounted avatar: a canvas group inside `host`, redrawn on demand.
 *
 * Draws are coalesced. A slider being dragged asks far faster than the library
 * can draw, and queueing every request would run the whole backlog after the
 * player stopped moving.
 */
export class AvatarView {
  private group: HTMLElement | null = null;
  private library: DaLibrary | null = null;
  private drawing = false;
  private again = false;
  private pending: AvatarPayload | null = null;
  private lastSignature: string | null = null;
  /** One line for what the library is doing, or why it is not drawing. */
  status = "loading";
  onStatus: ((status: string) => void) | null = null;

  constructor(private readonly host: HTMLElement) {}

  async mount(): Promise<void> {
    try {
      this.library = await loadAvatarLibrary();
    } catch (error) {
      this.setStatus(`unavailable: ${(error as Error).message}`);
      return;
    }
    // getCanvasGroup looks its holder up by id and reads its style without
    // checking -- its docstring claims it creates one, but it only creates
    // the canvases inside. Passing an id that does not exist throws on null.
    const holder = document.createElement("div");
    holder.id = `lechery-avatar-${Math.random().toString(36).slice(2)}`;
    this.host.appendChild(holder);
    this.group = this.library.getCanvasGroup(holder.id, {
      width: NATIVE_SIZE[0],
      height: NATIVE_SIZE[1],
    });
    this.setStatus("ready");
    if (this.pending) {
      const pending = this.pending;
      this.pending = null;
      this.draw(pending);
    }
  }

  /** Redraw for `character` if anything the drawing depends on moved. */
  update(character: Character, force = false): boolean {
    const current = signature(character);
    if (!force && current === this.lastSignature) return false;
    this.lastSignature = current;
    this.draw(payload(character));
    return true;
  }

  private draw(data: AvatarPayload): void {
    if (!this.library || !this.group) {
      this.pending = data;
      return;
    }
    if (this.drawing) {
      this.pending = data;
      this.again = true;
      return;
    }
    this.drawing = true;
    const player = new this.library.Player(data);
    this.library
      .draw(this.group, player, VIEW)
      .then(() => {
        this.drawing = false;
        if (this.again) {
          this.again = false;
          const next = this.pending;
          this.pending = null;
          if (next) this.draw(next);
        }
      })
      .catch((error: Error) => {
        this.drawing = false;
        this.setStatus(`draw failed: ${error.message}`);
      });
  }

  private setStatus(status: string): void {
    this.status = status;
    this.onStatus?.(status);
  }

  destroy(): void {
    this.group?.remove();
    this.group = null;
  }
}
