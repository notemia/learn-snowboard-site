#!/usr/bin/env python3
"""Builds the one-page snowboard site (one page per language) from lang_*.py and docs_*.py.

Run:  python3 _src/build.py   (from the repo root)
Course names, level names and lesson names come from the app's own string
catalog, so the site always says exactly what the app says.
"""
import hashlib, html, json, importlib, os, re, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)                    # repo root, served as the site
ROOT = SITE
CATALOG = os.environ.get('SNOWBOARD_XCSTRINGS',
    '/Users/vladimir/claude/SnowboardFeelTheTurn/SnowboardFeelTheTurn/Localization/Localizable.xcstrings')
sys.path.insert(0, HERE)

# code -> (folder, hreflang, og:locale, app catalog key, native name)
LANGS = [
    ('en', '',     'en',      'en_US', 'en',      'English'),
    ('ru', 'ru/',  'ru',      'ru_RU', 'ru',      'Русский'),
    ('de', 'de/',  'de',      'de_DE', 'de',      'Deutsch'),
    ('es', 'es/',  'es',      'es_ES', 'es',      'Español'),
    ('fr', 'fr/',  'fr',      'fr_FR', 'fr',      'Français'),
    ('it', 'it/',  'it',      'it_IT', 'it',      'Italiano'),
    ('ja', 'ja/',  'ja',      'ja_JP', 'ja',      '日本語'),
    ('ko', 'ko/',  'ko',      'ko_KR', 'ko',      '한국어'),
    ('zh', 'zh/',  'zh-Hans', 'zh_CN', 'zh-Hans', '简体中文'),
]
BASE = 'https://learn-snowboard.fun/'
STR = json.load(open(CATALOG, encoding='utf-8'))['strings']

def app(key, ck):
    return STR[key]['localizations'][ck]['stringUnit']['value']

LEVELS = [('level.safety', [17, 18]), ('level1', [11, 10, 2]), ('level2', [12, 6]), ('level.lifts', [20, 21]),
          ('level3', [1, 13, 4, 8, 19]), ('level4', [5, 14, 7, 15]), ('level5', [3, 9, 22, 23, 16])]
assert sum(len(l) for _, l in LEVELS) == 23

e = lambda s: html.escape(s, quote=False)
a = lambda s: html.escape(s, quote=True)

def fit(word, code):
    """Viewport-relative size that makes the product name fill the line, in any script."""
    per_char = 1.02 if code in ('ja', 'ko', 'zh') else 0.385
    return round(92 / (len(word) * per_char), 1)

MAIL = 'mailto:helpyoutofeel@gmail.com'

GREEN, BLUE, RED, BLACK = '#218f54', '#2668d8', '#d13333', '#142238'
lesson_line = lambda n: (lambda ck, d: app(f'lesson{n}.title', ck))
# Film chapters: start in seconds, piste color, the line shown.
FILM = [(0, GREEN, lesson_line(2)), (3.65, GREEN, lesson_line(21)), (11.3, BLUE, lesson_line(1)), (15.95, BLUE, lesson_line(4)),
        (22.6, BLUE, lesson_line(18)), (28.9, RED, lesson_line(14)), (34.55, RED, lesson_line(15)), (46.2, BLACK, lambda ck, d: d['m_h2'])]
FILM_END = 70.27

def icon(name):
    """Icon address tied to the file's content: Cloudflare lets browsers keep images for hours."""
    with open(os.path.join(SITE, 'assets', name), 'rb') as f:
        return f'/assets/{name}?v={hashlib.md5(f.read()).hexdigest()[:8]}'

def head_tags(url, hl, ogl, code, title, desc, alt, image=True):
    og = f"""<meta property="og:image" content="{BASE}assets/og-{code}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
""" if image else ''
    return f"""<!doctype html>
<html lang="{hl}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{a(desc)}">
<link rel="canonical" href="{url}">
{alt}<meta name="theme-color" content="#7fa3cc">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Snowboarding">
<meta property="og:title" content="{a(title)}">
<meta property="og:description" content="{a(desc)}">
<meta property="og:url" content="{url}">
{og}<meta property="og:locale" content="{ogl}">
<link rel="icon" href="{icon('icon-64.png')}" type="image/png">
<link rel="apple-touch-icon" href="{icon('icon-180.png')}">
<link rel="stylesheet" href="/style.css">
"""

def header(code, folder, native, d, page=''):
    return f"""<header class="top">
  <a class="brand" href="/{folder}"><img src="{icon('icon-64.png')}" alt="" width="32" height="32"><span>Snowboarding</span></a>
  <nav><a href="/{folder}support.html">{e(d['foot_support'])}</a><a href="/{folder}privacy.html">{e(d['foot_privacy'])}</a>
  <details class="langs"><summary aria-label="{a(d['lang_label'])}">{e(native)}</summary><div>{lang_menu(code, page)}</div></details></nav>
</header>
"""

def footer(folder, d):
    return f"""<footer>
  <small>{e(d['foot'])}<br>© 2026 Vladimir Dyagay</small>
  <nav><a href="/{folder}support.html">{e(d['foot_support'])}</a><a href="/{folder}privacy.html">{e(d['foot_privacy'])}</a><a href="https://notemia.app/">Notemia apps</a></nav>
</footer>
<script src="/app.js"></script>
</body>
</html>
"""

def alternates(page=''):
    alt = ''.join(f'<link rel="alternate" hreflang="{h}" href="{BASE}{f}{page}">\n' for _, f, h, *_ in LANGS)
    return alt + f'<link rel="alternate" hreflang="x-default" href="{BASE}{page}">\n'

def build(code, folder, hl, ogl, ck, native, d):
    url = BASE + folder
    mail = MAIL + '?subject=' + urllib.parse.quote(d['notify_subject'], safe='')
    name = re.sub(r'[\s:：]+$', '', d['h1a'])
    app_ld = {"@context": "https://schema.org", "@type": "MobileApplication", "name": "Snowboarding",
              "alternateName": "Snowboarding: Lessons & Game", "url": url, "inLanguage": hl, "description": d['desc'],
              "applicationSubCategory": "Snowboarding lessons and riding game", "operatingSystem": "iOS 18 or later",
              "applicationCategory": "SportsApplication", "image": BASE + "assets/icon.png",
              "screenshot": [BASE + "assets/game.jpg"],
              "author": {"@type": "Person", "name": "Vladimir Dyagay"}}
    ld = json.dumps(app_ld, ensure_ascii=False).replace('</', '<\\/')
    # One day on the mountain, one film for every language: the line over it is the lesson's own name.
    # The rail's colors climb like piste colors, as the lessons get harder.
    rail = ''.join(
        f'<li style="flex:{end - at:.2f}"><button type="button" data-at="{at}" data-line="{a(title(ck, d))}" aria-label="{a(title(ck, d))}" style="--pole:{pole}"><i></i></button></li>'
        for (at, end), pole, title in zip(zip([c[0] for c in FILM], [c[0] for c in FILM[1:]] + [FILM_END]), [c[1] for c in FILM], [c[2] for c in FILM]))
    first = FILM[0][2](ck, d)
    levels = ''.join(f'<li><b class="pole">{i}</b>{e(app(stem + ".title", ck))}</li>' for i, (stem, _) in enumerate(LEVELS, 1))
    return head_tags(url, hl, ogl, code, d['title'], d['desc'], alternates()) + f"""<script type="application/ld+json">{ld}</script>
</head>
<body>
{header(code, folder, native, d)}
<main>
<div class="hero">
  <h1><span style="--fit:{fit(name, code)}vw">{e(name)}</span>{e(d['h1b'])}</h1>
  <div class="pitch">
    <p>{e(d['sub'])}</p>
    <a class="btn" href="{a(mail)}">{e(d['cta2'])}</a>
  </div>
  <video data-loop muted loop playsinline preload="metadata" poster="{icon('game.jpg')}" aria-label="{a(d['hero_aria'])}" width="640" height="1312"><source src="{icon('game.mp4')}" type="video/mp4"></video>
</div>
<div class="run" id="run">
  <section class="gate"><div class="in">
    <h2>{e(d['c_h2'])}</h2>
    <ol class="levels">{levels}</ol>
  </div></section>
  <section class="film" aria-label="{a(d['g_h2'])}">
    <div class="screen">
      <video data-loop data-film muted loop playsinline preload="metadata" poster="{icon('film.jpg')}" width="1280" height="720"><source src="{icon('film.mp4')}" type="video/mp4"></video>
      <p class="line">{e(first)}</p>
    </div>
    <ol class="rail">{rail}</ol>
  </section>
</div>
</main>
""" + footer(folder, d)

def build_doc(kind, code, folder, hl, ogl, native, d, X):
    """kind: 'privacy' or 'support'. App Store Connect links to these addresses."""
    page = kind + '.html'
    body = []
    if kind == 'privacy':
        body.append(f'<p class="short"><strong>{e(X["short_label"])}</strong> {e(X["short"])}</p>')
        for h, p in X['sections']:
            body.append(f'<h2>{e(h)}</h2><p>{e(p)}</p>')
        body.append(f'<h2>{e(X["contact_h"])}</h2><p><a href="{MAIL}">helpyoutofeel@gmail.com</a></p>')
    else:
        body.append('<div class="contact">' + ''.join(
            f'<p><strong>{e(h)}</strong>{e(p)}</p><a class="btn {c}" href="{a(MAIL + "?subject=" + urllib.parse.quote(sub, safe=""))}">{e(b)}</a>'
            for (h, p, b, sub), c in zip(X['cards'], ('', 'line'))) + '</div>')
        body.append('<div class="rows">' + ''.join(f'<details><summary>{e(q)}</summary><p>{e(t)}</p></details>' for q, t in X['faq']) + '</div>')
    return head_tags(BASE + folder + page, hl, ogl, code, X['title'], X['desc'], alternates(page), image=False) + f"""</head>
<body class="plain">
{header(code, folder, native, d, page)}
<main class="doc">
  <h1>{e(X['h1'])}</h1>
  <p class="quiet">{e(X['sub'])}</p>
  {''.join(body)}
</main>
""" + footer(folder, d)

def check(code, d):
    need = ['title','desc','lang_label','h1a','h1b','sub','cta2','notify_subject','hero_aria','g_h2','c_h2','foot','foot_support','foot_privacy']
    miss = [k for k in need if k not in d]
    assert not miss, (code, miss)

def lang_menu(code, page=''):
    return ''.join(f'<a href="/{f2}{page}" hreflang="{h2}" lang="{h2}"' + (' aria-current="true"' if c2 == code else '') + f'>{n2}</a>'
                   for c2, f2, h2, _o, _k, n2 in LANGS)

def check_doc(code, P, S):
    for k in ['title','desc','h1','sub','short_label','short','sections','contact_h']:
        assert k in P, (code, 'P', k)
    assert len(P['sections']) == 7, (code, len(P['sections']))
    for k in ['title','desc','h1','sub','cards','faq']:
        assert k in S, (code, 'S', k)
    assert len(S['cards']) == 2 and len(S['faq']) == 13, (code, len(S['faq']))

def main():
    for code, folder, hl, ogl, ck, native in LANGS:
        d = importlib.import_module('lang_' + code).D
        dm = importlib.import_module('docs_' + code)
        check(code, d)
        check_doc(code, dm.P, dm.S)
        out = os.path.join(SITE, folder, 'index.html')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf-8').write(build(code, folder, hl, ogl, ck, native, d))
        for kind, X in (('privacy', dm.P), ('support', dm.S)):
            open(os.path.join(SITE, folder, kind + '.html'), 'w', encoding='utf-8').write(build_doc(kind, code, folder, hl, ogl, native, d, X))
        print('wrote', os.path.relpath(out, ROOT))
    blocks = ''
    for pg in ('', 'privacy.html', 'support.html'):
        alts = ''.join(f'    <xhtml:link rel="alternate" hreflang="{h}" href="{BASE}{f}{pg}"/>\n' for _, f, h, *_ in LANGS) + f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}{pg}"/>\n'
        blocks += ''.join(f'  <url><loc>{BASE}{f}{pg}</loc>\n{alts}  </url>\n' for _, f, *_ in LANGS)
    head = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(head + blocks + '</urlset>\n')

if __name__ == '__main__':
    main()
