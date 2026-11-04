/** Everything the player reads or picks from. Data, not code. */

export type Swatch = [name: string, hex: string];

export const SKIN: Swatch[] = [
  ["porcelain", "#f7e0cc"], ["peach", "#f3d2b8"], ["fair", "#eabf9f"],
  ["honey", "#d9a47c"], ["bronze", "#c08560"], ["umber", "#8a5a3c"], ["ebony", "#5e3b28"],
];

export const HAIR: Swatch[] = [
  ["black", "#2b2433"], ["chestnut", "#6b4430"], ["auburn", "#a8402c"],
  ["honey blonde", "#d9c08a"], ["platinum", "#f2f0ea"], ["silver", "#b9bccb"],
  ["rose", "#e8b4c8"], ["lavender", "#b9a2e0"], ["teal", "#4fa3a5"], ["crimson", "#b8283c"],
];

export const EYES: Swatch[] = [
  ["brown", "#6b4a30"], ["amber", "#b8862f"], ["green", "#6aa06a"], ["blue", "#4f7bb8"],
  ["grey", "#8d93a3"], ["violet", "#9a5bb8"], ["red", "#c0473f"], ["gold", "#e0b84a"],
];

export const STYLES = ["Short", "Bob", "Long", "Ponytail", "Twintails"];

export const PRONOUNS = ["she/her", "he/him", "they/them"];

export interface Origin {
  name: string;
  line: string;
  gift: string;
}

export const ORIGINS: Origin[] = [
  { name: "The Student", line: "Two exams from a life you hadn't chosen yet.", gift: "Quick to learn" },
  { name: "The Nurse", line: "Twelve-hour shifts, and a very steady hand.", gift: "Knows the body" },
  { name: "The Athlete", line: "Trained for a sport that doesn't exist here.", gift: "Hard to tire" },
  { name: "The Office Worker", line: "Fourteen years at a desk nobody will miss.", gift: "Reads people" },
  { name: "The Shut-in", line: "You know how these stories go. You've read hundreds.", gift: "Knows the genre" },
];

/** A line of the script. A bare string is narration. */
export type Line = string | [speaker: string, text: string];

const VOICE = "A voice";

export const INTRO: Line[] = [
  "The last thing you remember is ordinary.",
  "A weekday. A familiar street. Light that belonged to somewhere you knew.",
  "Then it isn't.",
  "There is no ground beneath you. There is no falling, either — only a long, patient dark, and the feeling of being looked at.",
  [VOICE, "Ah. Another one, pulled loose."],
  [VOICE, "Don't be frightened. The crossing takes things from people. Names. Faces. The shape they were."],
  [VOICE, "So before you go any further, you'll have to remember yourself."],
  [VOICE, "Tell me. Who were you?"],
];

/** After creation. `{name}` is filled in. */
export const ARRIVAL: Line[] = [
  [VOICE, "{name}. Yes."],
  [VOICE, "I'll hold you to that. The other side has a way of changing people."],
  "Light, all at once — and grass, and wind, and a sky the wrong colour for any hour you remember.",
];
