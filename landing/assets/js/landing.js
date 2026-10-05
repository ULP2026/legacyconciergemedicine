/* Legacy Concierge Medicine: landing page behaviour
   Ported from the landing canvas: the hero video and closing photo drift for
   parallax, and [data-reveal] blocks fade in as they scroll into view. */
(function () {
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
