# Legacy Concierge Medicine — website

Static site (plain HTML/CSS/JS), deployed on Vercel from the `main` branch of github.com/ULP2026/legacyconciergemedicine.

- Pages: `index.html`, `about.html`, `services.html`, `contact.html`, legal (`disclaimer`, `privacy-policy`, `terms-and-conditions`), `404.html`
- Styles: `assets/css/style.css` (brand tokens at the top) + `assets/css/home.css` (home page only) · Scripts: `assets/js/main.js` · Media: `assets/img/`, `assets/video/`
- Clean URLs + redirects from the old Showit paths live in `vercel.json`.
- Updating a page, whether from the design canvas or by hand: see [CONTRIBUTING.md](CONTRIBUTING.md).

## Design canvas

The site follows the Legacy design canvas, whose latest export is kept at
`design/Legacy-Home-standalone.html` (a Claude Design bundle; `.vercelignore` keeps it out of the deploy). The home page body, and the shared
chrome on every page — top bar, CTA band, footer, in `assets/css/chrome.css` — are hand
ports of it.

The canvas nav points at pages that were never exported (The Practice, Membership,
In-Home Care, Continuity of Care, Service Areas and its city pages, FAQ, and separate
bio pages). Those menu entries currently resolve to sections of `/services` and
`/about`, and the service-area panel lists the cities as plain text rather than links.
Repoint them as the real pages get built.

Two further deliberate differences from the canvas:

- The credential strip under the hero uses text credentials, not the canvas's placeholder
  partner logos, which would imply affiliations the practice has not stated.
- The three-column testimonial wall is not built. Its quotes and member names in the canvas
  are placeholder copy; add it once real, attributable member quotes exist.

The hero is scroll-driven: a sticky panel inside a 150vh wrapper shrinks into a rounded
card while four photo tiles slide in behind it, and the survey section rides up underneath.
`main.js` drives it; it degrades to a plain hero without JS or under reduced motion.

The hero video (`assets/video/hero-loop.mp4`) is H.264 — the canvas shipped HEVC, which
Chrome and Firefox often refuse to decode. Re-encode any replacement the same way.

Local preview: `npx serve .` then open http://localhost:3000
