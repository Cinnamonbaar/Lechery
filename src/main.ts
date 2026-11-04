import "./style.css";
import { load } from "./character";
import { ARRIVAL, INTRO } from "./content";
import { creation } from "./creation";
import { h } from "./h";
import { story } from "./story";

const app = document.getElementById("app")!;

// One dot, cast as a hundred shadows across the screen: a starfield for the
// cost of a line, scattered fresh each visit so it never looks tiled.
const r = (n: number) => Math.round(Math.random() * n);
document.body.style.setProperty("--sky", Array.from({ length: 110 }, (_, i) =>
  `${r(100)}vw ${r(100)}vh 0 ${i % 9 ? -0.4 : 0.2}px ${i % 7 ? "#fff8" : "#f6e9c4"}`).join());
const show = (screen: HTMLElement) => app.replaceChildren(screen);

function title() {
  const screen = h("div", "screen title", h("div", "stars"),
    h("h1", { textContent: "Lechery" }),
    h("div", "rule", h("span", { textContent: "Tap to begin" })));
  screen.onclick = () => show(story(INTRO, {}, make));
  show(screen);
}

function make() {
  show(creation(load(), (c) => show(story(ARRIVAL, { name: c.name }, end))));
}

function end() {
  const again = h("button", { className: "primary", textContent: "Begin again" });
  again.onclick = title;
  show(h("div", "screen end", h("div", "stars"),
    h("div", "rule", h("span", { textContent: "End of the prologue" })),
    h("p", { textContent: "Thank you for playing this far. More is coming." }), again));
}

title();
