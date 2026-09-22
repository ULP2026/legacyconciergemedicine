"""Add structured data (schema.org JSON-LD) to the Legacy pages.

Run from the project root. Re-running replaces the blocks it wrote before, so it
is safe to run again after copy changes.
"""
import json
import re
from pathlib import Path

SITE = 'https://www.legacyconciergemedicine.com'
PRACTICE_ID = f'{SITE}/#practice'
MARK_OPEN = '  <!-- Structured data for search engines -->\n'

CITIES = ['Sarasota', 'Venice', 'North Port', 'Longboat Key', 'Anna Maria', 'Bradenton',
          'Bradenton Beach', 'Cortez', 'Ellenton', 'Holmes Beach', 'Lakewood Ranch',
          'Myakka City', 'Palmetto', 'Parrish']

practice = {
    '@context': 'https://schema.org',
    # Physician is schema.org's type for a medical practice; it is a MedicalBusiness
    # and a MedicalOrganization, so it carries medicalSpecialty and availableService.
    '@type': ['MedicalBusiness', 'Physician'],
    '@id': PRACTICE_ID,
    'name': 'Legacy Concierge Medicine',
    'legalName': 'Legacy Concierge Medicine, PLLC',
    'description': ('Relationship-based, in-home concierge primary care for adults and families '
                    'across Sarasota and Manatee Counties, Southwest Florida.'),
    'url': SITE + '/',
    'logo': f'{SITE}/assets/img/logo-main.png',
    'image': f'{SITE}/assets/img/hero-09.jpg',
    'telephone': '+1-941-401-1001',
    'email': 'info@legacyconciergemedicine.com',
    'address': {
        '@type': 'PostalAddress',
        'addressLocality': 'Sarasota',
        'addressRegion': 'FL',
        'addressCountry': 'US',
    },
    'medicalSpecialty': ['PrimaryCare', 'Geriatric'],
    'openingHoursSpecification': [{
        '@type': 'OpeningHoursSpecification',
        'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        'opens': '08:00',
        'closes': '17:00',
    }],
    'areaServed': [{'@type': 'City', 'name': c,
                    'containedInPlace': {'@type': 'State', 'name': 'Florida'}} for c in CITIES],
    'availableService': [
        {'@type': 'MedicalTherapy', 'name': 'In-home primary care visits'},
        {'@type': 'MedicalTherapy', 'name': 'Preventive and longevity-focused care planning'},
        {'@type': 'MedicalTherapy', 'name': 'Continuity of care through assisted living and skilled nursing'},
    ],
    'founder': {'@type': 'Person', 'name': 'Pamela Chapman, DO', 'url': f'{SITE}/about#dr-chapman'},
    'employee': [
        {
            '@type': 'Person',
            'name': 'Pamela Chapman, DO',
            'honorificSuffix': 'DO',
            'jobTitle': 'Founder and Physician',
            'url': f'{SITE}/about#dr-chapman',
        },
        {
            '@type': 'Person',
            'name': 'Emily Smith, APRN, FNP-C',
            'honorificSuffix': 'APRN, FNP-C',
            'jobTitle': 'Nurse Practitioner',
            'url': f'{SITE}/about#emily',
        },
    ],
}

website = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    '@id': f'{SITE}/#website',
    'name': 'Legacy Concierge Medicine',
    'url': SITE + '/',
    'publisher': {'@id': PRACTICE_ID},
}


def block(objects):
    out = MARK_OPEN
    for obj in objects:
        out += '  <script type="application/ld+json">\n'
        out += json.dumps(obj, indent=2, ensure_ascii=False) + '\n'
        out += '  </script>\n'
    return out


def strip_blocks(s, types):
    """Drop JSON-LD blocks of these @types so re-runs replace rather than duplicate.

    Blocks of any other type are left alone, such as the home page's own FAQ,
    which was written by hand and matches the FAQ shown on that page.
    """
    def drop(m):
        try:
            data = json.loads(m.group(1))
        except ValueError:
            return m.group(0)
        found = data.get('@type')
        found = found if isinstance(found, list) else [found]
        return '' if any(t in types for t in found) else m.group(0)

    s = re.sub(r'[ \t]*<script type="application/ld\+json">(.*?)</script>\n', drop, s, flags=re.S)
    return s.replace(MARK_OPEN, '')


def write(path, objects):
    p = Path(path)
    s = p.read_text(encoding='utf-8')
    types = set()
    for o in objects:
        t = o['@type']
        types.update(t if isinstance(t, list) else [t])
    s = strip_blocks(s, types)
    s = s.replace('</head>', block(objects) + '</head>', 1)
    p.write_text(s, encoding='utf-8', newline='\n')
    print(f'  {path}: {", ".join(o["@type"] if isinstance(o["@type"], str) else "/".join(o["@type"]) for o in objects)}')


def ref(name, url, crumbs=None):
    """A light page-level node pointing back at the practice."""
    return {
        '@context': 'https://schema.org',
        '@type': 'WebPage',
        'name': name,
        'url': url,
        'isPartOf': {'@id': f'{SITE}/#website'},
        'about': {'@id': PRACTICE_ID},
    }


def faq_page(pairs, url):
    return {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        '@id': url + '#faq',
        'mainEntity': [{
            '@type': 'Question',
            'name': q,
            'acceptedAnswer': {'@type': 'Answer', 'text': a},
        } for q, a in pairs],
    }


def breadcrumbs(items):
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [{
            '@type': 'ListItem', 'position': i + 1, 'name': name, 'item': url,
        } for i, (name, url) in enumerate(items)],
    }


def text_from_html(fragment):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', fragment)).strip()


def services_faqs():
    s = Path('services.html').read_text(encoding='utf-8')
    section = s[s.index('id="faq"'):s.index('</section>', s.index('id="faq"'))]
    pairs = []
    for m in re.finditer(r'<summary>(.*?)</summary>.*?<div class="answer">(.*?)</div>', section, re.S):
        pairs.append((text_from_html(m.group(1)), text_from_html(m.group(2))))
    return pairs


def main():
    print('Structured data:')
    write('index.html', [practice, website])
    write('about.html', [ref('About Legacy Concierge Medicine', f'{SITE}/about'),
                         breadcrumbs([('Home', SITE + '/'), ('Our Team', f'{SITE}/about')])])
    faqs = services_faqs()
    write('services.html', [ref('The Practice', f'{SITE}/services'),
                            breadcrumbs([('Home', SITE + '/'), ('The Practice', f'{SITE}/services')]),
                            faq_page(faqs, f'{SITE}/services')])
    write('contact.html', [ref('Request a Consultation', f'{SITE}/contact'),
                           breadcrumbs([('Home', SITE + '/'), ('Contact', f'{SITE}/contact')])])
    print(f'  ({len(faqs)} FAQs on the services page)')


if __name__ == '__main__':
    main()
