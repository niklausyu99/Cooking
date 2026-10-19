"""Slice generated grids into independent padded WebP assets; never upscale the art.

User authorized grid generation, cropping and image optimization. Masters stay intact.
Requires Pillow, numpy, scipy; no image service or runtime dependency in the app.
"""
from pathlib import Path
import base64
import hashlib
import json
import re
import shutil

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets/illustrations'
GRIDS = {
    'dishes-01': (2, 2, ['tomato-egg', 'sweet-leaves', 'pea-shoots', 'mince-rice']),
    'dishes-02': (2, 2, ['potato-mince', 'pork-stew', 'tomato-soup', 'pickle-soup']),
    'dishes-03': (2, 2, ['lotus-soup', 'radish-soup', 'cress-soup', 'rice-bowl']),
    'ingredients-01': (4, 3, ['tomato', 'potato', 'carrot', 'radish', 'cress', 'lotus', 'sweet-leaves', 'pea-shoots', 'scallion', 'ginger', 'garlic', 'egg']),
    'ingredients-02': (4, 3, ['bones', 'mince', 'belly', 'peanut', 'rice', 'pickle', 'oil', 'soy', 'oyster', 'salt', 'sugar', 'cooking-wine']),
    'ingredients-03': (4, 4, ['beanpaste', 'plum', 'anise', 'jar', 'blueberry', 'grape', 'apple', 'pineapple', 'banana', 'strawberry', 'cherry-tomato', 'milo', 'condensed-milk', 'cream-crackers', 'milk-carton', 'fruit-basket']),
    'ingredients-04': (2, 1, ['oats', 'protein-powder']),
}


def prepare():
    specs = json.loads((ASSETS / 'sources.json').read_text())
    definitions, metadata = [], []
    original_bytes = 0
    for spec in specs:
        key = spec['key']
        master = ASSETS / 'source' / (key + '.png')
        if not master.exists():
            master.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / spec['path'], master)
        original_bytes += master.stat().st_size
        image = Image.open(master).convert('RGBA')
        columns, rows, names = GRIDS[key]
        width, height = image.size
        alpha = np.asarray(image.getchannel('A'))
        labels, _ = ndimage.label(alpha > 24)
        counts = np.bincount(labels.ravel())
        objects = ndimage.find_objects(labels)
        # Use connected silhouettes so slight grid drift cannot cut a bottle cap or stem.
        cells = [[] for _ in names]
        min_area = max(60, int(width * height / (columns * rows) * .0005))
        for index, slices in enumerate(objects, 1):
            if slices is None or counts[index] < min_area:
                continue
            yy, xx = slices
            center_x = (xx.start + xx.stop) / 2
            center_y = (yy.start + yy.stop) / 2
            column = min(columns - 1, int(center_x / width * columns))
            row = min(rows - 1, int(center_y / height * rows))
            cells[row * columns + column].append((index, xx.start, yy.start, xx.stop, yy.stop))
        for name, components in zip(names, cells):
            if not components:
                raise ValueError(f'{key}/{name}: missing food silhouette; inspect source')
            x0 = min(c[1] for c in components)
            y0 = min(c[2] for c in components)
            x1 = max(c[3] for c in components)
            y1 = max(c[4] for c in components)
            if min(x0, y0, width - x1, height - y1) < 2:
                raise ValueError(f'{key}/{name}: object touches source edge; regenerate rather than crop it')
            box = (max(0, x0 - 6), max(0, y0 - 6), min(width, x1 + 6), min(height, y1 + 6))
            crop = image.crop(box)
            # Remove detached alpha-cutout speckles, preserving the complete food + anti-alias edge.
            mask = np.isin(labels, [c[0] for c in components])
            mask = ndimage.binary_dilation(mask, iterations=5)
            crop_array = np.asarray(crop).copy()
            crop_array[:, :, 3][~mask[box[1]:box[3], box[0]:box[2]]] = 0
            crop = Image.fromarray(crop_array)
            kind = 'dish' if key.startswith('dishes') else 'ingredient'
            canvas_size = (960, 640) if kind == 'dish' else (192, 192)
            # Dish images retain 15% clear space on every side; icons keep a 9% gutter.
            fill = .70 if kind == 'dish' else .82
            max_w, max_h = int(canvas_size[0] * fill), int(canvas_size[1] * fill)
            scale = min(max_w / crop.width, max_h / crop.height, 1)
            size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
            resized = crop.resize(size, Image.Resampling.LANCZOS) if size != crop.size else crop
            canvas = Image.new('RGBA', canvas_size)
            canvas.alpha_composite(resized, ((canvas.width - resized.width) // 2, (canvas.height - resized.height) // 2))
            output = ASSETS / kind / (name + '.webp')
            output.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(output, 'WEBP', quality=90 if kind == 'dish' else 92, method=6, exact=True)
            encoded = base64.b64encode(output.read_bytes()).decode()
            asset_id = 'food-' + kind + '-' + name
            definitions.append(f'<image id="{asset_id}" width="{canvas.width}" height="{canvas.height}" href="data:image/webp;base64,{encoded}"/>')
            metadata.append({'id': asset_id, 'key': name, 'kind': kind, 'file': str(output.relative_to(ROOT)), 'source': str(master.relative_to(ROOT)), 'source_crop': list(box), 'dimensions': list(canvas_size), 'content_size': list(size), 'bytes': output.stat().st_size, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()})
    manifest = {'format': 'WebP with alpha', 'quality': {'dish': 90, 'ingredient': 92}, 'assets': metadata, 'source_bytes': original_bytes, 'optimized_bytes': sum(item['bytes'] for item in metadata)}
    (ASSETS / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (ASSETS / 'embedded-definitions.txt').write_text('\n'.join(definitions))
    app = ROOT / 'little-basket.html'
    html = app.read_text()
    html, count = re.subn(r'<!-- FOOD-ASSETS-START -->.*?<!-- FOOD-ASSETS-END -->',
                          '<!-- FOOD-ASSETS-START -->\n' + '\n'.join(definitions) + '\n<!-- FOOD-ASSETS-END -->', html, flags=re.S)
    if count != 1:
        raise ValueError('Expected exactly one food asset block in app')
    keys = {kind: [item['key'] for item in metadata if item['kind'] == kind] for kind in ('dish', 'ingredient')}
    html = re.sub(r'const FOOD_IMAGES=.*?;', 'const FOOD_IMAGES=' + json.dumps(keys, separators=(',', ':')) + ';', html, count=1)
    app.write_text(html)
    # Normalize source locations so the pipeline works from a fresh checkout.
    (ASSETS / 'sources.json').write_text(json.dumps([{'key': spec['key'], 'path': str((ASSETS / 'source' / (spec['key'] + '.png')).relative_to(ROOT))} for spec in specs], indent=2) + '\n')
    print(f'{len(metadata)} independent assets; original {original_bytes:,} bytes; WebP {manifest["optimized_bytes"]:,} bytes; {(1-manifest["optimized_bytes"]/original_bytes)*100:.1f}% smaller')


if __name__ == '__main__':
    prepare()
