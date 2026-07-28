import { cp, mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const standaloneApp = path.join(
  webRoot,
  ".next",
  "standalone",
  "apps",
  "web",
);
const standaloneRoot = path.join(webRoot, ".next", "standalone");

await mkdir(path.join(standaloneApp, ".next"), { recursive: true });
await cp(path.join(webRoot, "public"), path.join(standaloneApp, "public"), {
  recursive: true,
  force: true,
});
await cp(
  path.join(webRoot, ".next", "static"),
  path.join(standaloneApp, ".next", "static"),
  {
    recursive: true,
    force: true,
  },
);
await writeFile(
  path.join(standaloneRoot, "server.js"),
  'require("./apps/web/server.js");\n',
);
