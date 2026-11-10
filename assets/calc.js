/* Fix It Notes calculators. Pure functions + live form wiring. */
(function () {
  'use strict';
  function num(f, n) { var v = parseFloat(f.elements[n].value); return isFinite(v) && v > 0 ? v : 0; }
  function r1(x) { return Math.round(x * 10) / 10; }
  function r2(x) { return Math.round(x * 100) / 100; }

  var CALC = {
    paint: function (f) {
      var L = num(f, 'len'), W = num(f, 'wid'), H = num(f, 'hgt');
      var coats = Math.max(1, Math.round(num(f, 'coats')) || 1);
      var cov = num(f, 'cov') || 350;
      var openings = num(f, 'doors') * 21 + num(f, 'wins') * 15;
      var walls = Math.max(0, 2 * (L + W) * H - openings);
      var ceil = f.elements.ceil.checked ? L * W : 0;
      var area = walls + ceil;
      var gal = area * coats / cov;
      var gallons = Math.ceil(gal * 4) / 4; // round up to the nearest quart
      var whole = Math.floor(gallons), quarts = Math.round((gallons - whole) * 4);
      var buy = whole + (whole ? ' gallon' + (whole > 1 ? 's' : '') : '') + (quarts ? (whole ? ' + ' : '') + quarts + ' quart' + (quarts > 1 ? 's' : '') : '');
      if (!area) return 'Enter room measurements to see an estimate.';
      return 'Paintable area: <strong>' + Math.round(area) + ' sq ft</strong> (' + Math.round(walls) + ' walls' + (ceil ? ', ' + Math.round(ceil) + ' ceiling' : '') + ').<br>' +
        'Paint needed for ' + coats + ' coat' + (coats > 1 ? 's' : '') + ': <strong>' + r1(gal) + ' gallons</strong>. Buy about ' + (buy || '1 quart') + '.';
    },
    floor: function (f) {
      var base = num(f, 'len') * num(f, 'wid') + num(f, 'extra');
      var waste = parseFloat(f.elements.waste.value) || 0;
      var total = base * (1 + waste / 100);
      var box = num(f, 'box') || 20;
      var boxes = Math.ceil(total / box);
      var price = num(f, 'price');
      if (!base) return 'Enter room measurements to see an estimate.';
      return 'Room area: <strong>' + r1(base) + ' sq ft</strong>. With ' + waste + '% waste: <strong>' + r1(total) + ' sq ft</strong>.<br>' +
        'Boxes to buy: <strong>' + boxes + '</strong> (' + r1(boxes * box) + ' sq ft)' +
        (price ? '. Material cost at $' + r2(price) + '/sq ft: about <strong>$' + Math.round(boxes * box * price).toLocaleString() + '</strong>' : '') + '.';
    },
    mulch: function (f) {
      var sqft = num(f, 'len') * num(f, 'wid');
      var cuft = sqft * num(f, 'dep') / 12;
      var yd = cuft / 27;
      var bag = parseFloat(f.elements.bag.value) || 2;
      var tpy = parseFloat(f.elements.mat.value) || 0;
      if (!sqft) return 'Enter the area to see an estimate.';
      return 'Area: <strong>' + r1(sqft) + ' sq ft</strong>. Volume: <strong>' + r2(yd) + ' cubic yards</strong> (' + r1(cuft) + ' cu ft).<br>' +
        'Bags of ' + bag + ' cu ft: <strong>' + Math.ceil(cuft / bag) + '</strong>' +
        (tpy ? '. Approximate weight: <strong>' + r2(yd * tpy) + ' tons</strong> (confirm with your supplier)' : '') + '.';
    }
  };
  window.FIXIT_CALC = CALC;

  document.querySelectorAll('form.calc').forEach(function (f) {
    var fn = CALC[f.getAttribute('data-calc')];
    var out = f.querySelector('.result');
    var run = function () { out.innerHTML = fn(f); };
    f.addEventListener('input', run);
    f.addEventListener('change', run);
    run();
  });
})();
