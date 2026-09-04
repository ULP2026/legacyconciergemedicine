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

  /* Home hero: keep the background video playing */
  var heroVideo = document.querySelector('.h-hero-bg video');
  if (heroVideo) {
    heroVideo.muted = true;
    heroVideo.defaultMuted = true;
    var playing = heroVideo.play();
    if (playing && playing.catch) { playing.catch(function () {}); }
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

  /* Contact form
     Interim behaviour: composes an email to the practice inbox with the
     entered details. Replace this block (or the whole <form>) with the
     GoHighLevel form embed once the client's form/pipeline is set up. */
  var form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (form.querySelector('input[name="company"]').value) return; /* honeypot */

      var data = new FormData(form);
      var name = (data.get('name') || '').toString().trim();
      var email = (data.get('email') || '').toString().trim();
      var phone = (data.get('phone') || '').toString().trim();
      var about = (data.get('about') || '').toString().trim();
      var message = (data.get('message') || '').toString().trim();

      var subject = 'Private consultation inquiry' + (name ? ' — ' + name : '');
      var body = [
        'Name: ' + name,
        'Email: ' + email,
        'Phone: ' + phone,
        'Exploring care for: ' + about,
        '',
        message
      ].join('\n');

      window.location.href = 'mailto:info@legacyconciergemedicine.com' +
        '?subject=' + encodeURIComponent(subject) +
        '&body=' + encodeURIComponent(body);

      var status = document.getElementById('form-status');
      if (status) {
        status.textContent = 'Thank you. Your email client should open with your message — send it and we will be in touch soon.';
        status.className = 'form-status ok';
      }
    });
  }
})();
