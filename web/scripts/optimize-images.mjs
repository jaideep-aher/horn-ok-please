/**
 * Write AVIF and WebP siblings for drawings under public/{stimuli,xai,round3,dev}.
 * Originals stay. Nothing under public/data is read or written.
 */
import { readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const root = path.resolve(import.meta.dirname, "..");
const publicDir = path.join(root, "public");
const dataDir = path.join(publicDir, "data");
const dirs = ["stimuli", "xai", "round3", "dev"];
const raster = new Set([".png", ".jpg", ".jpeg", ".webp"]);

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...(await walk(full)));
    else files.push(full);
  }
  return files;
}

function assertOutsideData(file) {
  const rel = path.relative(dataDir, file);
  if (rel === "" || (!rel.startsWith("..") && !path.isAbsolute(rel))) {
    throw new Error(`refusing to touch ${file}`);
  }
}

const sizes = {};
let avifBytes = 0;
let webpBytes = 0;
let avifCount = 0;
let webpCount = 0;

for (const dir of dirs) {
  const abs = path.join(publicDir, dir);
  assertOutsideData(abs);
  let files;
  try {
    files = await walk(abs);
  } catch (error) {
    if (error && error.code === "ENOENT") continue;
    throw error;
  }
  const present = new Set(files);
  for (const file of files) {
    assertOutsideData(file);
    const ext = path.extname(file).toLowerCase();
    if (!raster.has(ext)) continue;
    if (ext === ".webp") {
      const stem = file.slice(0, -ext.length);
      if (present.has(`${stem}.png`) || present.has(`${stem}.jpg`) || present.has(`${stem}.jpeg`)) {
        continue;
      }
    }
    const meta = await sharp(file).metadata();
    if (!meta.width || !meta.height) throw new Error(`no dimensions for ${file}`);
    const rel = `/${path.relative(publicDir, file).split(path.sep).join("/")}`;
    sizes[rel] = { width: meta.width, height: meta.height };
    const stem = file.slice(0, -ext.length);
    if (ext !== ".avif") {
      const dest = `${stem}.avif`;
      assertOutsideData(dest);
      const info = await sharp(file).avif({ quality: 50 }).toFile(dest);
      avifBytes += info.size;
      avifCount += 1;
    }
    if (ext !== ".webp") {
      const dest = `${stem}.webp`;
      assertOutsideData(dest);
      const info = await sharp(file).webp({ quality: 72 }).toFile(dest);
      webpBytes += info.size;
      webpCount += 1;
    }
  }
}

const ordered = Object.fromEntries(Object.keys(sizes).sort().map((key) => [key, sizes[key]]));
const manifestPath = path.join(root, "src/lib/image-sizes.json");
if (manifestPath.startsWith(dataDir)) throw new Error("manifest must not land in public/data");
await writeFile(manifestPath, `${JSON.stringify(ordered, null, 2)}\n`);
console.log(
  `optimize-images: ${Object.keys(ordered).length} sources, ${avifCount} avif (${avifBytes} bytes), ${webpCount} webp (${webpBytes} bytes)`,
);
