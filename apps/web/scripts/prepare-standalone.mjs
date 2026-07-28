import { cp, mkdir, rm, writeFile } from "node:fs/promises";
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
const hostingerRoot = path.join(webRoot, "dist");

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

await rm(hostingerRoot, { recursive: true, force: true });
await mkdir(hostingerRoot, { recursive: true });
await cp(
  path.join(standaloneRoot, "node_modules"),
  path.join(hostingerRoot, "node_modules"),
  { recursive: true, force: true },
);
await cp(
  path.join(standaloneApp, ".next"),
  path.join(hostingerRoot, ".next"),
  { recursive: true, force: true },
);
await cp(
  path.join(standaloneApp, "public"),
  path.join(hostingerRoot, "public"),
  { recursive: true, force: true },
);
await cp(
  path.join(webRoot, "package.json"),
  path.join(hostingerRoot, "package.json"),
  { force: true },
);
