import { describe, expect, it } from "vitest";
import {
  BUST,
  Character,
  CLOTHED,
  cupSize,
  defaultCharacter,
  GENDERS,
  HE,
  HEIGHT,
  MINIMUM_AGE,
  NUDE,
  SHE,
  THEY,
  Traits,
} from "./index";

const character = () => defaultCharacter("Test");

describe("scales", () => {
  it("gives a trait both a number and a word", () => {
    const c = character();
    c.set("height", 172);
    expect(c.traits.get("height")).toBe(172);
    expect(c.traits.label("height")).toBe("average height");
    expect(c.traits.describe("height")).toBe("172cm (average height)");
  });

  it.each([
    [140, "very short"],
    [155, "short"],
    [170, "average height"],
    [185, "tall"],
    [200, "towering"],
  ])("bands height %i as %s", (height, label) => {
    expect(HEIGHT.label(height)).toBe(label);
  });

  it("clamps values to the scale", () => {
    const c = character();
    c.set("height", 9999);
    expect(c.traits.get("height")).toBe(HEIGHT.maximum);
    c.set("height", -50);
    expect(c.traits.get("height")).toBe(HEIGHT.minimum);
  });

  it("lets content compare bands without knowing labels", () => {
    expect(HEIGHT.index(200)).toBeGreaterThan(HEIGHT.index(140));
  });

  it.each([
    [0, "flat"],
    [1, "A cup"],
    [3, "C cup"],
    [5, "DD cup"],
    [12, "K cup"],
  ])("labels bust %i as %s", (index, label) => {
    expect(cupSize(index)).toBe(label);
  });
});

describe("identity is not the body", () => {
  it("does not change who the character is when a bust grows", () => {
    const c = character();
    const before = c.gender;
    c.set("bust", 6);
    expect(c.gender).toBe(before);
    expect(c.pronouns).toBe(before.pronouns);
  });

  it("follows gender unless overridden, and keeps a chosen set", () => {
    const c = character();
    c.gender = GENDERS.woman!;
    expect(c.pronouns).toBe(SHE);
    c.pronounOverride = THEY;
    expect(c.pronouns).toBe(THEY);
    c.gender = GENDERS.man!;
    expect(c.pronouns).toBe(THEY);
  });
});

describe("the age floor", () => {
  it("rejects rather than silently correcting", () => {
    const c = character();
    expect(() => c.set("age", 16)).toThrow();
    expect(c.traits.get("age")).toBeGreaterThanOrEqual(MINIMUM_AGE);
  });

  it("applies at construction too", () => {
    expect(() => new Traits({ name: "x", age: 12 })).toThrow();
  });
});

describe("changes as events", () => {
  it("reports what moved and which way", () => {
    const c = character();
    const change = c.adjust("height", 20)!;
    expect(change.key).toBe("height");
    expect(change.before).toBe(170);
    expect(change.after).toBe(190);
    expect(change.direction).toBe(1);
  });

  it("knows whether it crossed a band", () => {
    const c = character();
    expect(c.adjust("height", 2)!.crossedBand).toBe(false);
    expect(c.adjust("height", 20)!.crossedBand).toBe(true);
  });

  it("is not a change when the value does not move", () => {
    const c = character();
    expect(c.set("height", c.traits.get("height"))).toBeNull();
    expect(c.traits.history).toEqual([]);
  });

  it("does not record building a character as a transformation", () => {
    expect(defaultCharacter().traits.history).toEqual([]);
  });

  it("rejects unknown traits and non-numeric adjustment", () => {
    const c = character();
    expect(() => c.set("wingspan" as never, 3)).toThrow();
    expect(() => c.adjust("hair_colour", 1)).toThrow();
  });
});

describe("absent parts are a real state", () => {
  it("treats zero as absent, not missing", () => {
    const c = character();
    expect(c.hasPhallus).toBe(false);
    c.set("phallus", 14);
    expect(c.hasPhallus).toBe(true);
    c.set("phallus", 0);
    expect(c.hasPhallus).toBe(false);
  });
});

describe("perception", () => {
  it("can read a body against the character's identity", () => {
    const c = character();
    c.gender = GENDERS.man!;
    c.set("bust", 8);

    const read = c.presentation(CLOTHED);
    expect(read.label).toBe("feminine");
    expect(read.pronouns(false)).toBe(SHE);
    expect(c.pronouns).not.toBe(SHE);
    expect(c.readMatchesIdentity).toBe(false);
  });

  it("hides the signals clothing should hide", () => {
    const bare = defaultCharacter();
    bare.set("phallus", 16);
    const grown = defaultCharacter();
    grown.set("phallus", 40);

    // Dressed, the size of it cannot matter: none of it is visible.
    expect(bare.presentation(CLOTHED).score).toBe(grown.presentation(CLOTHED).score);
    expect(bare.presentation(CLOTHED).score).toBe(
      defaultCharacter().presentation(CLOTHED).score,
    );

    // Marked invisible rather than weighted to zero, so a scene that
    // undresses the character needs no new plumbing.
    const hidden = bare
      .presentation(CLOTHED)
      .signals.filter((s) => !s.visible)
      .map((s) => s.key);
    expect(hidden).toContain("phallus");

    expect(bare.presentation(NUDE).score).toBeLessThan(bare.presentation(CLOTHED).score);
  });

  it("still reads a covered chest somewhat", () => {
    const c = character();
    c.set("bust", 8);
    expect(c.presentation(CLOTHED).score).toBeGreaterThan(0);
  });

  it("lets knowing someone beat looking at them", () => {
    const c = character();
    c.gender = GENDERS.man!;
    c.set("bust", 9);

    const stranger = c.perceivedBy(CLOTHED);
    const friend = c.perceivedBy(CLOTHED, { knowsIdentity: true });

    expect(stranger.pronouns(false)).toBe(SHE);
    expect(friend.pronouns()).toBe(c.pronouns);
    expect(friend.fromKnowledge).toBe(true);
    expect(stranger.fromKnowledge).toBe(false);
  });

  it("hedges or guesses when unsure", () => {
    const read = character().presentation();
    expect(read.ambiguous).toBe(true);
    expect(read.pronouns(true)).toBe(THEY);
    expect([SHE, HE]).toContain(read.pronouns(false));
  });

  it("lets height nudge a read but never decide one", () => {
    const c = character();
    c.set("height", HEIGHT.minimum);
    expect(c.presentation().ambiguous).toBe(true);
    c.set("height", HEIGHT.maximum);
    expect(c.presentation().ambiguous).toBe(true);
  });

  it("lets clothing push the read without being a body trait", () => {
    const c = character();
    const before = c.presentation().score;
    c.presentationBias = 0.5;
    expect(c.presentation().score).toBeGreaterThan(before);
    expect(c.traits.history).toEqual([]);
  });

  it("keeps scores in range at the extremes", () => {
    const c = character();
    c.set("bust", 12);
    c.presentationBias = 1;
    expect(Math.abs(c.presentation(NUDE).score)).toBeLessThanOrEqual(1);

    c.set("bust", 0);
    c.set("phallus", 40);
    c.presentationBias = -1;
    expect(Math.abs(c.presentation(NUDE).score)).toBeLessThanOrEqual(1);
  });
});
