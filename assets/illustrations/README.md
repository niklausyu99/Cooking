# Food illustration collection · soft 2D anime

Generated with the image-generation tool available in this chat on 2026-10-19, following the user’s approved Japanese 2D animation food direction and subsequent request for softer colored outlines and gentler colors. The rejected photorealistic study and harder prototype are not shipped. No film screenshots, remote food library, 3D renderer, external paid API or runtime image service is used.

## Sources and independent crops

Seven transparent PNG masters are preserved intact in `source/`. `sources.json` and `manifest.json` map each optimized asset back to its master and crop. Dishes were generated in 2×2 grids, ingredient grids in 4×3 / 4×4; the oats and protein powder supplement is 2×1. The optional `/Volumes/Extreme Pro/ACTIVE/Claude Code/YouTube/` path was unavailable; none of its files or frames was read or used.

Run `python3 scripts/prepare_food_assets.py` from the repository root (Pillow, numpy, scipy required for authoring only). The script isolates each food silhouette, preserving caps and stems despite slight grid drift. It creates an independent transparent canvas for each asset, never upscales the artwork and never references neighboring grid cells at runtime. Each dish has at least 15% space on all sides; icons keep at least 9%. Output is WebP with alpha: 960×640 for dishes, 192×192 for ingredient icons, quality 90 / 92. Originals stay unchanged.

54 assets: 12 dish illustrations including a generic rice bowl, and 42 ingredient / supply illustrations. The optimized collection is 1,301,690 bytes versus 13,658,077 bytes of masters (90.5% smaller). All are embedded once in the standalone HTML SVG definitions. Individual `<use>` elements reuse the correctly sized padded assets; no atlas viewBox cropping or external image requests remain. The readable generated definitions file is ignored; rerunning the script updates the HTML block and available-image registry directly.

## Visual use

Cooked dishes have their own shapes: irregular tomato and folded egg, broad sweet-potato leaves versus slender pea shoots, varied braised mince, potato chunks, pork belly and distinguishable soups. Small icons simplify structure at phone size. Brand, typography and UI controls keep their existing roles; search, add, sync and delete use simple code-drawn SVG icons.

Food bytes never enter app state, JSON backups or Supabase. New user-created recipes initially use the selected generic food illustration. Recipe-specific artwork is added through subsequent repository updates, not an unconfigured in-app generation service.
