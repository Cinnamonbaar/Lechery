/**
 * Stats and skills: what a character can do, as opposed to what they are.
 *
 * Kept apart from traits deliberately. Traits are the body and who lives in
 * it; these are capability. A transformation changes traits and should not
 * silently make you better at arguing -- when a change should touch both, the
 * content says so explicitly.
 *
 * Stats are few and broad; skills are many and narrow. That split is what
 * keeps a skill list growable without every new skill needing a stat to hang
 * off, and what keeps stat checks meaningful when there are eighty skills.
 */

/** The five broad capabilities. Checked when no skill fits. */
export const Stat = {
  VIGOUR: "vigour", // bodily strength and endurance
  GRACE: "grace", // speed, balance, dexterity
  WITS: "wits", // reasoning, memory, quickness of thought
  PRESENCE: "presence", // charisma, bearing, how much room you take up
  RESOLVE: "resolve", // will, composure, the ability to keep going
} as const;

export type Stat = (typeof Stat)[keyof typeof Stat];

export const ALL_STATS: readonly Stat[] = Object.values(Stat);

export function statLabel(stat: Stat): string {
  return stat.charAt(0).toUpperCase() + stat.slice(1);
}

/** Where an ordinary person sits, and the range a character can occupy. */
export const STAT_DEFAULT = 3;
export const STAT_MIN = 1;
export const STAT_MAX = 10;

/** Points a player distributes during creation, on top of the default. */
export const CREATION_POINTS = 4;

const STAT_BANDS: readonly [number, string][] = [
  [2, "poor"],
  [4, "ordinary"],
  [6, "capable"],
  [8, "exceptional"],
  [99, "peerless"],
];

export function statBand(value: number): string {
  for (const [upper, label] of STAT_BANDS) {
    if (value <= upper) return label;
  }
  return STAT_BANDS[STAT_BANDS.length - 1]![1];
}

/** A character's five stats. */
export class StatBlock {
  private values = new Map<Stat, number>();

  constructor(values: Partial<Record<Stat, number>> = {}) {
    for (const stat of ALL_STATS) {
      this.values.set(stat, values[stat] ?? STAT_DEFAULT);
    }
  }

  get(stat: Stat): number {
    return this.values.get(stat) ?? STAT_DEFAULT;
  }

  set(stat: Stat, value: number): number {
    const clamped = Math.max(STAT_MIN, Math.min(STAT_MAX, Math.trunc(value)));
    this.values.set(stat, clamped);
    return clamped;
  }

  adjust(stat: Stat, delta: number): number {
    return this.set(stat, this.get(stat) + delta);
  }

  label(stat: Stat): string {
    return statBand(this.get(stat));
  }

  /** Points above the baseline, for creation to budget against. */
  get spent(): number {
    return ALL_STATS.reduce((total, stat) => total + this.get(stat) - STAT_DEFAULT, 0);
  }

  copy(): StatBlock {
    return new StatBlock(Object.fromEntries(this.values) as Partial<Record<Stat, number>>);
  }

  entries(): [Stat, number][] {
    return ALL_STATS.map((stat) => [stat, this.get(stat)]);
  }
}

/** A named, narrow competence. */
export interface SkillDef {
  readonly key: string;
  readonly label: string;
  readonly stat: Stat;
  readonly description: string;
}

const skill = (key: string, label: string, stat: Stat, description: string): SkillDef => ({
  key,
  label,
  stat,
  description,
});

/**
 * The starting list. Narrow on purpose -- skills are cheap to add and
 * expensive to remove once content checks them by name.
 */
export const SKILLS: Record<string, SkillDef> = Object.fromEntries(
  [
    skill("athletics", "Athletics", Stat.VIGOUR, "Running, climbing, hauling."),
    skill("brawling", "Brawling", Stat.VIGOUR, "Violence without a plan."),
    skill("fencing", "Fencing", Stat.GRACE, "Violence with one."),
    skill("stealth", "Stealth", Stat.GRACE, "Not being where attention is."),
    skill("sleight", "Sleight", Stat.GRACE, "Hands doing what they should not."),
    skill("lore", "Lore", Stat.WITS, "What is written down, and where."),
    skill("arcana", "Arcana", Stat.WITS, "The rules under the rules."),
    skill("medicine", "Medicine", Stat.WITS, "Keeping a body working."),
    skill("craft", "Craft", Stat.WITS, "Making and mending."),
    skill("survival", "Survival", Stat.WITS, "Weather, tracks, water, dark."),
    skill("persuasion", "Persuasion", Stat.PRESENCE, "Being agreed with."),
    skill("insight", "Insight", Stat.PRESENCE, "Reading what is not said."),
    skill("performance", "Performance", Stat.PRESENCE, "Being watched on purpose."),
    skill("composure", "Composure", Stat.RESOLVE, "Not showing it."),
    skill("endurance", "Endurance", Stat.RESOLVE, "Outlasting the problem."),
  ].map((definition) => [definition.key, definition]),
);

export const SKILL_MAX = 5;

export const SKILL_RANKS = [
  "untrained",
  "novice",
  "competent",
  "practised",
  "expert",
  "masterful",
] as const;

export function skillRank(rank: number): string {
  return SKILL_RANKS[Math.max(0, Math.min(SKILL_MAX, rank))]!;
}

/**
 * Skill ranks, defaulting to untrained.
 *
 * Stored sparsely: a character has a rank in a skill or they do not, and an
 * absent skill is untrained rather than missing. That keeps the list growable
 * without every save file needing every skill written into it.
 */
export class Skills {
  readonly ranks = new Map<string, number>();

  constructor(ranks: Record<string, number> = {}) {
    for (const [key, rank] of Object.entries(ranks)) this.set(key, rank);
  }

  get(key: string): number {
    if (!SKILLS[key]) throw new Error(`Unknown skill ${JSON.stringify(key)}`);
    return this.ranks.get(key) ?? 0;
  }

  set(key: string, rank: number): number {
    if (!SKILLS[key]) throw new Error(`Unknown skill ${JSON.stringify(key)}`);
    const clamped = Math.max(0, Math.min(SKILL_MAX, Math.trunc(rank)));
    if (clamped) this.ranks.set(key, clamped);
    else this.ranks.delete(key);
    return clamped;
  }

  adjust(key: string, delta: number): number {
    return this.set(key, this.get(key) + delta);
  }

  /** Skills the character actually has, best first. */
  trained(): [SkillDef, number][] {
    return [...this.ranks.entries()]
      .filter(([, rank]) => rank > 0)
      .map(([key, rank]) => [SKILLS[key]!, rank] as [SkillDef, number])
      .sort((a, b) => b[1] - a[1] || a[0].label.localeCompare(b[0].label));
  }

  label(key: string): string {
    return skillRank(this.get(key));
  }

  copy(): Skills {
    return new Skills(Object.fromEntries(this.ranks));
  }
}
