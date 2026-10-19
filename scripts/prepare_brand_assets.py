"""Optimize the generated brand master for the header and installable app."""
from pathlib import Path
import base64
import re

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    source = Image.open(ROOT / 'assets/brand/source.png').convert('RGBA')
    alpha = np.asarray(source.getchannel('A'))
    labels, count = ndimage.label(alpha > 24)
    sizes = np.bincount(labels.ravel())
    keep = [index for index in range(1, count + 1) if sizes[index] > 300]
    mask = ndimage.binary_dilation(np.isin(labels, keep), iterations=5)
    pixels = np.asarray(source).copy()
    pixels[:, :, 3][~mask] = 0
    source = Image.fromarray(pixels)
    crop = source.crop(source.getchannel('A').getbbox())
    icons = ROOT / 'pwa/icons'
    icons.mkdir(parents=True, exist_ok=True)
    for name, size in [('icon-192.png', 192), ('icon-512.png', 512), ('apple-touch-icon.png', 180), ('favicon.png', 32)]:
        # Keep the mark comfortably inside the maskable icon safe circle.
        art = crop.copy()
        art.thumbnail((round(size * .68), round(size * .60)), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (size, size), '#f6f5ee')
        canvas.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
        canvas.convert('RGB').save(icons / name, optimize=True)
    art = crop.copy()
    art.thumbnail((116, 116), Image.Resampling.LANCZOS)
    header = Image.new('RGBA', (128, 128))
    header.alpha_composite(art, ((128 - art.width) // 2, (128 - art.height) // 2))
    output = ROOT / 'assets/brand/header.webp'
    header.save(output, 'WEBP', quality=92, method=6, exact=True)
    encoded = base64.b64encode(output.read_bytes()).decode()
    definition = '<!-- BRAND-ASSET-START -->\n<image id="brand-basket" width="128" height="128" href="data:image/webp;base64,' + encoded + '"/>\n<!-- BRAND-ASSET-END -->'
    page = ROOT / 'little-basket.html'
    html, count = re.subn(r'<!-- BRAND-ASSET-START -->.*?<!-- BRAND-ASSET-END -->', definition, page.read_text(), flags=re.S)
    if count != 1:
        raise ValueError('Expected one brand asset block')
    page.write_text(html)
    print('Brand header:', output.stat().st_size, 'bytes; opaque home-screen icons prepared')


if __name__ == '__main__':
    prepare()
