import { cp, mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const standaloneRoot = path.join(webRoot, ".next", "standalone");
const standaloneApp = path.join(
  standaloneRoot,
  "apps",
  "web",
);
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

await rm(hostingerRoot, { recursive: true, force: true });
await cp(standaloneRoot, hostingerRoot, { recursive: true, force: true });
await writeFile(
  path.join(hostingerRoot, "server.js"),
  'require("./apps/web/server.js");\n',
);
