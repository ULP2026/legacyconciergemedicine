"""Audit the Legacy site for the SEO and AEO problems that cost us placement.

    python tools/seo_audit.py            # check the files in this repo
    python tools/seo_audit.py --live     # also fetch every published URL
    python tools/seo_audit.py --report audit.md

SEO is what a search crawler needs: a title, a description, one h1, a canonical,
links that resolve, a sitemap that matches the pages we actually publish.

AEO is what an answer engine needs before it will quote the practice: the AI
crawlers allowed in robots.txt, an llms.txt that states the facts plainly,
structured data carrying the phone, hours and service area, and a page of real
questions with real answers.

Findings are ERROR (fix before the next deploy), WARN (worth fixing) or NOTE.
The script exits non-zero when anything is an ERROR, so CI can fail on it.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://www.legacyconciergemedicine.com'

# The AI crawlers worth naming. Blocking one of these removes the practice from
# that assistant's answers, which is the opposite of what AEO is for.
AI_AGENTS = ['GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-User',
             'PerplexityBot', 'Google-Extended', 'Applebot-Extended', 'Bingbot',
             'meta-externalagent']

# Facts that must read the same everywhere, or an answer engine picks one at random.
NAP = {
    'phone': '(941) 401-1001',
    'phone_href': 'tel:+19414011001',
    'name': 'Legacy Concierge Medicine',
}

TITLE_MIN, TITLE_MAX = 15, 65
DESC_MIN, DESC_MAX = 70, 165

findings = []


def add(level, page, message):
    findings.append((level, page, message))


def pages():
    """Every publishable HTML page in the repo, as repo-relative paths."""
    out = sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('service-areas/*.html'))
    return [p.relative_to(ROOT).as_posix() for p in out]


def url_for(path):
    if path == 'index.html':
        return SITE + '/'
    return f'{SITE}/{path[:-5]}'


def meta(soup, **attrs):
    tag = soup.find('meta', attrs=attrs)
    return (tag.get('content') or '').strip() if tag else None


def json_ld(soup):
    """Every JSON-LD object on the page, flattened out of any @graph."""
    out = []
    for tag in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(tag.string or '')
        except ValueError:
            out.append({'@type': '__unparseable__'})
            continue
        for obj in (data if isinstance(data, list) else [data]):
            if isinstance(obj, dict):
                out.extend(obj.get('@graph', [obj]))
    return out


def types_of(obj):
    t = obj.get('@type', [])
    return t if isinstance(t, list) else [t]


def check_page(path, soup, noindex):
    """The per-page checks. A noindex page skips the ones only indexed pages need."""
    title = soup.title.string.strip() if soup.title and soup.title.string else ''
    desc = meta(soup, name='description')

    if not title:
        add('ERROR', path, 'no <title>')
    elif not noindex and not TITLE_MIN <= len(title) <= TITLE_MAX:
        add('WARN', path, f'title is {len(title)} chars (aim for {TITLE_MIN}-{TITLE_MAX})')

    if desc is None:
        add('ERROR', path, 'no meta description')
    elif not noindex and not DESC_MIN <= len(desc) <= DESC_MAX:
        add('WARN', path, f'meta description is {len(desc)} chars (aim for {DESC_MIN}-{DESC_MAX})')

    html = soup.find('html')
    if not (html and html.get('lang')):
        add('ERROR', path, 'no lang attribute on <html>')
    if not soup.find('meta', attrs={'name': 'viewport'}):
        add('ERROR', path, 'no viewport meta')

    canonical = soup.find('link', rel=lambda v: v and 'canonical' in v)
    if not noindex:
        if not canonical:
            add('ERROR', path, 'no canonical link')
        elif canonical.get('href') != url_for(path):
            add('ERROR', path, f'canonical is {canonical.get("href")}, expected {url_for(path)}')

    h1s = soup.find_all('h1')
    if len(h1s) == 0:
        add('ERROR', path, 'no h1')
    elif len(h1s) > 1:
        add('WARN', path, f'{len(h1s)} h1 headings; a page should have one')

    for prop in ('og:title', 'og:description', 'og:image', 'og:url'):
        if meta(soup, property=prop) is None:
            add('WARN', path, f'no {prop} tag')
    if meta(soup, name='twitter:card') is None:
        add('WARN', path, 'no twitter:card tag')

    missing_alt = [i for i in soup.find_all('img') if i.get('alt') is None]
    if missing_alt:
        srcs = ', '.join(sorted({(i.get('src') or '?').split('/')[-1] for i in missing_alt})[:4])
        add('WARN', path, f'{len(missing_alt)} img without an alt attribute ({srcs})')

    no_dims = [i for i in soup.find_all('img') if not (i.get('width') and i.get('height'))]
    if no_dims:
        srcs = ', '.join(sorted({(i.get('src') or '?').split('/')[-1] for i in no_dims})[:4])
        add('NOTE', path, f'{len(no_dims)} img without width/height, which can shift layout ({srcs})')

    for obj in json_ld(soup):
        if '__unparseable__' in types_of(obj):
            add('ERROR', path, 'a JSON-LD block does not parse as JSON')

    return title, desc


def redirect_sources():
    cfg = json.loads((ROOT / 'vercel.json').read_text(encoding='utf-8'))
    return {r['source'].split('/:')[0] for r in cfg.get('redirects', [])}


def check_links(path, soup, redirects):
    """Internal links have to resolve to a file we publish, or a redirect we declare."""
    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:')):
            continue
        parsed = urlparse(href)
        if parsed.scheme or parsed.netloc:
            continue
        target = parsed.path.rstrip('/')
        if not target or target in redirects:
            continue
        rel = target.lstrip('/')
        if not any((ROOT / c).exists() for c in (rel, rel + '.html', rel + '/index.html')):
            add('ERROR', path, f'link to {href} does not resolve to a published page')


def check_sitemap(page_paths, noindexed):
    text = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    listed = set(re.findall(r'<loc>([^<]+)</loc>', text))

    for path in page_paths:
        url = url_for(path)
        if path in noindexed:
            if url in listed:
                add('ERROR', 'sitemap.xml', f'{url} is noindex but listed in the sitemap')
        elif path == '404.html':
            continue
        elif url not in listed:
            add('ERROR', 'sitemap.xml', f'{url} is indexable but missing from the sitemap')

    known = {url_for(p) for p in page_paths}
    for url in sorted(listed - known):
        add('ERROR', 'sitemap.xml', f'{url} is listed but no page in the repo publishes it')


def check_robots():
    text = (ROOT / 'robots.txt').read_text(encoding='utf-8')
    agents = {m.lower() for m in re.findall(r'(?im)^user-agent:\s*(.+?)\s*$', text)}
    disallowed = re.findall(r'(?im)^disallow:\s*(\S+)\s*$', text)

    if f'{SITE}/sitemap.xml' not in text:
        add('ERROR', 'robots.txt', 'does not point at the sitemap')
    if '/' in disallowed:
        add('ERROR', 'robots.txt', 'a Disallow: / rule is blocking the whole site')

    missing = [a for a in AI_AGENTS if a.lower() not in agents]
    if missing:
        add('WARN', 'robots.txt',
            'these AI crawlers are not named, so the practice relies on the wildcard rule '
            'and drops out if one of them tightens its default: ' + ', '.join(missing))


def check_llms():
    p = ROOT / 'llms.txt'
    if not p.exists():
        add('WARN', 'llms.txt',
            'missing; answer engines have to infer the practice from page markup instead '
            'of reading the facts stated plainly')
        return
    text = p.read_text(encoding='utf-8')
    for label, value in (('practice name', NAP['name']), ('phone number', NAP['phone'])):
        if value not in text:
            add('WARN', 'llms.txt', f'does not state the {label}')
    if SITE not in text:
        add('WARN', 'llms.txt', 'does not link back to the site')


def check_structured_data():
    """The home page carries the practice record an answer engine reads first."""
    soup = BeautifulSoup((ROOT / 'index.html').read_text(encoding='utf-8'), 'html.parser')
    practice = next((o for o in json_ld(soup) if 'MedicalBusiness' in types_of(o)), None)

    if not practice:
        add('ERROR', 'index.html', 'no MedicalBusiness structured data on the home page')
    else:
        for field in ('name', 'telephone', 'address', 'url', 'description',
                      'openingHoursSpecification', 'areaServed', 'availableService'):
            if not practice.get(field):
                add('WARN', 'index.html', f'practice structured data has no {field}')
        digits = re.sub(r'\D', '', practice.get('telephone') or '')
        if digits and digits[-10:] != re.sub(r'\D', '', NAP['phone']):
            add('ERROR', 'index.html',
                f'structured data phone {practice["telephone"]} does not match {NAP["phone"]}')

    faq = [o for p in ROOT.glob('*.html')
           for o in json_ld(BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser'))
           if 'FAQPage' in types_of(o)]
    if not faq:
        add('WARN', 'site', 'no FAQPage anywhere; question-and-answer markup is what '
                            'assistants quote most readily')
    else:
        total = sum(len(o.get('mainEntity', [])) for o in faq)
        add('NOTE', 'site', f'{total} questions marked up across {len(faq)} FAQ blocks')


def check_nap(page_paths):
    """One phone number, spelled one way, on every page that shows one."""
    for path in page_paths:
        # the structured data field writes it +1-941-401-1001, which is its own convention
        text = (ROOT / path).read_text(encoding='utf-8').replace('+1-941-401-1001', '')
        numbers = set(re.findall(r'\(?\b941\)?[-. ]?\d{3}[-. ]?\d{4}\b', text))
        odd = {n for n in numbers if re.sub(r'\D', '', n) != re.sub(r'\D', '', NAP['phone'])}
        if odd:
            add('ERROR', path, f'a different phone number appears: {", ".join(sorted(odd))}')
        spellings = {n for n in numbers if n != NAP['phone']} - odd
        if spellings:
            add('NOTE', path, f'the phone number is also written as {", ".join(sorted(spellings))}; '
                              f'one spelling reads better to a directory')
        for a in BeautifulSoup(text, 'html.parser').find_all('a', href=re.compile(r'^tel:')):
            if a['href'] != NAP['phone_href']:
                add('ERROR', path, f'tel: link is {a["href"]}, expected {NAP["phone_href"]}')


def check_duplicates(seen):
    for kind, values in seen.items():
        groups = {}
        for path, value in values:
            if value:
                groups.setdefault(value, []).append(path)
        for value, paths in groups.items():
            if len(paths) > 1:
                add('WARN', ', '.join(paths), f'share the same {kind}: {value[:60]!r}')


def check_live(page_paths):
    """Fetch what is actually published, so the audit is about the live site."""
    import requests

    session = requests.Session()
    session.headers['User-Agent'] = 'LegacySEOAudit/1.0'
    for path in page_paths:
        if path == '404.html':
            continue
        url = url_for(path)
        try:
            r = session.get(url, timeout=20)
        except requests.RequestException as exc:
            add('ERROR', path, f'live fetch failed: {exc.__class__.__name__}')
            continue
        if r.status_code != 200:
            add('ERROR', path, f'live URL returns {r.status_code}')
        elif r.history:
            add('NOTE', path, f'live URL redirects via {len(r.history)} hop(s)')
        kb = len(r.content) // 1024
        if kb > 120:
            add('NOTE', path, f'HTML is {kb} KB before assets')

    for name in ('robots.txt', 'sitemap.xml', 'llms.txt'):
        r = session.get(f'{SITE}/{name}', timeout=20)
        if r.status_code == 200:
            add('NOTE', name, 'live: 200')
        else:
            add('WARN' if name == 'llms.txt' else 'ERROR', name, f'live: {r.status_code}')


def main():
    ap = argparse.ArgumentParser(description='SEO and AEO audit for the Legacy site.')
    ap.add_argument('--live', action='store_true', help='also fetch every published URL')
    ap.add_argument('--report', metavar='FILE', help='write the findings to a markdown file')
    args = ap.parse_args()

    page_paths = pages()
    redirects = redirect_sources()
    noindexed = set()
    seen = {'title': [], 'meta description': []}

    for path in page_paths:
        soup = BeautifulSoup((ROOT / path).read_text(encoding='utf-8'), 'html.parser')
        noindex = 'noindex' in (meta(soup, name='robots') or '').lower()
        if noindex:
            noindexed.add(path)
        title, desc = check_page(path, soup, noindex)
        check_links(path, soup, redirects)
        if not noindex and path != '404.html':
            seen['title'].append((path, title))
            seen['meta description'].append((path, desc))

    check_duplicates(seen)
    check_sitemap(page_paths, noindexed)
    check_robots()
    check_llms()
    check_structured_data()
    check_nap(page_paths)
    if args.live:
        check_live(page_paths)

    order = {'ERROR': 0, 'WARN': 1, 'NOTE': 2}
    findings.sort(key=lambda f: (order[f[0]], f[1]))
    counts = {k: sum(1 for f in findings if f[0] == k) for k in order}

    scope = ' against the live site' if args.live else ''
    lines = [f'# SEO / AEO audit: {SITE}', '',
             f'{len(page_paths)} pages checked{scope}. '
             f'{counts["ERROR"]} errors, {counts["WARN"]} warnings, {counts["NOTE"]} notes.']
    current = None
    for level, page, message in findings:
        if level != current:
            lines += ['', f'## {level}', '']
            current = level
        lines.append(f'- **{page}** - {message}')
    text = '\n'.join(lines) + '\n'

    print(text)
    if args.report:
        Path(args.report).write_text(text, encoding='utf-8', newline='\n')
        print(f'written to {args.report}')

    return 1 if counts['ERROR'] else 0


if __name__ == '__main__':
    sys.exit(main())
