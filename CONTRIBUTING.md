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

You never need git or a code editor for this. Everything happens in the browser.

**1. Edit the canvas in Claude Design,** and save when you're happy.

**2. Export it.** Use the canvas's export/download to get the standalone `.html`. It lands
in your **Downloads** folder, named something like `Legacy Home (standalone).html`. Leave
it there — it does not get filed anywhere on your PC.

To check your own work, double-click the file. It opens and renders in your browser. That
preview is local to your machine; nobody else can see it.

**3. Rename it to match the page you're updating.** In Downloads, rename the file to:

| Updating | Rename to |
|---|---|
| Home page | `Legacy-Home-standalone.html` |
| A page with no canvas yet | `Legacy-<Page>-standalone.html` |

Matching the existing name is what makes the change show up as a diff instead of as an
unrelated second file.

**4. Upload it to the repo, on a new branch:**

- Go to the repo → click into the **`design`** folder
- **Add file → Upload files**, and drag your renamed `.html` in
- Commit message: what you changed — `Hero: new photos and shorter headline`
- Select **"Create a new branch for this commit and start a pull request"**.
  Do not pick the other option — that one publishes straight to the live site.
- Branch name: something like `design/new-hero` → **Propose changes**

**5. Open the pull request.** Title starts with your name — `Maria: new hero photos`. In
the body, say which sections you changed and anything that isn't obvious by looking. The
port is built from that description.

**6. Ask for the port.** Say in the PR that it's ready. Someone runs Claude Code on your
branch to turn the export into real pages.

Until that happens the preview will show the site **unchanged** — you've added a design
file, not edited the site. That's expected, not a broken preview.

**7. Review the preview.** Once the port is pushed, Vercel updates the preview link in the
PR. Open it on a laptop **and** a phone.

**8. Merge.** Click **Merge pull request**; the site rebuilds and is live in about a
minute. If something's wrong afterwards: Vercel dashboard → the project → **Deployments** →
the previous one → **Instant Rollback**.

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
