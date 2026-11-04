/**
 * Lines of script, shown one at a time in a dialogue box.
 *
 * Text types itself out, pausing a beat at punctuation so prose reads at the
 * pace it was written. A tap finishes the line if it is still typing and
 * moves on if it isn't -- the one control a phone needs.
 */
import type { Line } from "./content";
import { h } from "./h";

const PAUSE: Record<string, number> = { ",": 140, ".": 320, "?": 320, "!": 320, "—": 260 };

export function story(lines: Line[], fill: Record<string, string>, done: () => void) {
  const speaker = h("div", "speaker");
  const text = h("p", "line");
  const hint = h("div", "hint", "◆");
  const box = h("div", "box", speaker, text, hint);
  const skip = h("button", { className: "skip", textContent: "Skip ›" });
  const root = h("div", "screen story", h("div", "stars"), box, skip);

  let index = -1, timer = 0, full = "", typing = false;

  const finish = () => {
    clearTimeout(timer);
    text.textContent = full;
    typing = false;
    hint.hidden = false;
  };

  const next = () => {
    if (typing) return finish();
    if (++index >= lines.length) return done();
    const line = lines[index]!;
    const [who, said] = typeof line === "string" ? ["", line] : line;
    full = said.replace(/\{(\w+)\}/g, (_, key: string) => fill[key] ?? "");
    speaker.textContent = who;
    speaker.hidden = !who;
    box.classList.toggle("spoken", !!who);
    text.textContent = "";
    hint.hidden = true;
    typing = true;
    let n = 0;
    const type = () => {
      text.textContent = full.slice(0, ++n);
      if (n >= full.length) return finish();
      timer = window.setTimeout(type, PAUSE[full[n - 1]!] ?? 24);
    };
    type();
  };

  root.onclick = next;
  skip.onclick = (event) => { event.stopPropagation(); clearTimeout(timer); done(); };
  next();
  return root;
}
