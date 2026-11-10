/* Fix It Notes: sticky nav, guide filter, optional AdSense + HubSpot form. No dependencies. */
(function () {
  'use strict';
  var CFG = window.SITE_CONFIG || {};
  var root = document.documentElement;

  /* Sticky nav: darken + blur once scrolled */
  var head = document.querySelector('.site-head');
  if (head) {
    var onScroll = function () { head.classList.toggle('scrolled', window.scrollY > 8); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* Mark the active nav link (guides map to their category via the breadcrumb) */
  var path = location.pathname;
  var crumb = document.querySelector('.crumbs a[href^="/"]:not([href="/"])');
  var navLinks = document.querySelectorAll('.main-nav a');
  navLinks.forEach(function (a) {
    var href = a.getAttribute('href');
    if (path.indexOf(href) === 0 || (crumb && path.indexOf('/guides/') === 0 && crumb.getAttribute('href') === href)) {
      a.setAttribute('aria-current', 'page');
    }
  });

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
      window.hbspt.forms.create({
        region: CFG.HUBSPOT_REGION, portalId: CFG.HUBSPOT_PORTAL, formId: CFG.CONTACT_FORM_ID, target: '#' + form.id,
        onFormReady: function () {
          /* The embed renders in a same-origin iframe with light-theme colors; restyle it for the dark brand (AA contrast). */
          var fr = form.querySelector('iframe');
          var doc = fr && fr.contentDocument;
          if (!doc || !doc.head) return;
          var st = doc.createElement('style');
          st.textContent =
            'body,form{font-family:Inter,"Helvetica Neue",Helvetica,Arial,sans-serif !important;background:transparent !important}' +
            'label,legend,.hs-form-field>label,.hs-richtext,.hs-richtext p{color:#fff !important;font-size:14px !important;font-weight:700 !important}' +
            '.hs-field-desc,.legal-consent-container,.legal-consent-container p{color:rgba(255,255,255,.72) !important;font-size:13px !important}' +
            '.hs-form-required{color:#ff9b7a !important}' +
            '.hs-error-msg,.hs-error-msgs label{color:#ff9b7a !important}' +
            'input.hs-input,textarea.hs-input,select.hs-input{background:#000 !important;color:#fff !important;border:1px solid rgba(255,255,255,.28) !important;border-radius:4px !important;min-height:46px;font-size:16px !important}' +
            '.hs-button{background:#9a00ff !important;border:0 !important;border-radius:50px !important;min-height:52px;padding:0 28px !important;font:700 14px/1 Inter,Arial,sans-serif !important;text-transform:uppercase;letter-spacing:.06em;color:#fff !important;cursor:pointer}' +
            '.submitted-message,.submitted-message p{color:#fff !important}';
          doc.head.appendChild(st);
        }
      });
    };
    h.onerror = function () {
      form.innerHTML = '<p>The form did not load (an ad blocker can do this).' + (CFG.CONTACT_EMAIL ? ' Email <a href="mailto:' + CFG.CONTACT_EMAIL + '">' + CFG.CONTACT_EMAIL + '</a> instead.' : '') + '</p>';
    };
    document.body.appendChild(h);
  }
})();
