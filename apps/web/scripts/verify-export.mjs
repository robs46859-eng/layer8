#!/usr/bin/env node
/**
 * Post-build gate for the Hostinger static export.
 *
 * `next build` succeeding is not the same as the deployable artifact being
 * correct. This script asserts the things that silently break indexing:
 *
 *   - .htaccess survived the public/ copy (dotfile copying is not guaranteed)
 *   - robots.txt and sitemap.xml exist as real files, not directories
 *   - every route the runbook lists as required has an index.html
 *   - 404.html exists so ErrorDocument has something to serve
 *   - the sitemap advertises only URLs that were actually exported
 *
 * Exits non-zero on any failure so CI and the Hostinger build both stop.
 */
import { existsSync, readFileSync, statSync, copyFileSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = join(webRoot, "out");

const failures = [];
const notes = [];

function fail(message) {
  failures.push(message);
}

if (!existsSync(outDir)) {
  console.error("verify-export: out/ does not exist. Did `next build` run?");
  process.exit(1);
}

// --- .htaccess -------------------------------------------------------------
// Next copies public/ into out/, but dotfile handling has changed between
// releases. Copy it explicitly rather than trusting the behaviour.
const htaccessSrc = join(webRoot, "public", ".htaccess");
const htaccessOut = join(outDir, ".htaccess");
if (!existsSync(htaccessSrc)) {
  fail("public/.htaccess is missing from the repository");
} else if (!existsSync(htaccessOut)) {
  copyFileSync(htaccessSrc, htaccessOut);
  notes.push("copied public/.htaccess into out/ (next build did not)");
}

// --- SEO files must be files ----------------------------------------------
for (const file of ["robots.txt", "sitemap.xml", "manifest.webmanifest"]) {
  const target = join(outDir, file);
  if (!existsSync(target)) {
    fail(`out/${file} was not generated`);
    continue;
  }
  if (!statSync(target).isFile()) {
    // trailingSlash: true has previously turned these into directories
    // containing index.html, which serves the wrong content type.
    fail(`out/${file} is a directory, not a file`);
  }
}

// --- Required routes -------------------------------------------------------
const requiredRoutes = [
  "/",
  "/architecture/",
  "/ai-gateway/",
  "/llm-routing/",
  "/ai-governance/",
  "/governed-ai-agents/",
  "/human-in-the-loop-ai/",
  "/salti-b-engine/",
  "/spatial-intelligence/",
  "/integrations/",
  "/security/",
  "/pricing/",
  "/pilot/",
  "/contact/",
  "/docs/",
  "/glossary/",
  "/privacy/",
  "/terms/",
  "/acceptable-use/",
  "/compare/portkey/",
  "/compare/litellm/",
  "/compare/openrouter/",
  "/sign-in/",
  "/sign-up/",
  "/app/billing/",
  "/billing/success/",
];

for (const route of requiredRoutes) {
  const target = join(outDir, route, "index.html");
  if (!existsSync(target)) {
    fail(`route ${route} did not export (missing ${route}index.html)`);
  }
}

if (!existsSync(join(outDir, "404.html"))) {
  fail("out/404.html is missing — ErrorDocument 404 would fall through");
}

// --- Icons and social cards ------------------------------------------------
for (const asset of [
  "favicon.ico",
  "images/og/salti8-default.png",
  "images/og/salti8-architecture.png",
  "images/salti8-mark-192.png",
  "images/salti8-mark-512.png",
]) {
  if (!existsSync(join(outDir, asset))) {
    fail(`asset out/${asset} is missing`);
  }
}

// --- Sitemap must only advertise exported URLs -----------------------------
const sitemapPath = join(outDir, "sitemap.xml");
if (existsSync(sitemapPath) && statSync(sitemapPath).isFile()) {
  const xml = readFileSync(sitemapPath, "utf8");
  const locs = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
  if (locs.length === 0) {
    fail("sitemap.xml contains no <loc> entries");
  }
  for (const loc of locs) {
    const path = new URL(loc).pathname;
    const target = join(outDir, path, "index.html");
    if (!existsSync(target)) {
      fail(`sitemap advertises ${path} but it was not exported`);
    }
  }
  notes.push(`sitemap advertises ${locs.length} URLs, all exported`);

  // Noindex pages must never appear in the sitemap.
  for (const blocked of ["/sign-in/", "/sign-up/", "/app/", "/billing/"]) {
    if (locs.some((loc) => new URL(loc).pathname.startsWith(blocked))) {
      fail(`sitemap advertises noindex path ${blocked}`);
    }
  }
}

// --- Report ----------------------------------------------------------------
for (const note of notes) {
  console.log(`verify-export: ${note}`);
}

if (failures.length) {
  console.error("\nverify-export FAILED:");
  for (const failure of failures) {
    console.error(`  - ${failure}`);
  }
  process.exit(1);
}

console.log("verify-export: static export passed all release gates");
