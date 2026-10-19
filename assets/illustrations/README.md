# Food illustration collection · soft 2D anime

Generated with the image-generation tool available in this chat on 2026-10-19, following the user’s approved Japanese 2D animation food direction and subsequent request for softer colored outlines and gentler colors. The rejected photorealistic study and harder prototype are not shipped. No film screenshots, remote food library, 3D renderer, external paid API or runtime image service is used.

## Sources and independent crops

Eight transparent PNG masters are preserved intact in `source/`. `sources.json` and `manifest.json` map each optimized asset back to its master and crop. Dishes were generated in 2×2 grids, ingredient grids in 4×3 / 4×4; the oats and protein powder supplement is 2×1. The optional `/Volumes/Extreme Pro/ACTIVE/Claude Code/YouTube/` path was unavailable; none of its files or frames was read or used.

Run `python3 scripts/prepare_food_assets.py` from the repository root (Pillow, numpy, scipy required for authoring only). The script isolates each food silhouette, preserving caps and stems despite slight grid drift. It creates an independent transparent canvas for each asset, never upscales the artwork and never references neighboring grid cells at runtime. Each dish has at least 15% space on all sides; icons keep at least 9%. Output is WebP with alpha: 960×640 for dishes, 192×192 for ingredient icons, quality 90 / 92. The hero basket is 640×440 at quality 92 with at least 11% clear space. Originals stay unchanged.

55 assets: 12 dish illustrations including a generic rice bowl, 42 ingredient / supply illustrations and one hero grocery basket. The optimized collection is 1,360,160 bytes versus 15,666,843 bytes of masters (91.3% smaller). All are embedded once in the standalone HTML SVG definitions. Individual `<use>` elements reuse the correctly sized padded assets; no atlas viewBox cropping or external image requests remain. The readable generated definitions file is ignored; rerunning the script updates the HTML block and available-image registry directly.

## Visual use

Cooked dishes have their own shapes: irregular tomato and folded egg, broad sweet-potato leaves versus slender pea shoots, varied braised mince, potato chunks, pork belly and distinguishable soups. Small icons simplify structure at phone size. Brand, typography and UI controls keep their existing roles; search, add, sync and delete use simple code-drawn SVG icons.

Food bytes never enter app state, JSON backups or Supabase. New user-created recipes initially use a generic food illustration; existing saved artwork choices are preserved. Recipe-specific artwork is added through subsequent repository updates, not an unconfigured in-app generation service.

The recipe-page hero basket now matches the food collection: soft colored contours, layered leafy vegetables, tomato, carrot and daikon, simplified woven straw and gentle shading. `source/hero-01.png` is the untouched generated master; `decoration/basket.webp` is 58,470 bytes. The old geometric basket and floating hearts were replaced; the brand mark and UI action icons remain unchanged.
