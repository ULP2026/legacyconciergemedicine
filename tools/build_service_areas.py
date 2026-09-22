"""Build the service-area pages from the Claude Design exports.

    python tools/build_service_areas.py

Reads the standalone exports in design/service-areas/ (Service-Areas.html and
one Service-Area-<City>.html per community), pulls each page's content out of
its template, and writes:

    service-areas.html                 the overview (/service-areas)
    service-areas/<slug>.html          one page per community (/service-areas/<slug>)
    assets/map/service-map.html        the shared Leaflet map, framed by every page

The top bar, mobile menu and footer are copied from contact.html, so they stay
identical to the rest of the site. Re-run this after a new export; the city
pages all share one layout, so only their content comes from the export.
"""

import base64
import gzip
import hashlib
import html
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / 'design' / 'service-areas'
SITE = 'https://www.legacyconciergemedicine.com'
CSS_VERSION = '20260922'

# Canvas slug (Service-Area-<Slug>.dc.html) -> URL slug
def url_slug(canvas_slug):
    return canvas_slug.lower()

# Images the exports embed, matched to files already in assets/img by content.
# The island photo ships as a 1.8 MB PNG; the site uses a JPEG copy of it.
IMAGE_OVERRIDES = {
    '6d277eaa66': 'couple-sunset-beach.jpg',
}


# ---------------------------------------------------------------------------
# Unpacking a Claude Design bundle
# ---------------------------------------------------------------------------

def _bundle_tag(text, name):
    opener = f'<script type="__bundler/{name}">'
    start = text.index(opener) + len(opener)
    return text[start:text.index('</script>', start)]


def unpack(path):
    """Return (template_html, {uuid: bytes}) for a standalone export."""
    text = path.read_text(encoding='utf-8')
    manifest = json.loads(_bundle_tag(text, 'manifest'))
    template = json.loads(_bundle_tag(text, 'template'))
    assets = {}
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry['data'])
        if entry.get('compressed'):
            data = gzip.decompress(data)
        assets[uuid] = data
    return template, assets


def image_for(uuid, assets, library):
    digest = hashlib.sha1(assets[uuid]).hexdigest()[:10]
    if digest in IMAGE_OVERRIDES:
        return IMAGE_OVERRIDES[digest]
    if digest in library:
        return library[digest]
    raise SystemExit(f'New image in the export ({digest}); add it to assets/img or IMAGE_OVERRIDES.')


def image_library():
    lib = {}
    for f in (ROOT / 'assets' / 'img').iterdir():
        if f.is_file():
            lib[hashlib.sha1(f.read_bytes()).hexdigest()[:10]] = f.name
    return lib


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def esc(text):
    return html.escape(text, quote=False)


def attr(text):
    return html.escape(text, quote=True)


def text_of(node):
    return re.sub(r'\s+', ' ', node.get_text()).strip()


def body_of(template):
    return BeautifulSoup(template[template.index('</helmet>') + len('</helmet>'):], 'html.parser')


def map_focus(iframe):
    doc = html.unescape(iframe['srcdoc'])
    focus = json.loads(re.search(r'var focus = ([^;]+);', doc).group(1))
    return url_slug(focus) if focus else None


def map_data(iframe):
    doc = html.unescape(iframe['srcdoc'])
    cities = re.search(r'var CITIES = (\{.*?\});', doc, re.S).group(1)
    nearby = re.search(r'var NEARBY = (\{.*?\});', doc, re.S).group(1)
    return cities, nearby


def svg_inner(svg):
    return ''.join(str(c) for c in svg.children if getattr(c, 'name', None))


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_city(path, library):
    template, assets = unpack(path)
    soup = body_of(template)
    root = soup.find('div', attrs={'data-screen-label': True})
    sections = root.find_all('section', recursive=False)
    hero, care, hoods, why, continuity, nearby, faq = sections

    img = hero.find('img')
    copy = hero.find('div', style=re.compile('max-width:680px'))
    d = {
        'canvas_slug': path.stem.replace('Service-Area-', ''),
        'name': text_of(hero.find('nav').find_all('span')[-1]),
        'hero_img': image_for(img['src'], assets, library),
        'hero_alt': img.get('alt', ''),
        'hero_pos': re.search(r'object-position:([^;]+)', img['style']).group(1).strip(),
        'county': text_of(copy.find('div')),
        'h1': text_of(copy.find('h1')),
        'intro': text_of(copy.find('p')),
    }

    left, card = care.find('div').find_all('div', recursive=False)
    d['care_eyebrow'] = text_of(left.find('span'))
    d['care_h2'] = text_of(left.find('h2'))
    d['care_ps'] = [text_of(p) for p in left.find_all('p')]
    d['glance_title'] = text_of(card.find('div', style=re.compile('letter-spacing:0.18em')))
    d['glance'] = [(text_of(r.find_all('span')[0]), text_of(r.find_all('span')[1]))
                   for r in card.find_all('div', class_='lcm-glance-row')]
    d['glance_cta'] = text_of(card.find('a'))

    d['hoods_eyebrow'] = text_of(hoods.find('div', style=re.compile('letter-spacing:0.22em')))
    d['hoods_h2'] = text_of(hoods.find('h2'))
    d['hoods'] = [text_of(s) for s in hoods.find('div', style=re.compile('flex-wrap:wrap')).find_all('span')]
    d['hoods_note'] = text_of(hoods.find('p'))

    d['why_eyebrow'] = text_of(why.find('div', style=re.compile('letter-spacing:0.22em')))
    d['why_h2'] = text_of(why.find('h2'))
    d['why_cards'] = [{'icon': svg_inner(c.find('svg')), 'title': text_of(c.find('h3')), 'body': text_of(c.find('p'))}
                      for c in why.find('div', style=re.compile('grid-template-columns')).find_all('div', recursive=False)]

    d['cont_eyebrow'] = text_of(continuity.find('div', style=re.compile('letter-spacing:0.22em')))
    d['cont_quote'] = text_of(continuity.find('p'))
    d['cont_links'] = [text_of(a) for a in continuity.find_all('a')]

    iframe = nearby.find('iframe')
    d['nearby_label'] = text_of(nearby.find('div', style=re.compile('letter-spacing:0.22em')))
    d['map_title'] = iframe.get('title', '')
    d['map_focus'] = map_focus(iframe)
    d['map_note'] = text_of(nearby.find('p'))

    d['faq_eyebrow'] = text_of(faq.find('div', style=re.compile('letter-spacing:0.22em')))
    d['faq_h2'] = text_of(faq.find('h2'))
    script = template[template.index('class Component'):]
    d['faq'] = json.loads(re.search(r'const faq = (\[.*?\]);', script, re.S).group(1))

    cta = root.find('dc-import', attrs={'name': 'CtaBand'})
    d['cta'] = {k: cta[k] for k in ('eyebrow', 'title', 'body')}
    d['slug'] = url_slug(d['canvas_slug'])
    return d


def extract_overview(path):
    template, _ = unpack(path)
    soup = body_of(template)
    root = soup.find('div', attrs={'data-screen-label': True})
    header, communities, why = root.find_all('section', recursive=False)

    left, card = header.find('div').find_all('div', recursive=False)
    d = {
        'eyebrow': text_of(left.find('div')),
        'h1': text_of(left.find('h1')),
        'intro': text_of(left.find('p')),
        'button': text_of(left.find('x-import')),
    }
    lines = card.find('div', style=re.compile('position:relative')).find_all('div', recursive=False)
    d['card_eyebrow'] = text_of(lines[0])
    d['card_title'] = [text_of(BeautifulSoup(part, 'html.parser')) for part in re.split(r'<br\s*/?>', lines[1].decode_contents())]
    d['card_pill'] = text_of(lines[2])

    head = communities.find('div', style=re.compile('text-align:center'))
    d['list_eyebrow'] = text_of(head.find('div'))
    d['list_h2'] = text_of(head.find('h2'))
    iframe = communities.find('iframe')
    d['map_title'] = iframe.get('title', '')
    d['map_cities'], d['map_nearby'] = map_data(iframe)
    counties = []
    grid = iframe.find_next_sibling('div')
    for col in grid.find_all('div', recursive=False):
        spans = col.find('div').find_all('span')
        links = [(text_of(a.contents[0]) if a.contents else text_of(a),
                  url_slug(re.search(r'Service-Area-(.+)\.dc\.html', a['href']).group(1)))
                 for a in col.find_all('a')]
        counties.append({'name': text_of(spans[0]), 'count': text_of(spans[1]), 'links': links})
    d['counties'] = counties
    d['list_note'] = text_of(communities.find_all('p')[-1])
    d['why'] = [{'title': text_of(b.find('h3')), 'body': text_of(b.find('p'))}
                for b in why.find('div').find_all('div', recursive=False)]
    cta = root.find('dc-import', attrs={'name': 'CtaBand'})
    d['cta'] = {k: cta[k] for k in ('eyebrow', 'title', 'body')}
    return d


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


PRACTICE_ID = SITE + '/#practice'


def breadcrumbs(items):
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u}
                            for i, (n, u) in enumerate(items)],
    }


def city_schema(d):
    """Breadcrumbs, the page's FAQs, and the practice serving this community."""
    url = f"{SITE}/service-areas/{d['slug']}"
    return [
        breadcrumbs([('Home', SITE + '/'), ('Service Areas', f'{SITE}/service-areas'), (d['name'], url)]),
        {
            '@context': 'https://schema.org',
            '@type': 'FAQPage',
            '@id': url + '#faq',
            'mainEntity': [{'@type': 'Question', 'name': q,
                            'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in d['faq']],
        },
        {
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            'name': d['h1'],
            'url': url,
            'about': {
                '@type': ['MedicalBusiness', 'Physician'],
                '@id': PRACTICE_ID,
                'name': 'Legacy Concierge Medicine',
                'telephone': '+1-941-401-1001',
                'areaServed': {'@type': 'City', 'name': d['name'],
                               'containedInPlace': {'@type': 'State', 'name': 'Florida'}},
            },
        },
    ]


def overview_schema(d):
    url = f'{SITE}/service-areas'
    cities = [name for c in d['counties'] for name, _ in c['links']]
    return [
        breadcrumbs([('Home', SITE + '/'), ('Service Areas', url)]),
        {
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            'name': 'Service Areas',
            'url': url,
            'about': {
                '@type': ['MedicalBusiness', 'Physician'],
                '@id': PRACTICE_ID,
                'name': 'Legacy Concierge Medicine',
                'telephone': '+1-941-401-1001',
                'areaServed': [{'@type': 'City', 'name': n,
                                'containedInPlace': {'@type': 'State', 'name': 'Florida'}}
                               for n in dict.fromkeys(cities)],
            },
        },
    ]


def site_chrome():
    """Top bar + mobile menu, and footer, from contact.html with Service Areas marked current."""
    page = (ROOT / 'contact.html').read_text(encoding='utf-8')
    before = page[page.index('<body>') + len('<body>'):page.index('  <main>')]
    after = page[page.index('  </main>') + len('  </main>'):page.index('  <script src="/assets/js/main.js')]
    marker = '<li class="has-menu">\n            <a href="/service-areas">'
    if marker not in before:
        raise SystemExit('Could not find the Service Areas menu item in contact.html')
    before = before.replace(marker, marker.replace('has-menu', 'has-menu is-current'), 1)
    return before, after


def head(title, description, path, image, schema=()):
    url = SITE + path
    blocks = ''
    if schema:
        blocks = '  <!-- Structured data for search engines -->\n'
        for obj in schema:
            blocks += '  <script type="application/ld+json">\n'
            blocks += json.dumps(obj, indent=2, ensure_ascii=False) + '\n'
            blocks += '  </script>\n'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Google Analytics 4 -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-GP4YR58GRS"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-GP4YR58GRS');
  </script>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{attr(description)}">
  <link rel="canonical" href="{url}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{attr(title)}">
  <meta property="og:description" content="{attr(description)}">
  <meta property="og:url" content="{url}">
  <meta property="og:site_name" content="Legacy Concierge Medicine">
  <meta property="og:locale" content="en_US">
  <meta property="og:image" content="{SITE}/assets/img/social/{Path(image).stem}.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="/favicon.ico" sizes="any">
  <link rel="icon" href="/assets/img/favicon.png" type="image/png">
  <link rel="apple-touch-icon" href="/assets/img/favicon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/css/style.css?v=20260911">
  <link rel="stylesheet" href="/assets/css/chrome.css?v={CSS_VERSION}">
  <link rel="stylesheet" href="/assets/css/service-areas.css?v={CSS_VERSION}">
{blocks}</head>
<body>
'''


def cta_band(cta):
    return f'''  <section class="lcm-cta">
    <img src="/assets/img/stamp.png" alt="" width="400" height="400" loading="lazy">
    <div class="inner">
      <span class="eyebrow">{esc(cta['eyebrow'])}</span>
      <h2>{esc(cta['title'])}</h2>
      <p>{esc(cta['body'])}</p>
      <div class="btns">
        <a class="solid" href="/contact">Request a consultation</a>
        <a class="ghost" href="tel:+19414011001">(941) 401-1001</a>
      </div>
    </div>
  </section>
'''


def page(doc_head, chrome, main):
    before, after = chrome
    return (doc_head + before + '  <main class="sa-page">\n' + main + '\n  </main>' + after
            + '  <script src="/assets/js/main.js?v=20260911" defer></script>\n</body>\n</html>\n')


def render_city(d, chrome):
    glance = '\n'.join(
        f'            <div class="sa-glance-row"><span>{esc(k)}</span><span>{esc(v)}</span></div>'
        for k, v in d['glance'])
    hoods = '\n'.join(f'          <li>{esc(h)}</li>' for h in d['hoods'])
    cards = '\n'.join(f'''        <article class="sa-card">
          <span class="sa-card-icon" aria-hidden="true"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{c['icon']}</svg></span>
          <h3>{esc(c['title'])}</h3>
          <p>{esc(c['body'])}</p>
        </article>''' for c in d['why_cards'])
    faqs = '\n'.join(f'''      <details class="sa-faq">
        <summary><span>{esc(q)}</span><span class="sign" aria-hidden="true"></span></summary>
        <p>{esc(a)}</p>
      </details>''' for q, a in d['faq'])
    focus = f'?focus={d["map_focus"]}' if d['map_focus'] else ''
    main = f'''
    <section class="sa-hero">
      <img src="/assets/img/{d['hero_img']}" alt="{attr(d['hero_alt'])}" style="object-position:{d['hero_pos']}" fetchpriority="high">
      <div class="shade" aria-hidden="true"></div>
      <div class="sa-hero-inner">
        <nav class="sa-crumbs" aria-label="Breadcrumb">
          <a href="/">Home</a><span aria-hidden="true">/</span>
          <a href="/service-areas">Service Areas</a><span aria-hidden="true">/</span>
          <span aria-current="page">{esc(d['name'])}</span>
        </nav>
        <div class="sa-hero-copy">
          <span class="sa-eyebrow on-dark">{esc(d['county'])}</span>
          <h1>{esc(d['h1'])}</h1>
          <p>{esc(d['intro'])}</p>
          <div class="sa-hero-cta">
            <a class="sa-btn sa-btn-solid" href="/contact">Request a Consultation</a>
            <a class="sa-btn sa-btn-glass" href="tel:+19414011001">(941) 401-1001</a>
          </div>
        </div>
      </div>
    </section>

    <section class="sa-section sa-white">
      <div class="sa-wrap sa-care">
        <div>
          <span class="sa-eyebrow">{esc(d['care_eyebrow'])}</span>
          <h2>{esc(d['care_h2'])}</h2>
          <p>{esc(d['care_ps'][0])}</p>
          <p class="muted">{esc(d['care_ps'][1])}</p>
        </div>
        <aside class="sa-glance">
          <img src="/assets/img/stamp.png" alt="" width="400" height="400" loading="lazy">
          <div class="inner">
            <div class="title">{esc(d['glance_title'])}</div>
{glance}
            <a class="sa-glance-cta" href="/contact">{esc(d['glance_cta'])}</a>
          </div>
        </aside>
      </div>
    </section>

    <section class="sa-section sa-cream sa-hoods">
      <div class="sa-narrow">
        <span class="sa-eyebrow">{esc(d['hoods_eyebrow'])}</span>
        <h2>{esc(d['hoods_h2'])}</h2>
        <ul class="sa-chips">
{hoods}
        </ul>
        <p class="sa-note">{esc(d['hoods_note'])}</p>
      </div>
    </section>

    <section class="sa-section sa-white">
      <div class="sa-wrap">
        <div class="sa-head-left">
          <span class="sa-eyebrow">{esc(d['why_eyebrow'])}</span>
          <h2>{esc(d['why_h2'])}</h2>
        </div>
        <div class="sa-cards">
{cards}
        </div>
      </div>
    </section>

    <section class="sa-continuity">
      <img src="/assets/img/stamp.png" alt="" width="400" height="400" loading="lazy">
      <div class="inner">
        <span class="sa-eyebrow on-dark">{esc(d['cont_eyebrow'])}</span>
        <p class="sa-quote">{esc(d['cont_quote'])}</p>
        <div class="btns">
          <a class="sa-btn sa-btn-light" href="/services#continuity">{esc(d['cont_links'][0])}</a>
          <a class="sa-btn sa-btn-outline" href="/services#membership">{esc(d['cont_links'][1])}</a>
        </div>
      </div>
    </section>

    <section class="sa-section sa-cream sa-nearby">
      <div class="sa-wrap sa-wrap-md">
        <span class="sa-eyebrow muted">{esc(d['nearby_label'])}</span>
        <iframe class="sa-map" src="/assets/map/service-map{focus}" title="{attr(d['map_title'])}" loading="lazy"></iframe>
        <p class="sa-map-note">{esc(d['map_note'])}</p>
      </div>
    </section>

    <section class="sa-section sa-white">
      <div class="sa-faqs">
        <div class="sa-head-center">
          <span class="sa-eyebrow">{esc(d['faq_eyebrow'])}</span>
          <h2>{esc(d['faq_h2'])}</h2>
        </div>
{faqs}
      </div>
    </section>

{cta_band(d['cta'])}'''
    title = f"{d['h1']} | Legacy Concierge Medicine"
    return page(head(title, d['intro'], f"/service-areas/{d['slug']}", d['hero_img'], city_schema(d)), chrome, main)


def render_overview(d, chrome):
    counties = []
    for c in d['counties']:
        links = '\n'.join(f'            <a href="/service-areas/{slug}">{esc(name)}<span aria-hidden="true">&rarr;</span></a>'
                          for name, slug in c['links'])
        counties.append(f'''        <div>
          <div class="sa-county"><span class="name">{esc(c['name'])}</span><span class="count">{esc(c['count'])}</span></div>
          <div class="sa-county-links">
{links}
          </div>
        </div>''')
    why = '\n'.join(f'''      <div class="sa-local">
        <div class="rule" aria-hidden="true"></div>
        <h3>{esc(w['title'])}</h3>
        <p>{esc(w['body'])}</p>
      </div>''' for w in d['why'])
    card_title = '<br>'.join(esc(t) for t in d['card_title'])
    main = f'''
    <section class="sa-overview-head">
      <div class="sa-wrap sa-split">
        <div>
          <span class="sa-eyebrow">{esc(d['eyebrow'])}</span>
          <h1>{esc(d['h1'])}</h1>
          <p>{esc(d['intro'])}</p>
          <a class="sa-btn sa-btn-solid sa-btn-lg" href="/contact">{esc(d['button'])}</a>
        </div>
        <div class="sa-serving">
          <img src="/assets/img/stamp.png" alt="" width="400" height="400">
          <div class="inner">
            <div class="label">{esc(d['card_eyebrow'])}</div>
            <div class="title">{card_title}</div>
            <div class="pill">{esc(d['card_pill'])}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="sa-section sa-white sa-communities">
      <div class="sa-wrap sa-wrap-md">
        <div class="sa-head-center">
          <span class="sa-eyebrow">{esc(d['list_eyebrow'])}</span>
          <h2>{esc(d['list_h2'])}</h2>
        </div>
        <iframe class="sa-map sa-map-lg" src="/assets/map/service-map" title="{attr(d['map_title'])}" loading="lazy"></iframe>
        <div class="sa-counties">
{chr(10).join(counties)}
        </div>
        <p class="sa-note">{esc(d['list_note'])}</p>
      </div>
    </section>

    <section class="sa-section sa-cream sa-locals-section">
      <div class="sa-wrap sa-wrap-md sa-locals">
{why}
      </div>
    </section>

{cta_band(d['cta'])}'''
    return page(head('Service Areas | Legacy Concierge Medicine', d['intro'], '/service-areas', 'couple-shore.jpg',
                     overview_schema(d)), chrome, main)


def render_map(cities, nearby):
    # Canvas keys are Title-Case slugs; the site's URLs are lower-case.
    cities = re.sub(r"'([A-Za-z-]+)':(\s*)\{", lambda m: f"'{m.group(1).lower()}':{m.group(2)}{{", cities)
    nearby = re.sub(r"'([A-Za-z-]+)'", lambda m: f"'{m.group(1).lower()}'", nearby)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Legacy Service Area Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha384-sHL9NAb7lN7rfvG5lfHpm643Xkcjzp4jFvuavGOndn6pjVqS6ny56CAt3nsEVT4H" crossorigin="anonymous">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha384-cxOPjt7s7Iz04uaHJceBmS+qpjv2JkIHNVcuOrM+YHwZOmJGBXI00mdUXEq65HTH" crossorigin="anonymous"></script>
<style>
  html,body{{margin:0;padding:0;height:100%;background:#EFECEA;}}
  .leaflet-container{{background:#EFECEA;font-family:Inter,Helvetica,Arial,sans-serif;}}
  .leaflet-tile-pane{{filter:grayscale(0.55) sepia(0.2) saturate(0.9) brightness(1.04) contrast(0.92);}}
  .leaflet-control-zoom a{{color:#1C1918;border-color:#DBD5CE;}}
  .leaflet-control-attribution{{background:rgba(239,236,234,0.85);color:#7F756E;font-size:10px;}}
  .leaflet-control-attribution a{{color:#71140C;}}
  #map{{width:100%;height:100%;}}
  .lcm-tip{{font-family:Georgia,"Times New Roman",serif;font-size:13px;color:#1C1918;background:#fff;border:1px solid #DBD5CE;border-radius:4px;box-shadow:0 6px 18px rgba(28,25,24,0.12);padding:4px 9px;}}
  .lcm-tip.focus{{background:#71140C;color:#EFECEA;border-color:#71140C;font-size:14px;}}
  .leaflet-popup-content-wrapper{{border-radius:6px;font-family:Georgia,serif;}}
  .leaflet-popup-content{{margin:12px 16px;font-size:14px;color:#1C1918;}}
  .leaflet-popup-content a{{color:#71140C;text-decoration:none;font-weight:600;}}
</style>
</head>
<body>
<div id="map" aria-label="Map of Legacy Concierge Medicine service areas"></div>
<script>
/* Generated by tools/build_service_areas.py from the design exports.
   ?focus=<slug> centres the map on one community and its nearby areas. */
(function(){{
  var CITIES = {cities};
  var NEARBY = {nearby};
  var focus = new URLSearchParams(location.search).get('focus');
  if (focus && !CITIES[focus]) focus = null;

  var map = L.map('map', {{ scrollWheelZoom:false, zoomControl:true, attributionControl:true }});
  /* CARTO's basemaps (used on the canvas) now watermark every tile without a paid key,
     so the site uses OpenStreetMap's standard tiles, muted by the filter above. */
  L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors' }}).addTo(map);

  function marker(slug, isFocus){{
    var c = CITIES[slug];
    var m = L.circleMarker(c.ll, {{
      radius: isFocus ? 11 : 7,
      color: '#ffffff', weight: 2,
      fillColor: isFocus ? '#4A0D07' : '#71140C', fillOpacity: 1
    }}).addTo(map);
    m.bindTooltip(c.n, {{ permanent: !!focus, direction: 'top', offset: [0, isFocus ? -12 : -8], className: 'lcm-tip' + (isFocus ? ' focus' : '') }});
    m.bindPopup('<a href="/service-areas/' + slug + '" target="_top">' + c.n + ' &rarr;</a>');
    return m;
  }}

  var shown = [];
  if (focus) {{
    L.circle(CITIES[focus].ll, {{ radius: 8000, color: '#71140C', weight: 1, opacity: 0.25, fillColor: '#71140C', fillOpacity: 0.07 }}).addTo(map);
    shown.push(marker(focus, true));
    (NEARBY[focus] || []).forEach(function(s){{ shown.push(marker(s, false)); }});
  }} else {{
    Object.keys(CITIES).forEach(function(s){{ shown.push(marker(s, false)); }});
  }}
  map.fitBounds(L.featureGroup(shown).getBounds(), {{ padding: [46, 46] }});
}})();
</script>
</body>
</html>
'''


def main():
    library = image_library()
    chrome = site_chrome()

    overview = extract_overview(DESIGN / 'Service-Areas.html')
    (ROOT / 'service-areas.html').write_text(render_overview(overview, chrome), encoding='utf-8', newline='\n')

    out = ROOT / 'service-areas'
    out.mkdir(exist_ok=True)
    slugs = []
    for path in sorted(DESIGN.glob('Service-Area-*.html')):
        d = extract_city(path, library)
        (out / f"{d['slug']}.html").write_text(render_city(d, chrome), encoding='utf-8', newline='\n')
        slugs.append(d['slug'])
        print(f"  service-areas/{d['slug']}.html  ({d['name']}, {len(d['hoods'])} neighborhoods, {len(d['faq'])} FAQs, photo {d['hero_img']})")

    mapdir = ROOT / 'assets' / 'map'
    mapdir.mkdir(parents=True, exist_ok=True)
    (mapdir / 'service-map.html').write_text(render_map(overview['map_cities'], overview['map_nearby']),
                                             encoding='utf-8', newline='\n')
    print(f'Wrote service-areas.html, {len(slugs)} community pages and assets/map/service-map.html')


if __name__ == '__main__':
    main()
