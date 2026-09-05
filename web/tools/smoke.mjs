/*
 * A browser smoke test.
 *
 * Every hard bug in this project so far has been invisible outside a real
 * browser -- a canvas that never painted, a library that failed to load, a
 * layout that only broke at a phone's aspect ratio. So this walks the whole
 * game with a real engine and writes screenshots to look at.
 *
 *   npx vite build && npx vite preview --port 4173 &
 *   node tools/smoke.mjs [outdir]
 */
import { chromium } from "playwright";
import { join } from "node:path";
import { mkdirSync } from "node:fs";

const DIR = process.argv[2] ?? "smoke-out";
mkdirSync(DIR, { recursive: true });
const out = (name) => join(DIR, name);

const browser = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium" });
const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3 });
const errors = [];
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
page.on("pageerror", (e) => errors.push("pageerror: " + e.message));

await page.goto("http://localhost:4173/", { waitUntil: "networkidle" });
await page.screenshot({ path: out("1-menu.png") });

await page.getByRole("button", { name: "New game" }).click();
await page.waitForTimeout(3000);
await page.screenshot({ path: out("2-creation.png") });
console.log("avatar status:", await page.locator(".status").count() ? await page.locator(".status").first().innerText() : "ready");

await page.getByPlaceholder("Wanderer").fill("Test Name");
await page.locator('input[type="range"]').nth(2).fill("6");
await page.waitForTimeout(1500);
await page.screenshot({ path: out("3-creation-filled.png") });

await page.getByRole("button", { name: "Begin" }).click();
await page.waitForTimeout(1500);
await page.screenshot({ path: out("4-play.png") });

// Walk with the keyboard for a second.
await page.keyboard.down("ArrowRight");
await page.waitForTimeout(900);
await page.keyboard.up("ArrowRight");
await page.screenshot({ path: out("5-moved.png") });

await page.getByRole("button", { name: "Log" }).click();
await page.waitForTimeout(400);
await page.screenshot({ path: out("6-log.png") });
await page.getByRole("button", { name: "Body" }).click();
await page.waitForTimeout(1500);
await page.screenshot({ path: out("7-body.png") });

// And the wide layout.
await page.setViewportSize({ width: 1280, height: 800 });
await page.waitForTimeout(800);
await page.screenshot({ path: out("8-wide.png") });

console.log("errors:", errors.length ? errors : "none");
await browser.close();
