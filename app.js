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
        stageEl.style.background = getComputedStyle(stops[m].querySelector('.pole')).backgroundColor;
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

  // The yellow ball is your weight over the board. Where it sits decides what the board does.
  var deck = document.getElementById('deck'), ball = document.getElementById('ball'), say = document.getElementById('say');
  if (deck) {
    var pos = { x: 0, y: 0 }, tour = true, state = '';
    var clamp = function (v) { return Math.max(-1, Math.min(1, v)); };
    var read = function (p) {
      if (p.x < -0.35) return 'back';
      if (p.y > 0.35) return 'toes';
      if (p.y < -0.35) return 'heels';
      if (p.x > 0.35) return 'nose';
      return 'flat';
    };
    var place = function (x, y) {
      pos.x = clamp(x); pos.y = clamp(y);
      ball.style.left = (50 + pos.x * 37) + '%';
      ball.style.top = (50 - pos.y * 33) + '%';
      deck.style.setProperty('--edge', pos.y.toFixed(3));
      deck.style.setProperty('--nose', (pos.x * (1 - Math.abs(pos.y))).toFixed(3));
      deck.style.setProperty('--toe-on', Math.max(0, pos.y).toFixed(3));
      deck.style.setProperty('--heel-on', Math.max(0, -pos.y).toFixed(3));
      var now = read(pos);
      if (now !== state) { state = now; say.textContent = say.dataset[now]; }
    };
    var fromEvent = function (e) {
      var r = deck.getBoundingClientRect();
      place(((e.clientX - r.left) / r.width * 100 - 50) / 37, -((e.clientY - r.top) / r.height * 100 - 50) / 33);
    };
    var dragging = false;
    ball.addEventListener('pointerdown', function (e) { tour = false; dragging = true; ball.setPointerCapture(e.pointerId); e.preventDefault(); });
    ball.addEventListener('pointermove', function (e) { if (dragging) fromEvent(e); });
    ball.addEventListener('pointerup', function () { dragging = false; });
    ball.addEventListener('pointercancel', function () { dragging = false; });
    deck.addEventListener('click', function (e) { if (e.target !== ball) { tour = false; fromEvent(e); } });
    ball.addEventListener('keydown', function (e) {
      var d = { ArrowLeft: [-0.1, 0], ArrowRight: [0.1, 0], ArrowUp: [0, 0.1], ArrowDown: [0, -0.1] }[e.key];
      if (!d) return;
      e.preventDefault(); tour = false; place(pos.x + d[0], pos.y + d[1]);
    });
    place(0, 0);
    // Once, when it comes into view, the ball shows what it can do. Any touch ends this.
    if (!reduce) {
      var route = [[0, 0], [0.75, 0], [0, 0], [0, 0.8], [0, 0], [0, -0.8], [0, 0]];
      var shown = new IntersectionObserver(function (entries) {
        if (!entries[0].isIntersecting) return;
        shown.disconnect();
        var started = performance.now() + 500, leg = 1100;
        requestAnimationFrame(function step(now) {
          if (!tour) return;
          var t = Math.max(0, now - started) / leg, i = Math.floor(t);
          if (i >= route.length - 1) { place(0, 0); return; }
          var u = t - i, s = u * u * (3 - 2 * u);
          place(route[i][0] + (route[i + 1][0] - route[i][0]) * s, route[i][1] + (route[i + 1][1] - route[i][1]) * s);
          requestAnimationFrame(step);
        });
      }, { threshold: 0.6 });
      shown.observe(deck);
    }
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
  run.appendChild(track);
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
    var phone = W <= 760, room = parseFloat(getComputedStyle(document.querySelector('.who')).paddingRight);
    var near = W - room + (phone ? 10 : 22), far = W - (phone ? 10 : 20);
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
    board.setAttribute('transform', 'translate(' + p.x.toFixed(1) + ' ' + head.toFixed(1) + ') rotate(' + p.angle.toFixed(1) + ') scale(' + (W <= 760 ? 0.5 : 0.72) + ')');
  }

  window.addEventListener('scroll', function () {
    if (!ticking) { ticking = true; requestAnimationFrame(draw); }
  }, { passive: true });
  new ResizeObserver(layout).observe(run);
  layout();
})();
