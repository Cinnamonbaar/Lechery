/**
 * Who the character is, as opposed to what body they are in.
 *
 * These are kept apart deliberately. In a game about bodies changing, tying
 * gender to a body configuration means every transformation silently rewrites
 * who the character is -- grow a chest and the game starts calling you "she"
 * without asking. Identity moves when the story moves it; the body moves when
 * the body moves.
 */

export interface Pronouns {
  readonly subject: string; // she
  readonly object: string; // her
  readonly possessive: string; // her
  readonly possessiveNoun: string; // hers
  readonly reflexive: string; // herself
  /** Whether the pronoun takes a plural verb ("they are" vs "she is"). */
  readonly plural: boolean;
}

const pronouns = (
  subject: string,
  object: string,
  possessive: string,
  possessiveNoun: string,
  reflexive: string,
  plural = false,
): Pronouns => ({ subject, object, possessive, possessiveNoun, reflexive, plural });

export const SHE = pronouns("she", "her", "her", "hers", "herself");
export const HE = pronouns("he", "him", "his", "his", "himself");
export const THEY = pronouns("they", "them", "their", "theirs", "themselves", true);
export const IT = pronouns("it", "it", "its", "its", "itself");

export const PRONOUN_SETS: Record<string, Pronouns> = {
  she: SHE,
  he: HE,
  they: THEY,
  it: IT,
};

/** Pick the verb form a pronoun needs: `verb(p, "is", "are")`. */
export function verb(p: Pronouns, singular: string, plural: string): string {
  return p.plural ? plural : singular;
}

export function pronounLabel(p: Pronouns): string {
  return `${p.subject}/${p.object}`;
}

/**
 * A gender identity, with the pronouns that go with it.
 *
 * Free-form rather than an enum: this is a label the character carries, and
 * the set of them is content, not code. The defaults below are a starting
 * list, not a closed one.
 */
export interface Gender {
  readonly label: string;
  readonly pronouns: Pronouns;
}

export const WOMAN: Gender = { label: "woman", pronouns: SHE };
export const MAN: Gender = { label: "man", pronouns: HE };
export const NONBINARY: Gender = { label: "nonbinary", pronouns: THEY };

export const GENDERS: Record<string, Gender> = {
  woman: WOMAN,
  man: MAN,
  nonbinary: NONBINARY,
};
