"""Write WebP copies of the site's photos and logos, and point the pages at them.

    python tools/make_webp.py

The JPEG and PNG originals stay where they are: social previews, structured
data and the favicon still use them, because some crawlers and chat apps do
not read WebP. This writes a `.webp` beside each original, scaled down to at
most twice the largest size the pages show it at, and rewrites `src="..."`,
`poster="..."` and CSS `url(...)` references to the WebP copy.

Re-run this after adding or replacing an image under assets/img, and after
tools/build_service_areas.py, which writes its hero photos as .jpg.
"""
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / 'assets' / 'img'

# Never converted: the favicon and the logo are referenced by browsers and
# crawlers that expect PNG.
SKIP = {'favicon.png', 'logo-main.png', 'logo-alt.png', 'symbol.png'}

# Largest width (px) worth shipping: about twice the widest the image is shown.
# Anything not listed keeps its own width.
MAX_WIDTH = {
    'tile-doorstep.jpg': 500, 'tile-kitchen-table.jpg': 500,
    'tile-bedside.jpg': 500, 'tile-vitals.jpg': 500,
    'logo-smh-sarasota.png': 240, 'logo-smh-venice.png': 240,
    'logo-hca-blake.png': 400, 'logo-american-lab.png': 400,
    'crest.png': 177, 'stamp.png': 400,
    'photo-5.jpg': 1200, 'photo-11.jpg': 1000,
}
QUALITY = 78

PAGES = (sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('service-areas/*.html'))
         + [p for p in sorted((ROOT / 'assets' / 'css').glob('*.css'))
            if not p.name.endswith('.min.css')]
         + [ROOT / 'tools' / 'build_service_areas.py'])

# src="/assets/img/x.jpg" or url(/assets/img/x.png), not social/ previews
REFERENCE = re.compile(r'((?:src="|poster="|url\(["\']?)/assets/img/)([A-Za-z0-9_-]+)\.(jpg|png)\b')


def convert(source):
    target = source.with_suffix('.webp')
    with Image.open(source) as im:
        im.load()
        limit = MAX_WIDTH.get(source.name)
        if limit and im.width > limit:
            im = im.resize((limit, round(im.height * limit / im.width)), Image.LANCZOS)
        if im.mode not in ('RGB', 'RGBA'):
            im = im.convert('RGBA' if 'transparency' in im.info or im.mode in ('LA', 'P') else 'RGB')
        im.save(target, 'WEBP', quality=QUALITY, method=6)
    return target


def main():
    made = {}
    for source in sorted(IMG.glob('*')):
        if source.suffix.lower() in ('.jpg', '.png') and source.name not in SKIP:
            target = convert(source)
            made[source.stem] = (source.stat().st_size, target.stat().st_size)
            print(f'{source.name:32} {source.stat().st_size // 1024:5} KB -> {target.stat().st_size // 1024:5} KB')

    def swap(m):
        return f'{m.group(1)}{m.group(2)}.webp' if m.group(2) in made else m.group(0)

    for page in PAGES:
        text = page.read_text(encoding='utf-8')
        new = REFERENCE.sub(swap, text)
        if new != text:
            page.write_bytes(new.encode('utf-8'))
            print('updated', page.relative_to(ROOT))


if __name__ == '__main__':
    main()
