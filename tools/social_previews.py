"""Build the link-preview images and keep the sharing tags in step.

    python tools/social_previews.py

Facebook, LinkedIn, iMessage, WhatsApp and X all read the og: tags. They want a
landscape image around 1200x630; the site's own photos are various shapes, so
this crops a 1200x630 copy of each one into assets/img/social/ and points the
tags there. It also adds the twitter:card tags and gives the legal, thank-you
and 404 pages the sharing tags they were missing.

Re-run after changing a page's photo or copy. The service-area pages get their
tags from tools/build_service_areas.py instead.
"""
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://www.legacyconciergemedicine.com'
OUT = ROOT / 'assets' / 'img' / 'social'
W, H = 1200, 630

# source photo -> vertical focus (0 = top of the photo, 1 = bottom)
SOURCES = {
    'hero-09.jpg': 0.5,
    'photo-11.jpg': 0.5,
    'photo-2.jpg': 0.5,
    'bellagena-spring-2026.jpg': 0.22,   # portrait of Dr. Chapman; keep the face
    'couple-shore.jpg': 0.45,
    'family-home.jpg': 0.5,
    'photo-5.jpg': 0.5,
    'couple-sunset-beach.jpg': 0.45,
}

# page -> source photo used for its preview
PAGES = {
    'index.html': 'hero-09.jpg',
    'about.html': 'bellagena-spring-2026.jpg',
    'services.html': 'photo-11.jpg',
    'contact.html': 'photo-2.jpg',
    'thank-you.html': 'hero-09.jpg',
    '404.html': 'hero-09.jpg',
    'privacy-policy.html': 'hero-09.jpg',
    'terms-and-conditions.html': 'hero-09.jpg',
    'disclaimer.html': 'hero-09.jpg',
}

# pages that had no sharing tags: title and description to give them
FALLBACK_TAGS = {
    'thank-you.html': ('Thank You | Legacy Concierge Medicine',
                       'We have received your information and will reach out to you soon.'),
    '404.html': ('Page Not Found | Legacy Concierge Medicine',
                 'This page has moved on. Explore the practice, our team, or request a private consultation.'),
    'privacy-policy.html': ('Privacy Policy | Legacy Concierge Medicine',
                            'How Legacy Concierge Medicine collects, stores, and protects the information you share with us.'),
    'terms-and-conditions.html': ('Terms & Conditions | Legacy Concierge Medicine',
                                  'The terms that apply when you use the Legacy Concierge Medicine website.'),
    'disclaimer.html': ('Disclaimer | Legacy Concierge Medicine',
                        'The website is for general information and is not medical advice. In an emergency, call 911.'),
}


def crop(name, focus):
    """Centre-crop to 1200x630 around the given vertical focus."""
    src = Image.open(ROOT / 'assets' / 'img' / name).convert('RGB')
    scale = max(W / src.width, H / src.height)
    resized = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    left = (resized.width - W) // 2
    top = min(max(round(resized.height * focus - H / 2), 0), resized.height - H)
    out = OUT / (Path(name).stem + '.jpg')
    resized.crop((left, top, left + W, top + H)).save(out, quality=82, optimize=True, progressive=True)
    return out


def set_meta(s, attr, key, value):
    """Set a meta tag, adding it after the description if it is missing."""
    pattern = re.compile(rf'(<meta {attr}="{re.escape(key)}" content=")[^"]*(")')
    if pattern.search(s):
        return pattern.sub(lambda m: m.group(1) + value + m.group(2), s, count=1)
    anchor = re.search(r'[ \t]*<meta name="description"[^>]*>\n', s)
    if not anchor:
        anchor = re.search(r'[ \t]*<title>[^<]*</title>\n', s)
    insert = f'  <meta {attr}="{key}" content="{value}">\n'
    return s[:anchor.end()] + insert + s[anchor.end():]


def page_url(path):
    name = Path(path).stem
    return SITE + ('/' if name == 'index' else f'/{name}')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print('Preview images (1200x630):')
    for name, focus in SORTED_SOURCES:
        out = crop(name, focus)
        print(f'  assets/img/social/{out.name}  ({out.stat().st_size // 1024} KB)')

    print('Sharing tags:')
    for path, photo in PAGES.items():
        p = ROOT / path
        s = p.read_text(encoding='utf-8')
        image = f'{SITE}/assets/img/social/{Path(photo).stem}.jpg'
        added = ''
        if path in FALLBACK_TAGS:
            title, desc = FALLBACK_TAGS[path]
            s = set_meta(s, 'property', 'og:type', 'website')
            s = set_meta(s, 'property', 'og:title', title)
            s = set_meta(s, 'property', 'og:description', desc)
            s = set_meta(s, 'property', 'og:url', page_url(path))
            added = ' (tags added)'
        s = set_meta(s, 'property', 'og:site_name', 'Legacy Concierge Medicine')
        s = set_meta(s, 'property', 'og:locale', 'en_US')
        s = set_meta(s, 'property', 'og:image', image)
        s = set_meta(s, 'property', 'og:image:width', str(W))
        s = set_meta(s, 'property', 'og:image:height', str(H))
        s = set_meta(s, 'name', 'twitter:card', 'summary_large_image')
        p.write_text(s, encoding='utf-8', newline='\n')
        print(f'  {path}: {Path(photo).stem}.jpg{added}')


SORTED_SOURCES = sorted(SOURCES.items())

if __name__ == '__main__':
    main()
