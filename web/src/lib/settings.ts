/**
 * Player settings, persisted in the browser.
 *
 * localStorage rather than a file: the web build is the primary target, and a
 * private window or a browser set to block site data must cost the player
 * their preferences at worst, never the game -- so every read and write is
 * guarded and failure falls back to defaults.
 */

export const LayoutMode = {
  /**
   * AUTO measures the window; the other two are the player's override, for
   * when the measurement disagrees with what they want -- a tablet user who
   * prefers the full three-pane view, or a desktop user who wants the world
   * to fill the window.
   */
  AUTO: "auto",
  WIDE: "wide",
  COMPACT: "compact",
} as const;

export type LayoutMode = (typeof LayoutMode)[keyof typeof LayoutMode];

const LAYOUT_MODES: readonly string[] = Object.values(LayoutMode);

export const STORAGE_KEY = "lechery:settings";

export interface SettingsData {
  layoutMode: LayoutMode;
  /**
   * Bars the player last had open, remembered per layout so switching between
   * them does not lose the arrangement.
   */
  wideLeftOpen: boolean;
  wideRightOpen: boolean;
  /**
   * Draw the on-screen movement stick even on a mouse-and-keyboard machine.
   * Null means "decide from the layout".
   */
  touchControls: boolean | null;
  /** Which palette theme.css should apply. */
  theme: "dark" | "light";
}

export const DEFAULTS: SettingsData = {
  layoutMode: LayoutMode.AUTO,
  wideLeftOpen: true,
  wideRightOpen: true,
  touchControls: null,
  theme: "dark",
};

type Store = Pick<Storage, "getItem" | "setItem">;

function defaultStore(): Store | null {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    // Some browsers throw on the accessor itself when site data is blocked.
    return null;
  }
}

export class Settings implements SettingsData {
  layoutMode: LayoutMode = DEFAULTS.layoutMode;
  wideLeftOpen = DEFAULTS.wideLeftOpen;
  wideRightOpen = DEFAULTS.wideRightOpen;
  touchControls: boolean | null = DEFAULTS.touchControls;
  theme: "dark" | "light" = DEFAULTS.theme;

  /** Called after any successful change, so the UI can react. */
  onChange: ((settings: Settings) => void) | null = null;

  constructor(private store: Store | null = defaultStore()) {}

  // -- persistence --------------------------------------------------------

  static load(store: Store | null = defaultStore()): Settings {
    const settings = new Settings(store);
    let raw: string | null = null;
    try {
      raw = store?.getItem(STORAGE_KEY) ?? null;
    } catch {
      raw = null;
    }
    if (!raw) return settings;
    try {
      settings.apply(JSON.parse(raw) as unknown);
    } catch {
      // A corrupt file is a reason to lose preferences, not to refuse to
      // launch.
    }
    return settings;
  }

  /** Merge a stored blob in, ignoring anything this version does not know. */
  apply(data: unknown): void {
    if (typeof data !== "object" || data === null) return;
    const source = data as Partial<Record<keyof SettingsData, unknown>>;

    if (
      typeof source.layoutMode === "string" &&
      LAYOUT_MODES.includes(source.layoutMode)
    ) {
      this.layoutMode = source.layoutMode as LayoutMode;
    }
    if (typeof source.wideLeftOpen === "boolean") {
      this.wideLeftOpen = source.wideLeftOpen;
    }
    if (typeof source.wideRightOpen === "boolean") {
      this.wideRightOpen = source.wideRightOpen;
    }
    if (
      typeof source.touchControls === "boolean" ||
      source.touchControls === null
    ) {
      this.touchControls = source.touchControls;
    }
    if (source.theme === "dark" || source.theme === "light") {
      this.theme = source.theme;
    }
  }

  toJSON(): SettingsData {
    return {
      layoutMode: this.layoutMode,
      wideLeftOpen: this.wideLeftOpen,
      wideRightOpen: this.wideRightOpen,
      touchControls: this.touchControls,
      theme: this.theme,
    };
  }

  /** Write settings. Returns whether it worked; never throws. */
  save(): boolean {
    try {
      this.store?.setItem(STORAGE_KEY, JSON.stringify(this.toJSON()));
      return this.store !== null;
    } catch {
      return false;
    }
  }

  /** Change one setting and persist, in one call. */
  set<K extends keyof SettingsData>(key: K, value: SettingsData[K]): void {
    const self = this as SettingsData;
    if (self[key] === value) return;
    self[key] = value;
    this.save();
    this.onChange?.(this);
  }
}
