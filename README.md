# Legacy Concierge Medicine — website

Static site (plain HTML/CSS/JS), deployed on Vercel from the `main` branch of github.com/ULP2026/Legacy.

- Pages: `index.html`, `about.html`, `services.html`, `contact.html`, legal (`disclaimer`, `privacy-policy`, `terms-and-conditions`), `404.html`
- Styles: `assets/css/style.css` (brand tokens at the top) + `assets/css/home.css` (home page only) · Scripts: `assets/js/main.js` · Media: `assets/img/`, `assets/video/`
- Clean URLs + redirects from the old Showit paths live in `vercel.json`.

## Home page

The home page is a hand port of the Legacy design canvas kept at `design/Home.html`
(the Claude Design export; `.vercelignore` keeps it out of the deploy). Two deliberate
differences from that canvas:

- The credential strip under the hero uses text credentials, not the canvas's placeholder
  partner logos, which would imply affiliations the practice has not stated.
- The three-column testimonial wall is not built. Its quotes and member names in the canvas
  are placeholder copy; add it once real, attributable member quotes exist.

The hero video (`assets/video/hero-loop.mp4`) is H.264 — the canvas shipped HEVC, which
Chrome and Firefox often refuse to decode. Re-encode any replacement the same way.

Local preview: `npx serve .` then open http://localhost:3000
