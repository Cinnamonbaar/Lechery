/**
 * Character creation, in four steps under a live doll.
 *
 * Taps re-draw the step, so the selected chip or swatch is always the one
 * shown; sliders update their own readout instead, because rebuilding a
 * slider mid-drag would drop the thumb out from under the player's finger.
 */
import { EYES, HAIR, ORIGINS, PRONOUNS, SKIN, STYLES, type Swatch } from "./content";
import { type Character, look, roll, save } from "./character";
import { H, W } from "./doll";
import { dollView } from "./dollview";
import { h } from "./h";

const STEPS = ["Origin", "Body", "Face", "Name"];
const BUILD = ["Slender", "Lithe", "Balanced", "Soft", "Curvy"];
const CUPS = ["Flat", "AA", "A", "B", "C", "D", "DD", "E", "F", "G", "H"];
const ENDOW = ["None", "Small", "Small", "Modest", "Modest", "Average", "Average", "Generous", "Large", "Large", "Very large"];

export function creation(c: Character, done: (c: Character) => void) {
  const doll = dollView(look(c));
  const plate = h("div", "plate");
  const panel = h("div", "panel controls");
  const tabs = h("nav", "steps");
  const back = h("button", { textContent: "Back" });
  const next = h("button", "primary");
  let step = 0;

  const changed = () => {
    save(c);
    doll.update(look(c));
    plate.replaceChildren(
      h("b", { textContent: c.name }),
      h("span", { textContent: `${ORIGINS[c.origin]!.name} · ${PRONOUNS[c.pronouns]}` }),
    );
  };

  const set = (patch: Partial<Character>) => { Object.assign(c, patch); changed(); paint(); };

  const label = (text: string, extra?: Node) => h("div", "label", h("span", { textContent: text }), extra ?? "");

  const slider = (text: string, key: "height" | "build" | "bust" | "endowment", min: number, max: number, stepSize: number, fmt: (v: number) => string) => {
    const out = h("em", { textContent: fmt(c[key]) });
    const input = h("input", { type: "range", min: String(min), max: String(max), step: String(stepSize), value: String(c[key]) });
    input.oninput = () => { c[key] = Number(input.value); out.textContent = fmt(c[key]); changed(); };
    return h("div", "field", label(text, out), input);
  };

  const swatches = (text: string, list: Swatch[], key: "skin" | "hair" | "eyes") =>
    h("div", "field", label(text, h("em", { textContent: list[c[key]]![0] })),
      h("div", "swatches", ...list.map(([name, hex], i) => {
        const b = h("button", { className: i === c[key] ? "swatch on" : "swatch", title: name, ariaLabel: name });
        b.style.background = hex;
        b.onclick = () => set({ [key]: i });
        return b;
      })));

  const chips = (text: string, list: string[], key: "style" | "pronouns") =>
    h("div", "field", label(text), h("div", "chips", ...list.map((name, i) => {
      const b = h("button", { className: i === c[key] ? "on" : "", textContent: name });
      b.onclick = () => set({ [key]: i });
      return b;
    })));

  const pages = [
    () => ORIGINS.map((o, i) => {
      const b = h("button", { className: i === c.origin ? "origin on" : "origin" },
        h("b", { textContent: o.name }), h("span", { textContent: o.line }), h("i", { textContent: "◆ " + o.gift }));
      b.onclick = () => set({ origin: i });
      return b;
    }),
    () => [
      slider("Height", "height", 145, 195, 1, (v) => `${v} cm`),
      slider("Build", "build", 0, 1, 0.01, (v) => BUILD[Math.round(v * 4)]!),
      slider("Bust", "bust", 0, 10, 1, (v) => CUPS[Math.round(v)]!),
      slider("Endowment", "endowment", 0, 10, 1, (v) => ENDOW[Math.round(v)]!),
      swatches("Skin", SKIN, "skin"),
    ],
    () => [chips("Hair", STYLES, "style"), swatches("Hair colour", HAIR, "hair"), swatches("Eyes", EYES, "eyes")],
    () => {
      const input = h("input", { type: "text", value: c.name, placeholder: "Your name", maxLength: 24, autocomplete: "off", spellcheck: false });
      input.oninput = () => { c.name = input.value.trim(); changed(); next.disabled = !c.name; };
      return [h("div", "field", label("Name"), input), chips("Pronouns", PRONOUNS, "pronouns"),
        h("p", "note", "Others will decide for themselves what they see. This is what you call yourself.")];
    },
  ];

  const paint = () => {
    tabs.replaceChildren(...STEPS.map((name, i) => {
      const b = h("button", { className: i === step ? "on" : "", textContent: name });
      b.onclick = () => { step = i; paint(); };
      return b;
    }));
    const top = panel.scrollTop;
    panel.replaceChildren(...pages[step]!());
    panel.scrollTop = top;
    back.style.visibility = step ? "visible" : "hidden";
    next.textContent = step === STEPS.length - 1 ? "Begin" : "Next";
    next.disabled = step === STEPS.length - 1 && !c.name;
  };

  back.onclick = () => { step--; panel.scrollTop = 0; paint(); };
  next.onclick = () => {
    if (step < STEPS.length - 1) { step++; panel.scrollTop = 0; paint(); }
    else done(c);
  };
  const dice = h("button", { className: "dice", textContent: "⚄", title: "Surprise me", ariaLabel: "Randomise" });
  dice.onclick = () => set(roll(c));

  // Whole *device* pixels per art pixel, so every pixel of the doll is the
  // same size -- and on a 3x phone screen that allows steps of a third.
  const stage = h("div", "panel stage", doll.el, plate, dice);
  new ResizeObserver(() => {
    const dpr = devicePixelRatio || 1;
    const scale = Math.max(1, Math.floor(Math.min(stage.clientHeight * 0.96 / H, stage.clientWidth / W) * dpr));
    doll.el.style.height = `${(H * scale) / dpr}px`;
  }).observe(stage);

  changed();
  paint();
  return h("div", "screen creation", tabs, stage, panel, h("footer", "", back, next));
}
