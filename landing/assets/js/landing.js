/* Legacy Concierge Medicine: landing page behaviour
   Ported from the landing canvas: the hero video and closing photo drift for
   parallax, and [data-reveal] blocks fade in as they scroll into view. */
(function () {
  /* ==== Ad click attribution: BEGIN ========================================
     KEEP IN STEP: this block is identical in assets/js/main.js and
     landing/assets/js/landing.js. The landing site is its own Vercel project
     and can only load files under landing/, so it cannot share the file.
     Change one, change the other, then run tools/minify_assets.py.

     A visitor who comes from an ad has utm_* and gclid/fbclid on the URL of
     whichever page they land on, but often fills in the survey later, on
     another page or on the other site. So the seven keys the CRM's hidden
     fields read are kept in a first-party cookie, lcm_attr (the last ad
     click wins: any of the keys on the URL replaces the whole stored set),
     and added to every GoHighLevel survey or form iframe on the page. Only
     those seven, never the whole query string, which would reach the CRM
     as junk. No network call, nothing visible.

     It runs first, before anything else in this file, so a deferred survey's
     data-src already carries the keys when the lazy loader copies it to src.
     That is one ordering guarantee inside one file, rather than a second
     call to remember in every loader. */
  var attribution = (function () {
    var KEYS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid'];
    var COOKIE = 'lcm_attr';
    var MAX_LEN = 500;
    var MAX_AGE = 90 * 24 * 60 * 60;

    /* The seven keys out of any source, each a non-empty string of at most
       500 characters. null when none of them is there. */
    var pick = function (get) {
      var set = {};
      var found = false;
      KEYS.forEach(function (key) {
        var value = get(key);
        if (typeof value === 'string' && value !== '') {
          set[key] = value.slice(0, MAX_LEN);
          found = true;
        }
      });
      return found ? set : null;
    };

    var fromUrl = function () {
      try {
        var query = new URLSearchParams(window.location.search);
        return pick(function (key) { return query.get(key); });
      } catch (e) { return null; }
    };

    var readCookie = function () {
      try {
        var parts = document.cookie ? document.cookie.split(';') : [];
        for (var i = 0; i < parts.length; i++) {
          var part = parts[i].replace(/^\s+/, '');
          if (part.indexOf(COOKIE + '=') === 0) {
            var data = JSON.parse(decodeURIComponent(part.slice(COOKIE.length + 1)));
            return data && typeof data === 'object' ? pick(function (key) { return data[key]; }) : null;
          }
        }
      } catch (e) {}
      return null;
    };

    /* Shared by www. and landing. on the real domain; host-only anywhere
       else (localhost, *.vercel.app previews), where a Domain would be refused. */
    var writeCookie = function (set) {
      try {
        var host = window.location.hostname;
        var domain = /(^|\.)legacyconciergemedicine\.com$/.test(host) ? '; Domain=.legacyconciergemedicine.com' : '';
        document.cookie = COOKIE + '=' + encodeURIComponent(JSON.stringify(set)) +
          '; Path=/; Max-Age=' + MAX_AGE + '; SameSite=Lax; Secure' + domain;
      } catch (e) {}
    };

    /* This visit's keys if it has any (stored for later), else the stored
       set. If the cookie cannot be read or written, the URL's own keys are
       still used for this page. */
    var current = fromUrl();
    if (current) { writeCookie(current); } else { current = readCookie() || {}; }

    var isSurvey = function (url) {
      return !!url && (url.indexOf('leadconnectorhq.com/widget/survey') >= 0 || url.indexOf('/widget/form') >= 0);
    };

    /* url plus every stored key it does not already have. A key already on
       the iframe (put there by hand or by form_embed.js) is left as it is.
       Returns the very same string when nothing was added. */
    var addTo = function (url) {
      try {
        var next = new URL(url, window.location.href);
        var added = false;
        KEYS.forEach(function (key) {
          if (current[key] && !next.searchParams.has(key)) {
            next.searchParams.set(key, current[key]);
            added = true;
          }
        });
        return added ? next.toString() : url;
      } catch (e) { return url; }
    };

    /* data-src (a survey that waits for the visitor) and src alike. The
       attribute is written only when a key was actually added: setting src,
       even to the same value, reloads a frame that has already loaded. */
    var apply = function () {
      Array.prototype.forEach.call(document.querySelectorAll('iframe'), function (frame) {
        ['data-src', 'src'].forEach(function (attr) {
          var url = frame.getAttribute(attr);
          if (!isSurvey(url)) { return; }
          var next = addTo(url);
          if (next !== url) { frame.setAttribute(attr, next); }
        });
      });
    };

    return { apply: apply };
  })();
  attribution.apply();
  /* ==== Ad click attribution: END ========================================== */

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* The survey comes first. Its placeholder fades once CENTRO has answered (the frame's
     load event or its first message, whichever comes first, with a 4s fallback), and
     only then does the 6.6 MB hero video start downloading. The poster covers the wait. */
  var video = document.querySelector('.l-fold-video');
  var startVideo = function () {
    if (!video || video.getAttribute('src')) { return; }
    video.muted = true;
    video.defaultMuted = true;
    video.volume = 0;
    video.preload = 'auto';
    video.src = video.getAttribute('data-src');
    var playing = video.play();
    if (playing && playing.catch) { playing.catch(function () {}); }
  };

  var surveyFrame = document.querySelector('.l-survey .frame');
  var surveyIframe = surveyFrame && surveyFrame.querySelector('iframe');
  var surveyDone = false;
  var surveyReady = function () {
    if (surveyDone) { return; }
    surveyDone = true;
    if (surveyFrame) { surveyFrame.classList.add('is-ready'); }
    startVideo();
  };
  if (surveyIframe) {
    surveyIframe.addEventListener('load', surveyReady);
    window.addEventListener('message', function (e) {
      if (/leadconnectorhq\.com$|msgsndr\.com$/.test(String(e.origin))) { surveyReady(); }
    });
    window.setTimeout(surveyReady, 4000);
  } else {
    startVideo();
  }

  /* Reveal on scroll */
  var reveals = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && !reduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    Array.prototype.forEach.call(reveals, function (el) { io.observe(el); });
  } else {
    Array.prototype.forEach.call(reveals, function (el) { el.classList.add('is-in'); });
  }

  /* Analytics: GA4 does not count taps on phone or email links by itself. */
  document.addEventListener('click', function (e) {
    var link = e.target.closest && e.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!link || typeof window.gtag !== 'function') { return; }
    var href = link.getAttribute('href');
    window.gtag('event', href.indexOf('tel:') === 0 ? 'phone_click' : 'email_click', { link_url: href });
  });

  /* Keep the whole survey card inside the fold on desktop. When the window is too
     short for it, the card is zoomed down (never below 75%) instead of scrolling.
     Re-fits whenever form_embed.js resizes the survey for a new step. */
  var card = document.querySelector('.l-survey');
  var grid = document.querySelector('.l-fold-grid');
  var wide = window.matchMedia('(min-width: 960px)');
  if (card && grid && 'zoom' in card.style) {
    var fitting = false;
    var fit = function () {
      if (fitting) { return; }
      fitting = true;
      card.style.zoom = '';
      if (wide.matches) {
        var cs = window.getComputedStyle(grid);
        var top = grid.getBoundingClientRect().top + window.scrollY;
        var room = window.innerHeight - top - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
        var need = card.offsetHeight;
        if (need > room) { card.style.zoom = String(Math.max(0.75, room / need).toFixed(3)); }
      }
      fitting = false;
    };
    if ('ResizeObserver' in window) {
      var frameEl = card.querySelector('iframe');
      if (frameEl) { new ResizeObserver(fit).observe(frameEl); }
    }
    window.addEventListener('resize', fit, { passive: true });
    if (wide.addEventListener) { wide.addEventListener('change', fit); }
    fit();
  }

  if (reduced) { return; }

  var closing = document.querySelector('.l-closing');
  var closingImg = document.querySelector('.l-closing-img');
  var queued = false;

  var frame = function () {
    queued = false;
    var vh = window.innerHeight;

    if (video) {
      var y = Math.min(window.scrollY, vh);
      video.style.transform = 'translate3d(0, ' + (y * 0.16).toFixed(1) + 'px, 0) scale(' + (1 + y / vh * 0.04).toFixed(4) + ')';
    }

    if (closing && closingImg) {
      var r = closing.getBoundingClientRect();
      var t = Math.max(0, Math.min(1, (vh - r.top) / (vh + r.height)));
      closingImg.style.transform = 'translate3d(0, ' + ((t - 0.5) * r.height * 0.22).toFixed(1) + 'px, 0)';
    }
  };

  var request = function () {
    if (!queued) { queued = true; window.requestAnimationFrame(frame); }
  };
  window.addEventListener('scroll', request, { passive: true });
  window.addEventListener('resize', request, { passive: true });
  frame();
})();
