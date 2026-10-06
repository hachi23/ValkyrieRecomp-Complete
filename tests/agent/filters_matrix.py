#!/usr/bin/env python3
"""Capture the first_field checkpoint at 4x with nearest, smooth and
smooth + de-dither on Vulkan, and save side-by-side crops of a sprite, the
dialogue text and a dithered background as cmp_all.png."""
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graphics_matrix as g

NAMES = ['nearest4', 'smooth4', 'smooth4_dedither']
BOXES = {'sprite': (1120, 520, 1260, 620), 'text': (700, 120, 980, 230),
         'background': (80, 200, 280, 350)}

g.RUNS = {
    'nearest4': dict(supersampling=4, texture_filtering='nearest', antialiasing=True),
    'smooth4': dict(supersampling=4, texture_filtering='smooth', antialiasing=True),
    'smooth4_dedither': dict(supersampling=4, texture_filtering='smooth', antialiasing=True,
                             texture_dedither=True),
}
g.diff_fraction = lambda a, b: None
g.main()

out = sorted((g.ROOT / 'analysis/agent').glob('graphics-*'))[-1]
ims = {n: Image.open(out / f'{n}.hires.png').convert('RGB') for n in NAMES}
sheet = Image.new('RGB', (3 * 430, 310 * len(BOXES)), 'white')
for row, box in enumerate(BOXES.values()):
    for col, name in enumerate(NAMES):
        sheet.paste(ims[name].crop(box).resize((420, 300), Image.NEAREST), (col * 430, row * 310))
sheet.save(out / 'cmp_all.png')
print(out / 'cmp_all.png')
