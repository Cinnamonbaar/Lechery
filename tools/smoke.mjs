/*
 * Plays the game in a real browser at phone size and writes screenshots.
 * Every hard bug this project has had was invisible outside a browser.
 *
 *   npm run build && npx vite preview --port 4173 &
 *   npm run smoke -- [outdir]
 */
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { join } from "node:path";

const dir = process.argv[2] ?? "smoke-out";
mkdirSync(dir, { recursive: true });
const url = process.env.URL ?? "http://localhost:4173/";

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM ?? "/opt/pw-browsers/chromium" });
const errors = [];
const run = async (name, viewport) => {
  const page = await browser.newPage({ viewport, deviceScaleFactor: 3, hasTouch: true });
  page.on("pageerror", (e) => errors.push(`${name}: ${e.message}`));
  page.on("console", (m) => m.type() === "error" && errors.push(`${name}: ${m.text()}`));
  const shot = (n) => page.screenshot({ path: join(dir, `${name}-${n}.png`) });
  await page.goto(url);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.waitForTimeout(700);
  await shot("1-title");

  await page.click(".title");
  await page.waitForTimeout(2500);
  await shot("2-intro");
  for (let i = 0; i < 4; i++) { await page.click(".story"); await page.waitForTimeout(150); await page.click(".story"); }
  await page.waitForTimeout(3500);
  await shot("3-voice");
  await page.click(".skip");
  await page.waitForTimeout(800);
  await shot("4-origin");

  for (const [step, n] of [["Body", "5-body"], ["Face", "6-face"]]) {
    await page.click(`.steps >> text=${step}`);
    await page.waitForTimeout(900);
    await shot(n);
  }
  await page.click(".steps >> text=Body");
  await page.locator("input[type=range]").nth(2).fill("10");
  await page.locator("input[type=range]").nth(1).fill("1");
  await page.waitForTimeout(1200);
  await shot("7-body-max");

  await page.click(".steps >> text=Name");
  await page.fill("input[type=text]", "Aria");
  await page.waitForTimeout(400);
  await shot("8-name");
  await page.click("footer >> text=Begin");
  await page.waitForTimeout(2500);
  await shot("9-arrival");
  await page.click(".skip");
  await page.waitForTimeout(800);
  await shot("10-end");

  // The draft survives a reload.
  const saved = await page.evaluate(() => JSON.parse(localStorage.getItem("lechery:draft")).name);
  if (saved !== "Aria") errors.push(`${name}: draft not saved (got ${saved})`);
  await page.close();
};

await run("phone", { width: 390, height: 844 });
await run("desktop", { width: 1280, height: 800 });
await browser.close();
console.log(errors.length ? errors.join("\n") : "no errors");
process.exit(errors.length ? 1 : 0);
