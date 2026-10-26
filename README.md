# Invitation HTML references

Two self-contained invitation editors for use as implementation references by an AI agent.

| Design | Finished HTML | Preview |
|---|---|---|
| Whale birthday | [Editor](whale-birthday/Editor.html) | [PNG](whale-birthday/Preview.png) |
| Pumpkin gender reveal | [Editor](pumpkin-gender-reveal/Editor.html) | [PNG](pumpkin-gender-reveal/Preview.png) |

Download an Editor.html file and open it in a current desktop Chrome or Edge browser. GitHub's source viewer does not execute the editor. Internet access is unnecessary after downloading the HTML.

## Editing features

Each editable field has independent embedded-font selection, point sizing, automatic fitting with a minimum size, bold, italic, underline, fill and three ordered letter colors, outline, shadow, alignment, letter spacing, and position. Body fields support wrapping and line spacing. The whale name supports procedural painted texture and stitching, each with separate controls. Focus a text input to select it, or use the field selector. Global undo/redo, selected-field reset and full reset preserve independent field settings.

Save edits stores settings, including unfinished text. Load edits validates product identity, types, ranges, colors and supported glyphs before replacing state. Save personalized HTML embeds the current valid settings as its new opening/reset default. Print exports are blocked by invalid required content or out-of-bounds text. Fixed artwork and the whale's illustrated age remain fixed.

## Print specifications

- PNG: 1500 Ã— 2100 pixels; 300 ppi metadata.
- PDF: one portrait page, 360 Ã— 504 points = 5 Ã— 7 inches.
- PDF image compression is lossless; no JPEG recompression of replacement text.
- Finished trim size only: no bleed or crop marks. RGB output; no claim of CMYK or PDF/X prepress certification.

The original illustration sources are 1060 Ã— 1484 pixels, equivalent to 212 ppi at 5 Ã— 7 inches. The exported raster is resampled to 1500 Ã— 2100; this does not create native 300 ppi illustration detail. Editable typography is rendered at the export resolution. The procedural name lettering is an approximation of the original painted glyphs, not an identical copy of the original AI-painted word.

## Agent instructions

1. Read [AGENTS.md](AGENTS.md) and the verification records before adopting this renderer.
2. Reuse the single common renderer, with product-specific defaults and field geometry in the embedded `productData` JSON. Both HTML files contain their own fonts, licenses and background and work independently.
3. Preserve the original artwork outside the authorized repair regions. A working editor is not proof of a clean plate. Inspect every cleared field at native resolution.
4. Calibrate every field against the new product's original typography and decorations. Do not transfer one product's placement, font or cleanup area blindly to another design.
5. Keep required printed suffixes coherent, preserve fixed ages, and follow the user's replacement-name plan. The whale source personal name and its reference replacement have the same initial and four letters; the gender-reveal design has no personal-name field to invent.
6. Keep fit calculations inclusive of outlines, shadows, underline and stitching. Moving text must not change size. Do not crop overflow or silently discard lines.
7. Verify new products after fonts load. Use changed/short/long body fields, the name case/length matrix where applicable, independent blank/restore checks, style controls, saved HTML reopening and actual downloads.
8. Run the included verification script after renderer changes. Its scriptable read-only `window.InvitationEditor` interface exposes status, fields, layout, configuration and export functions for inspection. Do not ship changes with unexplained failing checks.
9. Re-export the final preview from the exact final saved HTML and record its SHA-256 hash. Follow the user's output path and review boundary.

The interface keeps the supplied editor's product titles and restrained neutral layout, with a design-specific accent. No shop name or logo was supplied, so no separate shop identity is invented or claimed as approved. For another brand, use the user's approved brand assets and check the resulting layout.

## Repeat verification

Use Python 3 with the dependencies below, then install the Playwright Chromium runtime:

```sh
python -m pip install -r requirements.txt
python -m playwright install chromium
python scripts/verify.py
python scripts/verify_controls.py
```

Local test evidence goes into the ignored `qa-local/` directory. The committed [verification record](verification/RESULTS.json) records the supplied files and the checks actually performed. Tests cover Chromium with desktop and mobile viewport sizes; this is not a claim of testing every browser, physical phone, screen reader or printer.

Fonts and their license text are embedded in each editor, and visible through Font licenses. Bold and italic may be synthesized from the selected embedded face. No original font binary has been modified. This repository does not grant additional rights to third-party artwork.

For Etsy buyer delivery, package the HTML with opening/extraction instructions in a supported ZIP and check Etsy's current upload requirements. This repository is an agent reference collection, not a live Etsy listing or a claim of marketplace approval.

## Visual evidence

- [Whale blank fields](verification/whale-birthday-blank-review.jpg)
- [Gender reveal blank fields](verification/pumpkin-gender-reveal-blank-review.jpg)
- [Name case and length matrix](verification/name-matrix-review.jpg)
- [All embedded English glyphs](verification/glyph-sheet.png)
- [Cleanup method and prompts](verification/CLEANUP.md)
