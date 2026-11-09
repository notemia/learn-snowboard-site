(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Language menu: close on outside click or Escape.
  var langs = document.querySelector('.langs');
  if (langs) {
    document.addEventListener('click', function (e) { if (!langs.contains(e.target)) langs.open = false; });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') langs.open = false; });
  }

  // Only the video most on screen plays, so a phone never decodes two at once.
  var videos = [].slice.call(document.querySelectorAll('video[data-loop]'));
  var share = videos.map(function () { return 0; });
  if (reduce) {
    videos.forEach(function (v) { v.controls = true; });
  } else {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { share[videos.indexOf(e.target)] = e.isIntersecting ? e.intersectionRatio : 0; });
      var best = share.indexOf(Math.max.apply(null, share));
      videos.forEach(function (v, i) {
        if (i === best && share[i] >= 0.25) { v.play().catch(function () {}); } else { v.pause(); }
      });
    }, { threshold: [0, 0.25, 0.5, 0.75, 1] });
    videos.forEach(function (v) { seen.observe(v); });
  }

  // The film: its captions follow the picture, and the levels jump to their part.
  var film = document.querySelector('video[data-film]');
  if (film) {
    var lineEl = document.querySelector('.line'), stageEl = document.querySelector('.stage');
    var lines = JSON.parse(document.getElementById('film-lines').textContent);
    var stops = [].slice.call(document.querySelectorAll('.levels button'));
    var marks = stops.map(function (b) { return parseFloat(b.dataset.at); });
    var line = -1, stage = -1;
    var sync = function () {
      var t = film.currentTime, n = lines.length - 1, m = marks.length - 1;
      while (n > 0 && lines[n][0] > t) n--;
      while (m > 0 && marks[m] > t) m--;
      if (n !== line) { line = n; lineEl.textContent = lines[n][1]; }
      if (m !== stage) {
        if (stage >= 0) { stops[stage].removeAttribute('aria-current'); stops[stage].style.removeProperty('--done'); }
        stage = m;
        stops[m].setAttribute('aria-current', 'true');
        stageEl.textContent = stops[m].querySelector('span').textContent;
      }
      var end = m + 1 < marks.length ? marks[m + 1] : (film.duration || t + 1);
      stops[m].style.setProperty('--done', Math.min(1, (t - marks[m]) / (end - marks[m])).toFixed(3));
    };
    film.addEventListener('timeupdate', sync);
    film.addEventListener('seeked', sync);
    stops.forEach(function (b, i) {
      b.addEventListener('click', function () { film.currentTime = marks[i] + 0.05; sync(); film.play().catch(function () {}); });
    });
    sync();
  }

  // The track: one S-line down the run, carved as you scroll.
  // Orange on toe-side arcs and teal on heel-side arcs, like the app's edges.
  var run = document.getElementById('run');
  if (!run) return;
  var NS = 'http://www.w3.org/2000/svg';
  function el(name, attrs, parent) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  var track = el('svg', { class: 'track', 'aria-hidden': 'true' });
  var rider = el('svg', { class: 'rider', 'aria-hidden': 'true' });
  var clip = el('rect', { x: 0, y: 0, width: 0, height: 0 }, el('clipPath', { id: 'carved' }, track));
  var carved = el('g', { 'clip-path': 'url(#carved)' }, track);
  var board = el('g', {}, rider);
  el('rect', { x: -36, y: -8.5, width: 72, height: 17, rx: 8.5, fill: '#12a5a2', stroke: '#15174f', 'stroke-width': 2.5 }, board);
  el('rect', { x: -22, y: -7, width: 4, height: 14, fill: '#f4661b' }, board);
  el('rect', { x: 18, y: -7, width: 4, height: 14, fill: '#f4661b' }, board);
  el('rect', { x: -15, y: -6, width: 9, height: 12, rx: 3, fill: '#15174f' }, board);
  el('rect', { x: 6, y: -6, width: 9, height: 12, rx: 3, fill: '#15174f' }, board);
  run.prepend(track);
  run.appendChild(rider);

  var apex = [];
  var mid = function (p, q) { return { x: (p.x + q.x) / 2, y: (p.y + q.y) / 2 }; };
  var f = function (p) { return p.x.toFixed(1) + ' ' + p.y.toFixed(1); };

  // Split the S between two apexes at its centre, where the edge changes.
  function halves(a, b) {
    var h = (b.y - a.y) / 2;
    var q1 = { x: a.x, y: a.y + h / 2 }, q3 = { x: b.x, y: b.y - h / 2 }, q2 = mid(a, b);
    var r1 = mid(q1, q2), r2 = mid(q2, q3);
    return { first: 'C' + f(q1) + ' ' + f(r1) + ' ' + f(q2), second: 'C' + f(r2) + ' ' + f(q3) + ' ' + f(b), m: q2 };
  }

  // The track swings in the free strip on the right, one turn every few hundred pixels.
  function apexes(W, H) {
    var phone = W <= 760;
    var near = phone ? W - 44 : W * 0.915, far = phone ? W - 12 : W * 0.975;
    var step = phone ? 300 : 230, pts = [], right = false;
    for (var y = 24; y < H - step / 2; y += step, right = !right) pts.push({ x: right ? far : near, y: y, toe: right });
    pts.push({ x: right ? far : near, y: H, toe: right });
    return pts;
  }

  var W = 0, H = 0, ticking = false;
  function layout() {
    W = run.clientWidth; H = run.offsetHeight;
    apex = apexes(W, H);
    [track, rider].forEach(function (s) { s.setAttribute('viewBox', '0 0 ' + W + ' ' + H); });
    clip.setAttribute('width', W);
    while (carved.firstChild) carved.removeChild(carved.firstChild);
    var whole = 'M' + f(apex[0]);
    var arcs = [];
    for (var i = 0; i < apex.length; i++) {
      var inn = i > 0 ? halves(apex[i - 1], apex[i]) : null, out = i < apex.length - 1 ? halves(apex[i], apex[i + 1]) : null;
      var d = 'M' + f(inn ? inn.m : apex[i]) + (inn ? inn.second : '') + (out ? out.first : '');
      if (inn) whole += inn.first + inn.second;
      arcs.push({ d: d, toe: apex[i].toe });
    }
    el('path', { class: 'groove', d: whole }, carved);
    arcs.forEach(function (a) { el('path', { class: 'edge ' + (a.toe ? 'toe' : 'heel'), d: a.d }, carved); });
    draw();
  }

  // Where the S is at height y: bisect the cubic, then read its slope.
  function at(y) {
    var i = 0;
    while (i < apex.length - 2 && apex[i + 1].y < y) i++;
    var a = apex[i], b = apex[i + 1], h = (b.y - a.y) / 2, lo = 0, hi = 1, t = 0, u, yt;
    for (var n = 0; n < 18; n++) {
      t = (lo + hi) / 2; u = 1 - t;
      yt = u * u * u * a.y + 3 * u * u * t * (a.y + h) + 3 * u * t * t * (b.y - h) + t * t * t * b.y;
      if (yt < y) lo = t; else hi = t;
    }
    u = 1 - t;
    var x = a.x * (u * u * u + 3 * u * u * t) + b.x * (3 * u * t * t + t * t * t);
    var dx = 6 * u * t * (b.x - a.x);
    var dy = 3 * u * u * h + 6 * u * t * (b.y - h - a.y - h) + 3 * t * t * h;
    return { x: x, angle: Math.atan2(dy, dx) * 180 / Math.PI };
  }

  // The whole run is ridden over the page's scroll, however short the page is.
  function progress() {
    var room = document.documentElement.scrollHeight - window.innerHeight;
    return room > 0 ? Math.min(window.scrollY / room, 1) : 0;
  }

  function draw() {
    ticking = false;
    var head = reduce ? H : 40 + (H - 42) * progress();
    clip.setAttribute('height', head);
    board.style.display = reduce ? 'none' : '';
    if (reduce) return;
    var p = at(head);
    board.setAttribute('transform', 'translate(' + p.x.toFixed(1) + ' ' + head.toFixed(1) + ') rotate(' + p.angle.toFixed(1) + ') scale(' + (W <= 760 ? 0.68 : 1) + ')');
  }

  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(draw); }
  }, { passive: true });
  new ResizeObserver(layout).observe(run);
  layout();
})();
