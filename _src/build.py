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
# The app's App Store name in each language, shown beside the logo.
METADATA = os.environ.get('SNOWBOARD_METADATA', '/Users/vladimir/claude/SnowboardFeelTheTurn/fastlane/metadata')
STORE_LOCALE = {'en': 'en-US', 'ru': 'ru', 'de': 'de-DE', 'es': 'es-ES', 'fr': 'fr-FR', 'it': 'it', 'ja': 'ja', 'ko': 'ko', 'zh': 'zh-Hans'}
def store_name(code):
    with open(os.path.join(METADATA, STORE_LOCALE[code], 'name.txt'), encoding='utf-8') as f:
        return f.read().strip()
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

# The film: every caption is the app's own text, so one video serves all languages.
FILM = json.load(open(os.path.join(HERE, 'film.json'), encoding='utf-8'))

def film_line(key, ck, d):
    return d[key[5:]] if key.startswith('site:') else app(key, ck)

def icon(name):
    """Icon address tied to the file's content: Cloudflare lets browsers keep images for hours."""
    with open(os.path.join(SITE, 'assets', name), 'rb') as f:
        return f'/assets/{name}?v={hashlib.md5(f.read()).hexdigest()[:8]}'

def favicon_ico():
    with open(os.path.join(SITE, 'favicon.ico'), 'rb') as f:
        return f'/favicon.ico?v={hashlib.md5(f.read()).hexdigest()[:8]}'

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
<meta property="og:site_name" content="{a(store_name(code))}">
<meta property="og:title" content="{a(title)}">
<meta property="og:description" content="{a(desc)}">
<meta property="og:url" content="{url}">
{og}<meta property="og:locale" content="{ogl}">
<link rel="icon" href="{favicon_ico()}" sizes="any">
<link rel="icon" href="{icon('favicon-32.png')}" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{icon('icon-180.png')}">
<link rel="stylesheet" href="/style.css">
"""

def header(code, folder, native, d, page=''):
    return f"""<header class="top">
  <a class="brand" href="/{folder}"><img src="{icon('icon-64.png')}" alt="" width="32" height="32"><span>{e(store_name(code))}</span></a>
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
    app_ld = {"@context": "https://schema.org", "@type": "MobileApplication", "name": store_name(code),
              "url": url, "inLanguage": hl, "description": d['desc'],
              "applicationSubCategory": "Snowboarding lessons and riding game", "operatingSystem": "iOS 18 or later",
              "applicationCategory": "SportsApplication", "image": BASE + "assets/icon.png",
              "screenshot": [BASE + "assets/game.jpg"],
              "author": {"@type": "Person", "name": "Vladimir Dyagay"}}
    ld = json.dumps(app_ld, ensure_ascii=False).replace('</', '<\\/')
    # The curriculum list doubles as the film's chapters. Levels the film skips are plain text.
    starts = {stem: at for stem, at in FILM['stages']}
    def level(i, stem):
        name = e(app(stem + ".title", ck))
        pole = f'<b class="pole">{i}</b>'
        if stem not in starts:
            return f'<li>{pole}<span>{name}</span></li>'
        return f'<li><button type="button" data-at="{starts[stem]}">{pole}<span>{name}</span></button></li>'
    levels = ''.join(level(i, stem) for i, (stem, _) in enumerate(LEVELS, 1))
    lines = json.dumps([[at, film_line(key, ck, d)] for at, key in FILM['lines']], ensure_ascii=False).replace('</', '<\\/')
    who = ''.join(f'<div><dt>{e(a_)}</dt><dd>{e(b_)}</dd></div>' for a_, b_ in d['who'])
    first_stage = e(app(FILM['stages'][0][0] + ".title", ck))
    first_line = e(film_line(FILM['lines'][0][1], ck, d))
    return head_tags(url, hl, ogl, code, d['title'], d['desc'], alternates()) + f"""<script type="application/ld+json">{ld}</script>
</head>
<body>
{header(code, folder, native, d)}
<main>
<div class="hero">
  <h1><span style="--fit:{fit(name, code)}vw">{e(name)}</span>{e(d['h1b'])}</h1>
  <div class="pitch">
    <p>{e(d['short'])}</p>
    <a class="btn" href="{a(mail)}">{e(d['cta2'])}</a>
  </div>
  <video data-loop muted loop playsinline preload="metadata" poster="{icon('game.jpg')}" aria-label="{a(d['hero_aria'])}" width="640" height="1312"><source src="{icon('game.mp4')}" type="video/mp4"></video>
</div>
<div class="run" id="run">
<section class="why">
  <div class="why-in">
    <div class="why-text">
      <h2>{e(d['why_h'])}</h2>
      <p>{e(d['sub'])}</p>
      <p>{e(d['sub2'])}</p>
    </div>
    <figure class="try">
      <figcaption>{e(d['t_try'])}</figcaption>
      <div class="deck" id="deck">
        <span class="dir toes">{e(d['t_toes'])}</span><span class="dir heels">{e(d['t_heels'])}</span><span class="dir nose">{e(d['t_nose'])}</span><span class="dir tail">{e(d['t_tail'])}</span>
        <svg class="board" viewBox="0 0 520 130" aria-hidden="true"><path class="sheet" d="M58 12H462C500 12 512 42 512 65S500 118 462 118H58C20 118 8 88 8 65S20 12 58 12Z"/><path class="edge-toe" d="M58 12H462"/><path class="edge-heel" d="M58 118H462"/><rect class="stripe" x="82" y="30" width="12" height="70" rx="3"/><rect class="stripe" x="426" y="30" width="12" height="70" rx="3"/><rect class="bind" x="148" y="34" width="44" height="62" rx="12"/><rect class="bind" x="328" y="34" width="44" height="62" rx="12"/></svg>
        <button type="button" class="ball" id="ball" aria-label="{a(d['t_ball'])}"></button>
      </div>
      <p class="say" id="say" aria-live="polite" data-flat="{a(d['pad']['flat'])}" data-nose="{a(d['pad']['nose'])}" data-toes="{a(d['pad']['toes'])}" data-heels="{a(d['pad']['heels'])}" data-back="{a(d['pad']['back'])}">{e(d['pad']['flat'])}</p>
      <small>{e(d['t_hint'])}</small>
    </figure>
  </div>
</section>
<section class="who">
  <h2>{e(d['who_h'])}</h2>
  <dl>{who}</dl>
</section>
<section class="columns">
  <div class="plan">
    <h2>{e(d['c_h2'])}</h2>
    <p class="lead">{e(d['c_lead'])}</p>
    <ol class="levels">{levels}</ol>
    <p class="game">{e(d['game_line'])}</p>
  </div>
  <div class="screen" role="group" aria-label="{a(d['g_h2'])}">
    <video data-loop data-film muted loop playsinline preload="metadata" poster="{icon('film.jpg')}" width="640" height="1312"><source src="{icon('film.mp4')}" type="video/mp4"></video>
    <p class="stage">{first_stage}</p>
    <p class="line">{first_line}</p>
  </div>
  <script type="application/json" id="film-lines">{lines}</script>
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
    need = ['why_h','short','sub2','who_h','who','game_line','c_lead','title','desc','lang_label','h1a','h1b','sub','cta2','notify_subject','hero_aria','g_h2','c_h2','foot','foot_support','foot_privacy']
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
