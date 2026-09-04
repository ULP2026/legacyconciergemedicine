# Updating the website

The live site is published by Vercel from the `main` branch of
[ULP2026/legacyconciergemedicine](https://github.com/ULP2026/legacyconciergemedicine).
Anything merged to `main` goes live within about a minute. Anything pushed to another
branch gets its own private preview URL instead, which is where review happens.

Design work happens on the Claude Design canvas. The canvas cannot publish to GitHub
itself, and its export is not a web page you can ship — see [Why the export needs a
port](#why-the-export-needs-a-port). So the flow below has one deliberate step where a
developer turns the export into real pages.

## We all share one account

Everyone works through the same GitHub, Vercel, and Claude login. That keeps access
simple, and it costs us three things the tools would otherwise handle. Conventions have to
cover them instead:

**Nobody can tell who changed what.** Every commit is authored by the same account, so git
history won't answer "who wrote this, and why". So: **put your name in the pull request
title** — `Maria: new hero photos` — and describe the change in the body. That is the only
record of who to ask.

**Anyone can publish instantly.** The shared account can push straight to `main`, which
goes live with no review. Don't. Always work on a branch and open a pull request, even for
a one-word fix — that's what produces the preview link, and it's the only thing standing
between a typo and the live site. (Worth turning on branch protection for `main` in
**Settings → Rules** so this is enforced rather than remembered.)

**Two people editing at once will overwrite each other.** This is the sharp edge, and it
bites hardest on the Claude Design canvas: saving publishes a new version for everyone, so
the second person to save wins and the first person's work is gone. **Say in the team chat
that you're picking up the canvas, and say when you're done.** In the repo it's less
dangerous — git will refuse to overwrite and ask you to reconcile — but two branches
touching the same page still means someone has to merge them by hand.

If someone leaves the team, the account password and any GitHub or Vercel tokens need
rotating, because there is no per-person access to revoke.

## Making a change

**1. Edit the canvas in Claude Design.** Save when you're happy with it.

**2. Export it.** Use the canvas's export/download to get the standalone `.html` file.

**3. Put the export in the repo, on a new branch.** No git needed — use the GitHub website:

- Open the repo → `design/` folder → **Add file → Upload files**
- Drag the exported `.html` in
- At the bottom, choose **Create a new branch for this commit and start a pull request**
- Name the branch something like `design/new-hero`, and click **Propose changes**
- Start the pull request title with your name, so the team knows whose change it is

Keep the existing filename if you're updating the same page, so the diff shows what
changed. Use a new descriptive name (`Legacy-About-standalone.html`) for a new page.

**4. Say what changed** in the pull request description — which sections you touched, and
anything that isn't obvious from looking. This is what the port is built from.

**5. A developer ports it.** The export gets turned into real HTML, CSS, and image files
on the same branch. Ask in the PR when it's ready for that.

**6. Review the preview.** Vercel comments on every pull request with a preview URL that
shows the ported result. Check it on a phone as well as a laptop.

**7. Merge.** The site rebuilds and the change is live. If something looks wrong
afterwards, Vercel's dashboard can roll back to the previous deployment immediately.

## Why the export needs a port

The Claude Design export is a self-unpacking bundle: about 13 MB, with the images and
video encoded inside the file, resources referenced by UUID rather than filename, and the
page assembled by JavaScript when it loads. Served as-is it would mean a page that search
engines see as blank, a very slow first load, and links pointing at `.dc.html` files that
don't exist on the site.

The port extracts the media into `assets/`, rewrites the markup against the site's real
stylesheets and URLs, and re-encodes video that browsers can't play (the canvas ships
HEVC, which Chrome and Firefox generally refuse).

## Decisions the port has to preserve

These live in the code, not the canvas, so every re-import has to re-apply them. If a
future port drops one, that's a bug:

- **No placeholder partner logos.** The canvas hero has a marquee of stand-in logos. The
  site shows text credentials instead, because unattributed logos imply affiliations the
  practice has not claimed.
- **No invented testimonials.** The canvas has a three-column testimonial wall whose
  quotes and member names are placeholder copy. It stays out until there are real,
  attributable member quotes with permission on file.
- **Menu links point at pages that exist.** The canvas nav links to The Practice,
  Membership, In-Home Care, Continuity of Care, Service Areas and its city pages, FAQ, and
  separate bio pages. None of those were exported, so those entries resolve to sections of
  `/services` and `/about`, and the service-area panel lists cities as plain text.

## If you only need to change wording

Small copy edits don't need the canvas at all. Edit the `.html` file directly on GitHub
(pencil icon → **Create a new branch** → propose changes) and the same preview-and-merge
flow applies. Tell the designer, so the canvas doesn't drift out of sync with the site.
