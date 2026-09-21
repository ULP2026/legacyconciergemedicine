/* Legacy Concierge Medicine — landing page behaviour
   Ported from the landing canvas: the fold copy fades up as the consultation
   band arrives, the hero video and closing photo drift for parallax, and
   [data-reveal] blocks fade in as they scroll into view. */
(function () {
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Keep the hero video playing silently (some browsers need the nudge). */
  var video = document.querySelector('.l-fold-video');
  if (video) {
    video.muted = true;
    video.defaultMuted = true;
    video.volume = 0;
    var playing = video.play();
    if (playing && playing.catch) { playing.catch(function () {}); }
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

  if (reduced) { return; }

  var foldCopy = document.querySelector('.l-fold-copy');
  var band = document.querySelector('.l-consult');
  var closing = document.querySelector('.l-closing');
  var closingImg = document.querySelector('.l-closing-img');
  var queued = false;

  var frame = function () {
    queued = false;
    var vh = window.innerHeight;

    if (foldCopy && band) {
      var top = band.getBoundingClientRect().top;
      var p = Math.max(0, Math.min(1, 1 - (top - vh * 0.15) / (vh * 0.85)));
      var e = p * p * (3 - 2 * p);
      foldCopy.style.opacity = String(1 - e * 0.9);
      foldCopy.style.transform = 'translate3d(0, ' + (-e * 40).toFixed(1) + 'px, 0)';
    }

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
