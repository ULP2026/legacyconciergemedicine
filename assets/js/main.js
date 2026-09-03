/* Legacy Concierge Medicine — site scripts */
(function () {
  'use strict';

  /* Mobile navigation */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('is-open', !open);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        toggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('is-open');
        toggle.focus();
      }
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

  /* Publish the header height so the home hero can fill the rest of the fold */
  var header = document.querySelector('.site-header');
  if (header) {
    var publishHeaderHeight = function () {
      document.documentElement.style.setProperty('--header-h', header.offsetHeight + 'px');
    };
    publishHeaderHeight();
    window.addEventListener('resize', publishHeaderHeight, { passive: true });
  }

  /* Home hero: keep the background video playing, and drift it gently on scroll */
  var heroVideo = document.querySelector('.h-hero-bg video');
  if (heroVideo) {
    heroVideo.muted = true;
    heroVideo.defaultMuted = true;
    var playing = heroVideo.play();
    if (playing && playing.catch) { playing.catch(function () {}); }

    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      var rate = parseFloat(heroVideo.getAttribute('data-parallax')) || 0;
      var ticking = false;
      var drift = function () {
        var offset = Math.min(window.scrollY, window.innerHeight) * rate;
        heroVideo.style.transform =
          'translate3d(0,' + offset.toFixed(1) + 'px,0) scale(1.12) scaleX(-1)';
        ticking = false;
      };
      window.addEventListener('scroll', function () {
        if (!ticking) { ticking = true; window.requestAnimationFrame(drift); }
      }, { passive: true });
      drift();
    }
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
