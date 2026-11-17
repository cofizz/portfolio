"""Builds pre-sized images from the full screenshots, so the browser never has to
shrink a 2000px image into a small box (that's what made them look blurry).

  thumbs/   folder grid tiles (shown about 120x90)
  previews/ folder detail view on the right (shown about 460px wide)
  cards/    3:4 cards in the "Selected work" gallery (shown about 295x393)

Run after adding or replacing a project image: python make-thumbs.py"""
import re
from pathlib import Path
from PIL import Image, ImageFilter

root = Path(__file__).parent
src = (root / 'index.html').read_text(encoding='utf-8')
block = src[src.index('const PROJECTS'):src.index('];', src.index('const PROJECTS'))]

def sharpen(im):
    return im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=2))

def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)

def cover_top(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    left = (im.width - w) // 2
    return im.crop((left, 0, left + w, h))

def save(im, folder, name):
    (root / folder).mkdir(exist_ok=True)
    out = root / folder / (Path(name).stem + '.jpg')
    sharpen(im).save(out, quality=86, optimize=True, progressive=True)
    print(f'{folder}/{out.name}', im.size)

# folder grid + detail preview, for every project with an image
for entry in re.findall(r'\{[^{}]*\}', block):
    m = re.search(r"img:'([^']+)'", entry)
    if not m:
        continue
    name = m.group(1)
    im = Image.open(root / name).convert('RGB')
    if 'phone:true' in entry:
        save(fit_h(im, 260), 'thumbs', name)
        save(fit_h(im, 900) if im.height > 900 else im, 'previews', name)
    else:
        save(cover_top(im, 360, 270), 'thumbs', name)
        save(im.resize((1000, round(im.height * 1000 / im.width)), Image.LANCZOS)
             if im.width > 1000 else im, 'previews', name)

# gallery cards: hand-picked 3:4 crop box (left, top, right, bottom) per source image
CARDS = {
    'GuessTheRide.png': (380, 0, 1123, 991),
    'Coffeenvite.jpg':  (0, 0, 780, 1040),
    'Camber.jpg':       (574, 0, 1586, 1350),
    'fornata.png':      (420, 0, 1020, 800),
}
for name, box in CARDS.items():
    im = Image.open(root / name).convert('RGB').crop(box)
    save(im.resize((600, 800), Image.LANCZOS), 'cards', name)
