/* Fix It Notes: theme toggle, guide filter, optional AdSense + HubSpot form. No dependencies. */
(function () {
  'use strict';
  var CFG = window.SITE_CONFIG || {};
  var root = document.documentElement;

  /* Theme toggle */
  var btn = document.querySelector('.theme-btn');
  if (btn) {
    btn.addEventListener('click', function () {
      var cur = root.getAttribute('data-theme') ||
        (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      var next = cur === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }

  /* Guide filter on /guides/ (also handles ?q= from the home search) */
  var idxEl = document.getElementById('gindex');
  var input = document.getElementById('gq');
  var out = document.getElementById('gresults');
  if (idxEl && input && out) {
    var idx = JSON.parse(idxEl.textContent);
    var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
    var run = function () {
      var q = input.value.trim().toLowerCase();
      if (!q) { out.hidden = true; out.innerHTML = ''; return; }
      var words = q.split(/\s+/);
      var hits = idx.filter(function (g) {
        var hay = (g.t + ' ' + g.k).toLowerCase();
        return words.every(function (w) { return hay.indexOf(w) !== -1; });
      });
      out.hidden = false;
      out.innerHTML = hits.length
        ? hits.map(function (g) { return '<li><a href="' + g.u + '">' + esc(g.t) + '</a></li>'; }).join('')
        : '<li>No guides match. Try a simpler word like "toilet" or "outlet".</li>';
    };
    input.addEventListener('input', run);
    var m = location.search.match(/[?&]q=([^&]*)/);
    if (m) { input.value = decodeURIComponent(m[1].replace(/\+/g, ' ')); run(); }
  }

  /* AdSense: only when a client id is configured. Slots are empty divs otherwise (and build.py omits them). */
  var slots = document.querySelectorAll('.ad-slot');
  if (CFG.ADSENSE_CLIENT && slots.length) {
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(CFG.ADSENSE_CLIENT);
    s.crossOrigin = 'anonymous';
    document.head.appendChild(s);
    slots.forEach(function (el) {
      el.innerHTML = '<ins class="adsbygoogle" style="display:block" data-ad-client="' + CFG.ADSENSE_CLIENT + '" data-ad-format="auto" data-full-width-responsive="true"></ins>';
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    });
  }

  /* HubSpot contact form: only when CONTACT_FORM_ID is set */
  var form = document.querySelector('[data-hs-form]');
  if (form && CFG.CONTACT_FORM_ID) {
    var h = document.createElement('script');
    h.src = 'https://js.hsforms.net/forms/embed/v2.js';
    h.async = true;
    h.onload = function () {
      form.id = form.id || 'hs-contact';
      window.hbspt.forms.create({ region: CFG.HUBSPOT_REGION, portalId: CFG.HUBSPOT_PORTAL, formId: CFG.CONTACT_FORM_ID, target: '#' + form.id });
    };
    h.onerror = function () {
      form.innerHTML = '<p>The form did not load (an ad blocker can do this).' + (CFG.CONTACT_EMAIL ? ' Email <a href="mailto:' + CFG.CONTACT_EMAIL + '">' + CFG.CONTACT_EMAIL + '</a> instead.' : '') + '</p>';
    };
    document.body.appendChild(h);
  }
})();
