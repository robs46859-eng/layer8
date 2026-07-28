# SALTI8 Enterprise Design Directive

This document is the source of truth for SALTI8 brand naming and the visual
direction of Layer8 Adaptive. The original frontend remains the structural
reference; this directive governs its production refinement.

## 1. Brand architecture and nomenclature

Consistency in naming establishes authority.

| Context | Required name |
|---|---|
| Brand and logo | **SALTI8** |
| Creative and R&D company context | **SALTI8 Labs** |
| Legal and financial company context | **SALTI8, Inc.** |
| Domain | `salti8.com` |
| Flagship product, first mention | **Layer8 Adaptive by SALTI8** |
| Flagship product, subsequent mentions | **Layer8 Adaptive** |
| Core technology | **SALTI-B Engine** |
| Code and packages | `salti8`, `salti_b` |

Use the brand in all caps. Use the domain and package identifiers in lowercase.
Always capitalize and hyphenate **SALTI-B Engine**.

## 2. Visual palette: the enterprise suite

The SALTI8 aesthetic merges industrial precision with warm, tactile
functionality. Colors must feel grounded and mature while maintaining
high-contrast legibility in complex enterprise environments.

### Primary accent: burnt matte terracotta

- Use for active states, primary buttons, alerts, and focal points.
- Prefer an earthy rust over a vibrant orange.
- Keep the treatment matte and restrained, with a premium hardware-like feel.
- Reserve the accent for meaningful focus; do not flood large areas with it.

### Structural foundation: deep slate / titanium gray

- Use for data-heavy dashboards, sidebars, structural dividers, and text.
- Favor charcoal tones with strong canvas contrast.
- The role should communicate authority, security, and structural integrity.

### Canvas: alabaster / cloud white

- Use for background layers and primary workspace areas.
- Prefer a slightly warm off-white that reduces glare during long sessions.
- Preserve a clean, breathable workspace with clear information hierarchy.

Final production color values must be calibrated for WCAG 2.2 AA contrast,
light/dark behavior, and real interface states before being made canonical.
Do not invent page-specific hex values.

## 3. Depth and materiality

Transparency and depth must communicate hierarchy and active state, not exist
as decoration.

### Architectural acrylics

Transparent layers should resemble frosted acrylic or physical boardroom
partitions. Avoid exaggerated blur, glowing glassmorphism, or transparency that
reduces text contrast.

### Functional layering

1. Base layer: alabaster / cloud white.
2. Mid layer: deep slate panels with restrained elevation for data and code.
3. Top layer: burnt matte terracotta for the highest-priority interactive
   layer.

Preserve the reference frontend's blueprint frames, registration marks, square
geometry, modular grid, and thin-stroke icons. Materiality should refine those
elements rather than replace them.

## 4. Typographic architecture

### Primary display

- Family: **Barlow Condensed**
- Weights: 400 and 600
- Primary heading weight: 600
- Use for headings, navigation branding, prices, and prominent labels.

### Core interface

- Family: **Barlow**
- Weights: 400, 500, and 700
- Use for body copy, forms, buttons, and general interface text.

### Technical output

- Stack: `ui-monospace`, `Menlo`, `monospace`
- Use for API documentation, code blocks, logs, and raw technical output from
  the SALTI-B Engine and `salti8` packages.

Self-host production WOFF2 font assets, subset them to the characters in use,
and provide system fallbacks. Font loading must not block meaningful rendering
or cause avoidable layout shift.
