"""Write minified copies of the stylesheets and scripts, and point the pages at them.

    pip install rcssmin rjsmin
    python tools/minify_assets.py

The readable files stay exactly where they are. This writes a `.min.css` or
`.min.js` beside each one and rewrites every `<link>` and `<script>` in the HTML
to load the minified copy, so nobody has to edit compressed CSS by hand.

**Re-run this after editing any file under assets/css or assets/js.** It records
each source's hash in assets/.min-manifest.json, and tools/seo_audit.py fails if
a minified file no longer matches its source, so CI catches a forgotten run
rather than the site quietly serving last week's stylesheet.

rcssmin and rjsmin are deliberately conservative: they strip comments and
whitespace and nothing else. No renaming, no reordering, no clever rewrites, so
minified output cannot behave differently from the source.
"""
import hashlib
import json
import re
from pathlib import Path

import rcssmin
import rjsmin

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'assets' / '.min-manifest.json'

# Asset folders to compress, and the HTML that references them.
AREAS = [
    (ROOT / 'assets', sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('service-areas/*.html'))),
    (ROOT / 'landing' / 'assets', [ROOT / 'landing' / 'index.html',
                                   ROOT / 'landing' / 'confirmation.html']),
]

# A reference to a source file, not already minified: /assets/css/style.css?v=1
REFERENCE = re.compile(r'(/assets/(?:css|js)/[A-Za-z0-9_-]+)\.(css|js)\b')


def sources(assets):
    for folder, suffix in (('css', '.css'), ('js', '.js')):
        for f in sorted((assets / folder).glob(f'*{suffix}')):
            if not f.name.endswith(f'.min{suffix}'):
                yield f


def source_hash(source):
    """Hash the text with newlines normalised.

    A Windows checkout has CRLF line endings and a Linux one has LF, so hashing
    the raw bytes would make the manifest disagree with itself between here and
    CI. The content is what matters, not how the line ends.
    """
    text = source.read_text(encoding='utf-8').replace('\r\n', '\n')
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def minified_path(source):
    return source.with_suffix('.min' + source.suffix)


def minify(source):
    text = source.read_text(encoding='utf-8')
    if source.suffix == '.css':
        return rcssmin.cssmin(text)
    return rjsmin.jsmin(text)


def main():
    manifest = {}
    total_before = total_after = 0

    print('Minified:')
    for assets, _ in AREAS:
        for source in sources(assets):
            out = minified_path(source)
            body = minify(source)
            out.write_text(body, encoding='utf-8', newline='\n')

            before, after = len(source.read_bytes()), len(out.read_bytes())
            total_before += before
            total_after += after
            manifest[source.relative_to(ROOT).as_posix()] = source_hash(source)
            saved = 100 - round(after / before * 100)
            print(f'  {out.relative_to(ROOT).as_posix():44} '
                  f'{before // 1024:3} KB -> {after // 1024:3} KB  ({saved}% smaller)')

    print('Pages pointed at the minified copies:')
    for _, pages in AREAS:
        for page in pages:
            text = page.read_text(encoding='utf-8')
            updated = REFERENCE.sub(r'\1.min.\2', text)
            if updated != text:
                page.write_text(updated, encoding='utf-8', newline='\n')
                print(f'  {page.relative_to(ROOT).as_posix()}')

    MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    saved = total_before - total_after
    print(f'\n{total_before // 1024} KB of CSS and JS is now {total_after // 1024} KB, '
          f'{saved // 1024} KB smaller ({round(saved / total_before * 100)}%).')
    print(f'Hashes recorded in {MANIFEST.relative_to(ROOT).as_posix()}.')


if __name__ == '__main__':
    main()
