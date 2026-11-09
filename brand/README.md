# LipidLens brand assets

The visual identity used on the Hugging Face Space, the pitch deck and future materials. Built in October 2026. The full rules are in `VI-manual.zh.md` (Chinese); `overview.zh.html` shows every asset on one page.

## Direction

The visual language comes from two sources: the covers of the Chinese 人教版 high-school biology textbooks (desaturated grey-green, cream title blocks, horizontal colour bands, semi-3D airbrushed scientific illustration) and the European scientific illustration tradition (Isotype, wall charts, Braun). The aim is that a Danish investor reads it as a precision scientific instrument company, not a consumer health brand. The textbook covers are a reference for the language only; nothing here copies their layout, titles or publisher marks.

## Files

| Path | Contents |
|---|---|
| `logo/` | Wordmark and mark in colour, reverse and mono; stacked and horizontal; app icon; a 16px simplified mark. `misuse/` holds six examples of what not to do. `png/` holds raster versions |
| `tokens/` | `lipidlens_tokens.json` and `.css` hold the colour, type, spacing and radius tokens. `lipidlens.css` holds component styles: bands, title blocks, buttons, status labels, the ILLUSTRATIVE stamp, cards, tables, figures |
| `icons/` | Ten line icons on a 24px grid, stroke 1.75, `currentColor` |
| `illustration/` | Cell membrane, liposome, lipid nanoparticle, the mixer with the add-on module, and a one-picture overview of the project. Editable SVG with live text |
| `dataviz/` | A matplotlib style and helper (`lipidlens_viz.py`), a Plotly template (`lipidlens_plotly.py`), seven example charts, and the Archivo font files the style needs |
| `motion/` | Five short animations as self-contained HTML, each with a still SVG fallback |
| `hardware/` | How to photograph and label hardware: camera positions, lighting, and the PROTOTYPE / RENDER labels |

## The parts that matter most

**Colour.** Primary green `#3A5442`, paper `#FBFAF6`, cream title blocks `#F2EFE3`, ink `#1B211E`, auxiliary blue `#2F6283`. The logo colour `#12333F` is used for the logo only. All 27 text-on-background combinations meet WCAG AA, the lowest being 5.27:1.

**Type.** Archivo for Latin text, Noto Sans SC for Chinese body text, Noto Serif SC for Chinese titles inside cream blocks. The logo wordmark is Arimo, converted to outlines, because the logo submitted in the DTU Skylab application rendered in Arial and Arimo is the metric-compatible open-licensed equivalent. All four are SIL OFL.

**Evidence encoding, used in every chart.** Measured results are a filled dark circle on a solid line. Internal results are a grey square. Predictions are a hollow blue circle on a dashed line with a hatched interval. Anything illustrative carries an "ILLUSTRATIVE DATA, NOT RESULTS" stamp. Project status is encoded the same way everywhere: solid is done, outlined is in progress, dashed is planned. The point is that nothing on a page can be mistaken for a validated result.

**What this identity does not do.** No gradients, glows, frosted glass, neon on dark, node-network "AI brain" graphics, hexagon grids, DNA helices, particle fields or stock lab photography. Not the words innovation, revolutionizing or cutting-edge.

## Known weaknesses

Two lipid colours in the nanoparticle illustration are close in greyscale. Data series 3 and 4 fall below 3:1 against paper as graphics, so both are outlined and also differ in marker shape. Pale green bands with cream title blocks can read as an educational publication when they appear alone, so any first screen should also show the instrument.
