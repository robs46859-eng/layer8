import { cp } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);
const nodeModulesRoot = path.dirname(
  path.dirname(require.resolve("next/package.json")),
);

await cp(nodeModulesRoot, path.join(webRoot, ".next", "node_modules"), {
  recursive: true,
  force: true,
});
await cp(
  path.join(webRoot, "public"),
  path.join(webRoot, ".next", "public"),
  { recursive: true, force: true },
);
await cp(
  path.join(webRoot, "package.json"),
  path.join(webRoot, ".next", "package.json"),
  { force: true },
);
