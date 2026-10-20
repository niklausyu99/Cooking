"""Slice generated grids into independent padded WebP assets; never upscale the art.

User authorized grid generation, cropping and image optimization. Masters stay intact.
Requires Pillow, numpy, scipy; no image service or runtime dependency in the app.
"""
from pathlib import Path
import argparse
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
    'dishes-04': (2, 2, ['lazi-ji', 'pepper-pork', 'ramen-chashu', None]),
    'ingredients-01': (4, 3, ['tomato', 'potato', 'carrot', 'radish', 'cress', 'lotus', 'sweet-leaves', 'pea-shoots', 'scallion', 'ginger', 'garlic', 'egg']),
    'ingredients-02': (4, 3, ['bones', 'mince', 'belly', 'peanut', 'rice', 'pickle', 'oil', 'soy', 'oyster', 'salt', 'sugar', 'cooking-wine']),
    'ingredients-03': (4, 4, ['beanpaste', 'plum', 'anise', 'jar', 'blueberry', 'grape', 'apple', 'pineapple', 'banana', 'strawberry', 'cherry-tomato', None, None, None, 'milk-carton', 'fruit-basket']),
    'ingredients-04': (2, 1, ['oats', None]),
    'ingredients-05': (4, 3, ['yogurt', 'dark-chocolate', 'mixed-nuts', 'chicken-thigh', 'green-chili', 'dried-chili', 'sichuan-pepper', 'white-pepper', 'starch', 'sesame', 'black-beans', 'sake']),
    'ingredients-06': (1, 1, ['soup-bones']),
    'ingredients-07': (2, 2, ['instant-noodles', 'cream-crackers', 'milo', 'condensed-milk']),
    'ingredients-08': (1, 1, ['protein-powder']),
    'basket-stages': (4, 2, ['basket-stage-' + str(i) for i in range(7)] + [None]),
    'hero-basket-full': (1, 1, ['basket-stage-7']),
    'hero-01': (1, 1, ['basket']),
}


def definition(item):
    encoded = base64.b64encode((ROOT / item['file']).read_bytes()).decode()
    width, height = item['dimensions']
    return f'<image id="{item["id"]}" width="{width}" height="{height}" href="data:image/webp;base64,{encoded}"/>'


def prepare(only=None):
    specs = json.loads((ASSETS / 'sources.json').read_text())
    previous = json.loads((ASSETS / 'manifest.json').read_text()) if only else None
    definitions, metadata = [], []
    original_bytes = 0
    for spec in specs:
        key = spec['key']
        master = ASSETS / 'source' / (key + '.png')
        if not master.exists():
            master.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / spec['path'], master)
        original_bytes += master.stat().st_size
        columns, rows, names = GRIDS[key]
        if only and key not in only:
            # Explicit partial rebuild: preserve every untouched asset byte-for-byte.
            cached = {item['key']: item for item in previous['assets'] if item['source'] == str(master.relative_to(ROOT))}
            for name in names:
                if name is None:
                    continue
                item = cached.get(name)
                if not item or hashlib.sha256((ROOT / item['file']).read_bytes()).hexdigest() != item['sha256']:
                    raise ValueError(f'{key}/{name}: cached asset missing or changed; run a full rebuild')
                definitions.append(definition(item))
                metadata.append(item)
            continue
        image = Image.open(master).convert('RGBA')
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
        for cell_index, (name, components) in enumerate(zip(names, cells)):
            if name is None:  # Preserve unused grid cells in the master without shipping them.
                continue
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
            kind = 'dish' if key.startswith('dishes') else 'decoration' if key.startswith(('hero', 'basket-')) else 'ingredient'
            canvas_size = {'dish': (960, 640), 'ingredient': (192, 192), 'decoration': (640, 440)}[kind]
            # Preserve clear padding: dishes 15%, icons 9%, hero basket 11%.
            fill = {'dish': .70, 'ingredient': .82, 'decoration': .78}[kind]
            max_w, max_h = int(canvas_size[0] * fill), int(canvas_size[1] * fill)
            scale = min(max_w / crop.width, max_h / crop.height, 1)
            if key == 'basket-stages':
                # One common scale, basket center and floor across the eight frames.
                # Fitting each silhouette separately makes the basket shrink as food grows.
                canvas_size = (360, 300)
                scale = min(.70 * 1774 / width, 1)
            elif key == 'hero-basket-full':
                canvas_size = (360, 300)
                scale = min(300 / crop.width, 240 / crop.height, 1)
            size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
            resized = crop.resize(size, Image.Resampling.LANCZOS) if size != crop.size else crop
            canvas = Image.new('RGBA', canvas_size)
            position = ((canvas.width - resized.width) // 2, (canvas.height - resized.height) // 2)
            if key in ('basket-stages', 'hero-basket-full'):
                # Align the wicker body, not a leaf leaning beyond one side of the pile.
                pixels = np.asarray(crop)
                red, green, blue = (pixels[:, :, channel].astype(float) for channel in range(3))
                wicker = (pixels[:, :, 3] > 128) & (red > green * 1.08) & (green > blue * 1.12)
                wicker[:round(crop.height * .75)] = False
                _, wicker_x = np.where(wicker)
                if not len(wicker_x):
                    raise ValueError(f'{key}/{name}: basket-body alignment missing')
                basket_center = box[0] + (wicker_x.min() + wicker_x.max() + 1) / 2
                position = (round(canvas.width / 2 - (basket_center - box[0]) * scale), 270 - resized.height)
            canvas.alpha_composite(resized, position)
            output = ASSETS / kind / (name + '.webp')
            output.parent.mkdir(parents=True, exist_ok=True)
            canvas.save(output, 'WEBP', quality=90 if kind == 'dish' else 92, method=6, exact=True)
            asset_id = 'food-' + kind + '-' + name
            metadata.append({'id': asset_id, 'key': name, 'kind': kind, 'file': str(output.relative_to(ROOT)), 'source': str(master.relative_to(ROOT)), 'source_crop': list(box), 'dimensions': list(canvas_size), 'content_size': list(size), 'bytes': output.stat().st_size, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()})
            definitions.append(definition(metadata[-1]))
    manifest = {'format': 'WebP with alpha', 'quality': {'dish': 90, 'ingredient': 92, 'decoration': 92}, 'assets': metadata, 'source_bytes': original_bytes, 'optimized_bytes': sum(item['bytes'] for item in metadata)}
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
    # Center the visible silhouette in the floating button; retain the fixed floor in the list.
    basket_offsets = []
    for stage in range(8):
        asset = next(item for item in metadata if item['key'] == f'basket-stage-{stage}')
        with Image.open(ROOT / asset['file']) as frame:
            left, top, right, bottom = frame.convert('RGBA').getchannel('A').getbbox()
            basket_offsets.append([(left + right - frame.width) / 2, (top + bottom - frame.height) / 2])
    html, offset_count = re.subn(r'const BASKET_ICON_OFFSETS=.*?;', 'const BASKET_ICON_OFFSETS=' + json.dumps(basket_offsets, separators=(',', ':')) + ';', html, count=1)
    if offset_count != 1:
        raise ValueError('Expected the floating-basket alignment registry in app')
    app.write_text(html)
    # Normalize source locations so the pipeline works from a fresh checkout.
    (ASSETS / 'sources.json').write_text(json.dumps([{'key': spec['key'], 'path': str((ASSETS / 'source' / (spec['key'] + '.png')).relative_to(ROOT))} for spec in specs], indent=2) + '\n')
    print(f'{len(metadata)} independent assets; original {original_bytes:,} bytes; WebP {manifest["optimized_bytes"]:,} bytes; {(1-manifest["optimized_bytes"]/original_bytes)*100:.1f}% smaller')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', nargs='+', choices=GRIDS, help='Rebuild only these changed masters; verify and reuse the other assets')
    prepare(set(parser.parse_args().only or []))
