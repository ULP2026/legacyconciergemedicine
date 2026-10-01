/* Legacy Concierge Medicine — site scripts */
(function () {
  'use strict';

  /* Top bar: on the home page it floats over the hero until you scroll past it */
  var bar = document.querySelector('.lcm-bar');
  if (bar) {
    var onScroll = function () { bar.classList.toggle('is-scrolled', window.scrollY > 24); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* Mobile navigation */
  var burger = document.querySelector('.lcm-burger');
  var panel = document.getElementById('lcm-mobile');
  if (burger && panel) {
    var closer = panel.querySelector('.lcm-mobile-close');
    var setMenu = function (open) {
      burger.setAttribute('aria-expanded', String(open));
      panel.hidden = !open;
      document.body.style.overflow = open ? 'hidden' : '';
      if (open) { panel.querySelector('a, button').focus(); } else { burger.focus(); }
    };
    burger.addEventListener('click', function () {
      setMenu(burger.getAttribute('aria-expanded') !== 'true');
    });
    if (closer) { closer.addEventListener('click', function () { setMenu(false); }); }
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !panel.hidden) { setMenu(false); }
    });
  }

  /* Footer year */
  var year = document.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());

  /* Scroll reveal (no-op when reduced motion is preferred) */
  var reveals = document.querySelectorAll('.reveal');
  if (reveals.length && 'IntersectionObserver' in window &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.1 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* Home hero: the 1.5 MB background video waits until the page has loaded
     and painted, so it doesn't compete with the headline on a phone
     connection. The poster shows until then. Skipped entirely when the
     visitor has asked to save data. */
  var heroVideo = document.querySelector('.h-hero-bg video');
  if (heroVideo) {
    var startVideo = function () {
      if (navigator.connection && navigator.connection.saveData) { return; }
      if (heroVideo.dataset.src) { heroVideo.src = heroVideo.dataset.src; }
      heroVideo.muted = true;
      heroVideo.defaultMuted = true;
      var playing = heroVideo.play();
      if (playing && playing.catch) { playing.catch(function () {}); }
    };
    var afterPaint = function () {
      var types = window.PerformanceObserver && PerformanceObserver.supportedEntryTypes;
      if (!types || types.indexOf('paint') < 0) { startVideo(); return; }
      new PerformanceObserver(function (list, obs) {
        if (list.getEntriesByName('first-contentful-paint').length) { obs.disconnect(); startVideo(); }
      }).observe({ type: 'paint', buffered: true });
    };
    if (document.readyState === 'complete') { afterPaint(); }
    else { window.addEventListener('load', afterPaint, { once: true }); }
  }

  /* Home hero: as you scroll through the taller wrapper, the sticky panel
     shrinks into a rounded card and the photo tiles slide in behind it. */
  var heroWrap = document.querySelector('.h-hero-wrap');
  var heroPanel = document.querySelector('.h-hero-panel');
  if (heroWrap && heroPanel && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var heroCopy = document.querySelector('.h-hero-copy');
    var left = document.querySelectorAll('.h-htile.from-left');
    var right = document.querySelectorAll('.h-htile.from-right');
    var queued = false;

    var frame = function () {
      queued = false;
      /* Phones get a plain hero (see home.css), so undo anything a wider window left behind. */
      if (window.innerWidth <= 760) {
        heroPanel.style.transform = '';
        heroPanel.style.borderRadius = '';
        if (heroCopy) { heroCopy.style.opacity = ''; }
        return;
      }
      var box = heroWrap.getBoundingClientRect();
      var travel = box.height - window.innerHeight;
      var p = travel > 0 ? Math.min(1, Math.max(0, -box.top / travel)) : 0;
      var eased = p * (2 - p);

      var scale = window.innerWidth < 1180 ? 1 - 0.10 * eased : 1 - 0.42 * eased;
      heroPanel.style.transform = 'scale(' + scale + ')';
      heroPanel.style.borderRadius = (14 * eased) + 'px';
      if (heroCopy) { heroCopy.style.opacity = String(1 - 0.25 * eased); }

      /* Tiles trail the panel: they only start once it has shrunk a little. */
      var t = Math.min(1, Math.max(0, (p - 0.22) / 0.55));
      var te = t * (2 - t);
      var slide = function (tiles, direction) {
        Array.prototype.forEach.call(tiles, function (tile, i) {
          tile.style.opacity = String(te);
          tile.style.transform = 'translateX(' + (direction * 130 * (1 - te)) + '%)' +
            ' translateY(' + (i * 8 * (1 - te)) + 'px)';
        });
      };
      slide(left, -1);
      slide(right, 1);
    };

    var request = function () {
      if (!queued) { queued = true; window.requestAnimationFrame(frame); }
    };
    window.addEventListener('scroll', request, { passive: true });
    window.addEventListener('resize', request, { passive: true });
    frame();
  }
  /* GoHighLevel survey embed
     form_embed.js grows the iframe to fit each survey step. It can leave the
     frame hidden while it initialises; the design canvas reveals it after a few
     seconds in case that never finishes, and so do we. */
  var revealSurveys = function () {
    var frames = document.querySelectorAll('iframe[src*="leadconnectorhq.com/widget/survey"]');
    Array.prototype.forEach.call(frames, function (f) {
      if (f.getAttribute('data-initial-iframe-hidden') !== 'true' && getComputedStyle(f).visibility !== 'hidden') return;
      ['position', 'left', 'top', 'opacity', 'visibility', 'pointer-events'].forEach(function (prop) { f.style.removeProperty(prop); });
      f.style.setProperty('position', 'static');
      f.style.setProperty('opacity', '1');
      f.style.setProperty('visibility', 'visible');
      f.style.setProperty('pointer-events', 'auto');
      f.removeAttribute('data-initial-iframe-hidden');
    });
  };
  window.setTimeout(revealSurveys, 2800);

  /* A survey below the fold carries data-src instead of src: the survey and
     form_embed.js together pull in about 1 MB of GoHighLevel, Cloudflare and
     Facebook code, so they wait for the visitor's first scroll, tap or key
     press (or the form coming into view), well before anyone reaches it.
     The script is added after the src, the same order as a normal page load. */
  var deferredSurveys = document.querySelectorAll('iframe[data-src*="leadconnectorhq.com/widget/survey"]');
  if (deferredSurveys.length) {
    var surveysLoaded = false;
    var firstTouch = ['scroll', 'touchstart', 'pointerdown', 'keydown'];
    var loadSurveys = function () {
      if (surveysLoaded) { return; }
      surveysLoaded = true;
      firstTouch.forEach(function (type) { window.removeEventListener(type, loadSurveys, true); });
      Array.prototype.forEach.call(deferredSurveys, function (f) {
        if (!f.src) { f.src = f.getAttribute('data-src'); }
      });
      if (!document.querySelector('script[src*="form_embed.js"]')) {
        var embed = document.createElement('script');
        embed.src = 'https://link.msgsndr.com/js/form_embed.js';
        document.body.appendChild(embed);
      }
      window.setTimeout(revealSurveys, 2800);
    };
    if ('IntersectionObserver' in window) {
      var surveyWatch = new IntersectionObserver(function (entries) {
        if (entries.some(function (e) { return e.isIntersecting; })) {
          surveyWatch.disconnect();
          loadSurveys();
        }
      });
      Array.prototype.forEach.call(deferredSurveys, function (f) { surveyWatch.observe(f); });
      firstTouch.forEach(function (type) { window.addEventListener(type, loadSurveys, { capture: true, passive: true }); });
    } else {
      loadSurveys();
    }
  }
  /* Analytics: GA4 does not count taps on phone or email links by itself. */
  document.addEventListener('click', function (e) {
    var link = e.target.closest && e.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!link || typeof window.gtag !== 'function') { return; }
    var href = link.getAttribute('href');
    window.gtag('event', href.indexOf('tel:') === 0 ? 'phone_click' : 'email_click', { link_url: href });
  });
})();
