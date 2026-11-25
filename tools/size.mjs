/*
 * The size budget: every file in the build, gzipped, must total under the
 * limit. See CLAUDE.md for when the limit may change -- and it is not
 * "when this script is inconvenient".
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { gzipSync } from "node:zlib";

const LIMIT = 20 * 1024;
const root = process.argv[2] ?? "dist";

function files(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : [path];
  });
}

const rows = files(root).map((path) => {
  const raw = readFileSync(path);
  return { path: relative(root, path), raw: raw.length, gz: gzipSync(raw, { level: 9 }).length };
});

const total = rows.reduce((sum, row) => sum + row.gz, 0);
const kb = (bytes) => (bytes / 1024).toFixed(2).padStart(6) + " KB";

for (const row of rows.sort((a, b) => b.gz - a.gz)) {
  console.log(`${kb(row.gz)}  (${kb(row.raw)} raw)  ${row.path}`);
}
console.log(`${kb(total)}  total, gzipped — limit ${kb(LIMIT)}, ${((total / LIMIT) * 100).toFixed(0)}% used`);

if (total > LIMIT) {
  console.error(`\nOver the size budget by ${kb(total - LIMIT)}. Make it smaller.`);
  process.exit(1);
}
