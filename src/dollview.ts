/**
 * The doll on screen: a small canvas scaled up by whole pixels, so the art
 * stays crisp, and a little life on top of it.
 *
 * Sizes spring toward their targets instead of snapping, with a touch of
 * overshoot, so dragging a slider feels like the body responding rather than
 * a picture swapping. She also breathes and blinks: a doll that never moves
 * reads as a mannequin.
 */
import { draw, H, W, type Look } from "./doll";
import { h } from "./h";

const SPRUNG = ["height", "build", "bust", "endowment"] as const;

export function dollView(initial: Look) {
  const canvas = h("canvas", { width: W, height: H, className: "doll" });
  const ctx = canvas.getContext("2d")!;
  const image = ctx.createImageData(W, H);

  let target = { ...initial };
  const shown = { ...initial };
  const speed: Record<string, number> = {};
  let blink = false, breath = 0, frame = 0, last = 0;

  const render = () => {
    draw(shown, { blink, breath }, image.data);
    ctx.putImageData(image, 0, 0);
  };

  const step = (now: number) => {
    const dt = Math.min(0.05, (now - (last || now)) / 1000);
    last = now;
    let moving = false;
    for (const key of SPRUNG) {
      const gap = target[key] - shown[key];
      // A spring a little under critical damping: it overshoots once, then
      // settles -- enough to feel alive, not enough to wobble.
      speed[key] = ((speed[key] ?? 0) + gap * 140 * dt) * Math.exp(-15 * dt);
      shown[key] += speed[key]! * dt;
      if (Math.abs(gap) > 0.01 || Math.abs(speed[key]!) > 0.01) moving = true;
      else shown[key] = target[key];
    }
    render();
    frame = moving ? requestAnimationFrame(step) : 0;
    if (!moving) last = 0;
  };

  const wake = () => { if (!frame) frame = requestAnimationFrame(step); };

  // Timers stop for good once the doll has been shown and taken away, so a
  // screen that is left behind does not keep animating in the dark.
  let shownOnce = false;
  const every = (act: () => void, delay: () => number) => {
    const run = () => {
      if (canvas.isConnected) shownOnce = true;
      else if (shownOnce) return;
      act();
      setTimeout(run, delay());
    };
    setTimeout(run, delay());
  };
  // Blink every few seconds, for a seventh of a second.
  every(() => {
    blink = true; render();
    setTimeout(() => { blink = false; render(); }, 140);
  }, () => 2600 + Math.random() * 2800);
  every(() => { breath = 1 - breath; render(); }, () => (breath ? 1300 : 1700));

  render();
  return {
    el: canvas,
    update(look: Look) {
      target = { ...look };
      // Colours and style have nothing to spring through; they change now.
      Object.assign(shown, { skin: look.skin, hair: look.hair, eyes: look.eyes, style: look.style });
      wake();
    },
  };
}
