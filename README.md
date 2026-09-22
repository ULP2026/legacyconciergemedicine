# Legacy Concierge Medicine — website

Static site (plain HTML/CSS/JS), deployed on Vercel from the `main` branch of github.com/ULP2026/legacyconciergemedicine.

- Pages: `index.html`, `about.html`, `services.html`, `service-areas.html` + `service-areas/` (generated, see below), `contact.html`, `thank-you.html` (not indexed; where the survey should send people after they submit), legal (`disclaimer`, `privacy-policy`, `terms-and-conditions`), `404.html`
- Styles: `assets/css/style.css` (brand tokens at the top) + `assets/css/home.css` (home page only) + `assets/css/contact.css` and `assets/css/thank-you.css` (one page each) · Scripts: `assets/js/main.js` · Media: `assets/img/`, `assets/video/`
- Clean URLs + redirects from the old Showit paths live in `vercel.json`.
- Structured data (schema.org JSON-LD): practice details, breadcrumbs and FAQs. `tools/add_structured_data.py` writes the blocks on `index/about/services/contact` (re-runnable; it replaces its own blocks and leaves the home page's hand-written FAQ alone), and `tools/build_service_areas.py` writes them on the service-area pages.
- Analytics: Google Analytics 4, Measurement ID `G-GP4YR58GRS`, tagged in the `<head>` of every page (main site, generated service-area pages via `tools/build_service_areas.py`, and the landing page). Taps on phone and email links send `phone_click` / `email_click` events (`main.js`, `landing/assets/js/landing.js`). New pages need the same snippet.
- Updating a page, whether from the design canvas or by hand: see [CONTRIBUTING.md](CONTRIBUTING.md).

## Design canvas

The site follows the Legacy design canvas, whose latest export is kept at
`design/Legacy-Home-standalone.html`, with the contact and thank-you pages at `design/Legacy-Contact-standalone.html` and `design/Legacy-Thank-You-standalone.html` (Claude Design bundles; `.vercelignore` keeps them out of the deploy). The home, contact and thank-you page bodies (`home.css`, `contact.css`, `thank-you.css`), and the shared
chrome on every page — top bar, CTA band, footer, in `assets/css/chrome.css` — are hand
ports of it.

The canvas nav points at some pages that were never exported (The Practice, Membership,
In-Home Care, Continuity of Care, FAQ, and separate bio pages). Those menu entries
resolve to sections of `/services` and `/about`. Repoint them as the real pages get built.

## Service-area pages (generated)

`/service-areas` and the 13 community pages under `/service-areas/<city>` are **generated**,
not hand-edited. The exports live in `design/service-areas/` (one `Service-Area-<City>.html`
per community plus `Service-Areas.html`). After a new export, drop the files in there and run:

    python tools/build_service_areas.py

It pulls each page's content out of its export and writes `service-areas.html`,
`service-areas/*.html` and the shared map `assets/map/service-map.html`, reusing the
top bar, mobile menu and footer from `contact.html` (so edit those there first). Styles are
in `assets/css/service-areas.css`. Needs Python 3 with `beautifulsoup4`. A new photo in an
export stops the build until it is added to `assets/img/` (or `IMAGE_OVERRIDES`).

- The canvas map used CARTO tiles, which now watermark every tile with "API KEY REQUIRED"
  unless you pay for a key; the site uses OpenStreetMap's tiles, toned to the brand palette.
- "Town of Longboat Key" (Sarasota County) and "Longboat Key" (Manatee County) both link to
  the one Longboat Key page, as on the canvas.
- "How Continuity Works" and "About In-Home Care" go to `/services#continuity` and
  `/services#membership` until those pages exist.

Two parts of the home page are ported from the canvas as-is but still need sign-off
before the domain goes live:

- The credential strip under the hero is the canvas's logo marquee: Sarasota Memorial
  (Sarasota and Venice), HCA Florida Blake Hospital, American Lab. Showing those marks
  claims affiliations the practice has not yet confirmed in writing, and permission to
  display them. Confirm both, or swap the strip back to text credentials (see git history
  before September 2026 for that version).
- The "What our members say" wall carries the canvas's placeholder quotes and member
  names. Replace them with real, attributable member quotes (with permission on file)
  before launch.

The hero is scroll-driven: a sticky panel inside a 150vh wrapper shrinks into a rounded
card while four photo tiles slide in behind it, and the survey section rides up underneath.
`main.js` drives it; it degrades to a plain hero without JS or under reduced motion.

The hero video (`assets/video/hero-loop.mp4`) is H.264 — the canvas shipped HEVC, which
Chrome and Firefox often refuse to decode. Re-encode any replacement the same way.

Local preview: `npx serve .` then open http://localhost:3000

## Landing page (landing.legacyconciergemedicine.com)

`landing/` is a separate, standalone page for paid campaigns: its own HTML, CSS, JS, images,
video and `vercel.json`, sharing nothing with the main site's stylesheets. It deploys as its
own Vercel project, **legacy-landing**, whose Root Directory is `landing/`, so it publishes
from the same repo and branch but on its own domain. The main site redirects `/landing/*` to
the subdomain so the folder is never served twice.

- Design export: `design/Legacy-Landing-standalone.html` (hand-ported like the main pages).
- Its survey is a different GoHighLevel survey from the main site's: `MxddXb6dZcfb9dMe6Ruc`.
- Every push rebuilds both projects; that is expected and harmless for static files.
- The survey's own styling lives in GoHighLevel, not in this repo. On phones GHL switches to a
  mobile layout that falls back to its default dark labels and a white "1 of 2" footer, which
  are unreadable on the dark card. This CSS in the survey's **Styles → Custom CSS** box fixes it
  (keep it there if the survey is ever rebuilt):

  ```css
  /* Legacy landing page: keep the survey readable on the dark card, phones included */
  #_builder-form label,
  #_builder-form label * { color: #FFFFFF !important; }
  #_builder-form ::placeholder,
  #_builder-form .multiselect__placeholder { color: rgba(239, 236, 234, .6) !important; }
  .ghl-footer { background-color: #71140C !important; }
  .ghl-footer-buttons,
  .ghl-mobile-step-text { color: #EFECEA !important; }
  .ghl-footer-next svg,
  .ghl-footer-back svg { stroke: #EFECEA !important; }

  /* Dropdown: dark list with white text on every option, maroon for the highlighted/selected one */
  #_builder-form .multiselect__content-wrapper {
    background-color: #2A2624 !important;
    border-color: rgba(239, 236, 234, .25) !important;
  }
  #_builder-form .multiselect__option,
  #_builder-form .multiselect__option * {
    color: #FFFFFF !important;
  }
  #_builder-form .multiselect__option--highlight,
  #_builder-form .multiselect__option--selected,
  #_builder-form .multiselect__option:hover {
    background-color: #71140C !important;
    color: #FFFFFF !important;
  }
  ```

Local preview: `npx serve landing` then open http://localhost:3000
