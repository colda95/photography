import copy, hashlib, html, os, json, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

# Genera tutte le pagine del sito, in italiano e in inglese:
#   home (index.html), album (usa-2026/), pagine dei temi (temi/<slug>/); in inglese le stesse sotto en/.
# Fonti: content_usa.py (struttura dell'album), testi_utente.json (testi italiani), testi_en.json (testi inglesi),
#        temi.py (temi), e il dizionario UI qui sotto (testi fissi di home, menu, pulsanti).
# Uso, dalla cartella principale del repository:  python3 _sorgenti/build_site.py
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                   # cartella principale del repository
REPO_DIR = 'USA-2026-places-web-2880'  # foto a piena risoluzione (schermo intero)
PAGE_DIR = 'USA-2026-places-web-2048'  # foto mostrate nella pagina
SRC = os.path.join(ROOT, REPO_DIR)
OUT = os.environ.get('OUT', ROOT)              # dove scrivere le pagine (di default: il repository)
AUTHOR = 'Dario Coluzzi'
SITE_TITLE = 'Dario Coluzzi'
SITE_URL = 'https://colda95.github.io/photography/'
EMAIL = ''                                     # indirizzo email mostrato in Contatti (vuoto = non mostrato)
GITHUB = 'https://github.com/colda95'
HOME_IMAGE = '20260409-3W9A7813-HDR'           # foto grande in cima alla home
LANGS = ('it', 'en')                           # la prima è la lingua principale (pagine nella radice)
sys.path.insert(0, HERE)
from content_usa import ALBUM as ALBUM_IT, CHAPTERS as CHAPTERS_IT
from temi import THEMES
import mappa
try:
    from content_usa import GPS as GPS_FIX
except ImportError:
    GPS_FIX = {}

# Testi fissi del sito (tutto ciò che non dipende dall'album).
UI = {
    'it': dict(
        html_lang='it', locale='it_IT', rights='Tutti i diritti riservati.', lang_nav='Lingua',
        menu=(('album', 'Album'), ('temi', 'Temi'), ('progetti', 'Progetti'), ('contatti', 'Contatti')), nav='Menu principale',
        open_full='Apri a schermo intero', open_map='Apri sulla mappa', chapter='Capitolo',
        route_kicker='Il percorso', route_title='Nove tappe, tre stati',
        col_photos='Fotografie', col_camera='Fotocamera', col_lenses='Obiettivi', col_dev='Sviluppo', col_map='Mappa',
        map_credit='Fiumi, laghi e confini: Natural Earth<br>Rilievo: NASA SRTM, tramite OpenTopography',
        all_albums='Torna alla home', rotate='Ruota il telefono per vederla più grande', close='Chiudi',
        home_title='Fotografie', home_desc='Le fotografie di {author}: paesaggi, animali, strade e viaggi.',
        home_sub='Fotografo per passione. Paesaggi, animali e strade, e la luce delle ore più belle.',
        home_alt='Alba sull’anfiteatro di Bryce Canyon',
        albums_h='Album', albums_p='Viaggi raccontati dall’inizio alla fine, capitolo per capitolo.',
        album_facts='{k0}, {k1}. {n} fotografie in {c} capitoli.', open_album='Apri l’album',
        themes_h='Temi', themes_p='Le fotografie raccolte per soggetto, oltre i confini dei singoli viaggi.',
        count='{n} fotografie', other_themes='Altri temi',
        from_album='Dall’album {album}, capitolo {num}',
        projects_h='Altri progetti', projects_p='Quello che succede intorno alle fotografie.',
        projects=(
            ('Mappe in rilievo', 'Per ogni viaggio disegno la mappa del percorso: fiumi e confini da Natural Earth, rilievo calcolato dal modello del terreno della NASA.',
             'Guarda la mappa di Terra rossa', '{up}{base}usa-2026/#mappa'),
            ('Questo sito', 'Lo scrivo e lo pubblico da solo, con qualche script in Python. Niente piattaforme e niente pubblicità: solo pagine leggere che mettono le foto al centro.',
             'Il codice su GitHub', GITHUB)),
        contact_h='Contatti', contact_p='Per una stampa, per usare una foto o anche solo per un saluto, scrivimi.',
        foot='© {year} {author}. Tutti i diritti riservati. Fotografie e testi non possono essere riprodotti senza autorizzazione scritta.'),
    'en': dict(
        html_lang='en', locale='en_US', rights='All rights reserved.', lang_nav='Language',
        menu=(('album', 'Albums'), ('temi', 'Themes'), ('progetti', 'Projects'), ('contatti', 'Contact')), nav='Main menu',
        open_full='View full screen', open_map='View on map', chapter='Chapter',
        route_kicker='The route', route_title='Nine stops, three states',
        col_photos='Photographs', col_camera='Camera', col_lenses='Lenses', col_dev='Editing', col_map='Map',
        map_credit='Rivers, lakes and borders: Natural Earth<br>Relief: NASA SRTM, via OpenTopography',
        all_albums='Back to home', rotate='Turn your phone sideways for a bigger view', close='Close',
        home_title='Photography', home_desc='Photographs by {author}: landscapes, wildlife, the open road and travel.',
        home_sub='Photography, mostly. Landscapes, wildlife, the open road, and the light at either end of the day.',
        home_alt='Sunrise over the Bryce Canyon amphitheater',
        albums_h='Albums', albums_p='Trips told from start to finish, chapter by chapter.',
        album_facts='{k0}, {k1}. {n} photographs in {c} chapters.', open_album='View the album',
        themes_h='Themes', themes_p='Photographs grouped by subject, across every trip.',
        count='{n} photographs', other_themes='More themes',
        from_album='From {album}, chapter {num}',
        projects_h='Other projects', projects_p='What happens around the photographs.',
        projects=(
            ('Shaded relief maps', 'For every trip I draw a map of the route: rivers and borders from Natural Earth, terrain shading computed from NASA elevation data.',
             'See the Red Earth map', '{up}{base}usa-2026/#mappa'),
            ('This site', 'I write and publish it myself with a few Python scripts. No platforms, no ads, just lightweight pages that put the photos first.',
             'Code on GitHub', GITHUB)),
        contact_h='Contact', contact_p='For a print, to license a photo, or just to say hi, drop me a line.',
        foot='© {year} {author}. All rights reserved. No photographs or text may be reproduced without written permission.'),
}
TEXTS = {'it': 'testi_utente.json', 'en': 'testi_en.json'}


def load(lang):
    """Album e capitoli con i testi della lingua scelta. I testi nei file JSON hanno la precedenza su content_usa.py."""
    album, chapters = copy.deepcopy(ALBUM_IT), copy.deepcopy(CHAPTERS_IT)
    album.update(hero_title='Terra rossa', hero_alt='La US-163 verso Monument Valley all’ultima luce',
                 cover_alt='La US-163 verso Monument Valley all’ultima luce', map_names=None)
    path = os.path.join(HERE, TEXTS[lang])
    if not os.path.exists(path):
        assert lang == 'it', f'Manca {TEXTS[lang]}'
        return album, chapters
    _u = json.load(open(path, encoding='utf-8'))
    album['lede'] = _u.get('lede', album['lede'])
    album['meta_description'] = _u.get('meta_description')
    album['footer_copy'] = _u.get('footer_copy')
    for k in ('title', 'hero_title', 'hero_alt', 'cover_alt', 'map_names'):
        if k in _u: album[k] = _u[k]
    album['hero_title'] = album['hero_title'].replace('<br>', ' ')
    if 'kicker' in _u: album['kicker'] = tuple(_u['kicker'])
    for _ch in chapters:
        _ch['title'] = _u.get('chapter_titles', {}).get(_ch['num'], _ch['title'])
        _ch['route_title'] = _u.get('route_titles', {}).get(_ch['num'], _ch['title'])
        _ch['date'] = _u.get('chapter_dates', {}).get(_ch['num'], _ch['date'])
    for _ch, _intro in zip(chapters, _u.get('intros', [])): _ch['intro'] = _intro
    missing = []
    def _fix(p):
        c = _u.get('captions', {}).get(p[0])
        if not c: missing.append(p[0])
        return (p[0], c[0], c[1], *p[3:]) if c else p
    for _ch in chapters:
        _ch['blocks'] = [(b[0], _fix(b[1])) if b[0] in ('full', 'wide') else (b[0], [_fix(p) for p in b[1]]) if b[0] == 'group'
                         else (b[0], _fix(b[1]), _fix(b[2]), b[3]) for b in _ch['blocks']]
    if lang != 'it' and missing:
        print(f'ATTENZIONE: didascalie mancanti in {TEXTS[lang]} (resta il testo italiano):', ', '.join(missing))
    return album, chapters

LENS = {
    'RF24-105mm F4 L IS USM': ('RF 24–105 mm f/4L', 'RF 24–105 mm f/4L IS USM'),
    '16mm F1.4 DC DN | Contemporary 017': ('Sigma 16 mm f/1.4', 'Sigma 16 mm f/1.4 DC DN Contemporary'),
    'RF100-400mm F5.6-8 IS USM': ('RF 100–400 mm', 'RF 100–400 mm f/5.6–8 IS USM'),
}
esc = html.escape

def process(name):
    """Legge dal file a piena risoluzione i dati di scatto, le dimensioni e la posizione GPS."""
    im = Image.open(f'{SRC}/{name}.jpg')
    ex = im.getexif(); sub = ex.get_ifd(0x8769)
    t = float(sub[33434]); sh = f'1/{round(1/t)} s' if t < 1 else f'{t:g} s'
    info = dict(
        exif=f'{float(sub[37386]):g} mm · f/{float(sub[33437]):g} · {sh} · ISO {sub[34855]}',
        time=sub.get(36867, '')[11:16], date=sub.get(36867, '')[:10], lens=sub.get(42036), gps=None)
    g = ex.get_ifd(0x8825)
    if g and 2 in g:
        dm = lambda v, r: (float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600) * (-1 if r in ('S', 'W') else 1)
        info['gps'] = (dm(g[2], g[1]), dm(g[4], g[3]))
    im = ImageOps.exif_transpose(im)
    info['w'], info['h'] = im.size
    return name, info

def blocks_photos(b):
    if b[0] in ('full', 'wide'): return [b[1]]
    if b[0] == 'group': return list(b[1])
    if b[0] == 'offset': return [b[1], b[2]]
    raise ValueError(b[0])

def all_names(chapters=CHAPTERS_IT):
    for ch in chapters:
        for b in ch['blocks']:
            for p in blocks_photos(b): yield p[0]

# ---------- lingue ----------
def lang_path(lang, path=''):
    """Percorso di una pagina (relativo alla radice del sito) nella lingua data."""
    return path if lang == LANGS[0] else f'{lang}/{path}'

def lang_href(l, path, up):
    return (up + lang_path(l, path)) or './'

def lang_switch(lang, path, up):
    links = []
    for l in LANGS:
        cur = ' aria-current="page"' if l == lang else ''
        links.append(f'<a href="{lang_href(l, path, up)}" lang="{l}" hreflang="{l}" data-lang="{l}"{cur}>{l.upper()}</a>')
    return f'<div class="lang" role="group" aria-label="{UI[lang]["lang_nav"]}">' + '<span aria-hidden="true">/</span>'.join(links) + '</div>'

def lang_script(lang, path, up):
    """Lingua automatica. Se il visitatore ha già scelto una lingua con il selettore, vale quella (salvata nel browser).
    Altrimenti, solo sulle pagine italiane: se il browser non indica l'italiano tra le lingue preferite, si passa all'inglese.
    I motori di ricerca non vengono reindirizzati: trovano le due versioni grazie ai link hreflang."""
    alt = {l: lang_href(l, path, up) for l in LANGS}
    return ('<script>(function(){var L=%s,A=%s,s=null;try{s=localStorage.getItem("lang")}catch(e){}'
            'var t=s;if(!t&&L==="it"&&!/bot|crawl|spider|slurp|preview|lighthouse/i.test(navigator.userAgent)){'
            'var ls=navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||""];'
            'if(!ls.some(function(x){return /^it\\b/i.test(x)}))t="en";}'
            'if(t&&t!==L&&A[t])location.replace(A[t]+location.hash);'
            'document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest("a[data-lang]");if(!a)return;'
            'try{localStorage.setItem("lang",a.getAttribute("data-lang"))}catch(_){}if(location.hash)a.href=a.href.split("#")[0]+location.hash;});'
            '})();</script>') % (json.dumps(lang), json.dumps(alt))

# ---------- parti comuni ----------
def page_head(lang, title, desc, path, up, ver, year):
    T = UI[lang]
    alternates = ''.join(f'<link rel="alternate" hreflang="{l}" href="{SITE_URL}{lang_path(l, path)}">\n' for l in LANGS)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}{lang_path("en", path)}">\n'
    other = ''.join(f'<meta property="og:locale:alternate" content="{UI[l]["locale"]}">\n' for l in LANGS if l != lang)
    return f'''<!doctype html>
<html lang="{T["html_lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#000000">
{lang_script(lang, path, up)}
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{AUTHOR}">
<meta name="copyright" content="© {year} {AUTHOR}. {T["rights"]}">
<meta name="robots" content="noai, noimageai">
<link rel="canonical" href="{SITE_URL}{lang_path(lang, path)}">
{alternates}<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}{lang_path(lang, path)}">
<meta property="og:image" content="{SITE_URL}assets/og-terra-rossa.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{T["locale"]}">
{other}<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{up}assets/style.css?v={ver}">
</head>
<body>
'''

def gnav(lang, path, up):
    """Barra di navigazione fissa: nome, sezioni della home, selettore di lingua."""
    T = UI[lang]; home = lang_href(lang, '', up); h = '' if home == './' else home
    links = ''.join(f'<a href="{h}#{a}">{esc(t)}</a>' for a, t in T['menu'])
    return (f'<header class="gnav"><nav class="gnav-in" aria-label="{T["nav"]}"><a class="brand" href="{home}">{AUTHOR}</a>'
            f'<div class="gnav-links">{links}</div>{lang_switch(lang, path, up)}</nav></header>\n')

def foot(lang, year):
    return f'<footer class="foot"><p>{esc(UI[lang]["foot"].format(year=year, author=AUTHOR))}</p></footer>\n'

LIGHTBOX = ('<div class="lb" id="lb" hidden><img alt=""><p class="lb-cap"></p><p class="lb-rot" hidden><svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">'
            '<rect x="9" y="3" width="10" height="22" rx="2"/><path d="M13 21.5h2"/></svg>{rotate}</p><button type="button" class="lb-x" aria-label="{close}">{close}</button></div>\n'
            '<script src="{up}assets/album.js?v={ver}"></script>\n')

def make_fig(meta, T, up, n, p, cls='', extra=''):
    """Una fotografia con didascalia. n = numero progressivo nella pagina."""
    name, title, text = p[:3]; opt = p[3] if len(p) > 3 else {}
    m = meta[name]
    parts = []
    if not opt.get('notime') and m['time']:
        parts.append(f'<i>{m["time"]}</i>')
    gps = GPS_FIX[name] if name in GPS_FIX else m['gps']
    if gps:
        la, lo = gps
        txt = f'{abs(la):.4f}° {"N" if la >= 0 else "S"}, {abs(lo):.4f}° {"E" if lo >= 0 else "W"}'
        parts.append(f'<a href="https://www.openstreetmap.org/?mlat={la:.5f}&amp;mlon={lo:.5f}#map=13/{la:.5f}/{lo:.5f}" target="_blank" rel="noopener" title="{T["open_map"]}"><i>{txt}</i></a>')
    where = f'<span class="where">{" · ".join(parts)}</span>' if parts else ''
    img = (f'<img src="{up}{PAGE_DIR}/{name}.jpg" data-full="{up}{REPO_DIR}/{name}.jpg" '
           f'width="{m["w"]}" height="{m["h"]}" alt="{esc(title.rstrip("."))}" loading="lazy" decoding="async">')
    return (f'<figure class="fig {cls}" style="--r:{m["w"]/m["h"]:.4f}">\n'
            f'  <button class="ph" type="button" aria-label="{T["open_full"]}: {esc(title)}">{img}</button>\n'
            f'  <figcaption><span class="no">{n:02d}</span><p class="cap"><strong>{esc(title)}</strong> {esc(text)}</p>{extra}'
            f'<p class="meta">{where}<span class="cam">{" · ".join("<i>"+esc(x)+"</i>" for x in m["exif"].split(" · "))}</span></p></figcaption>\n</figure>')

def tile(up, base, th, lang, T):
    name, _ = th[lang]
    return (f'<li class="tile"><a href="{up}{base}temi/{th["slug"]}/"><img src="{up}{PAGE_DIR}/{th["cover"]}.jpg" alt="" loading="lazy" decoding="async">'
            f'<div class="t"><h3>{esc(name)}</h3><p>{T["count"].format(n=len(th["photos"]))}</p></div></a></li>')

# ---------- build ----------
def build():
    year = ALBUM_IT['year']
    missing_page = [n for n in all_names() if not os.path.exists(f'{ROOT}/{PAGE_DIR}/{n}.jpg')]
    assert not missing_page, f'Mancano in {PAGE_DIR}: {missing_page}'
    names = list(all_names())
    assert len(names) == len(set(names)), 'foto duplicate'
    for th in THEMES:
        bad = [p for p in th['photos'] + [th['cover']] if p not in names]
        assert not bad, f'Tema {th["slug"]}: foto non presenti nell’album: {bad}'
    missing = sorted(set(os.path.splitext(f)[0] for f in os.listdir(SRC) if f.endswith('.jpg')) - set(names))
    extra = [n for n in names if not os.path.exists(f'{SRC}/{n}.jpg')]
    assert not extra, extra
    with ThreadPoolExecutor(8) as ex:
        meta = dict(ex.map(process, sorted(set(names + [ALBUM_IT['hero'], ALBUM_IT['cover'], HOME_IMAGE]))))
    ver = hashlib.md5(open(f'{ROOT}/assets/style.css','rb').read() + open(f'{ROOT}/assets/album.js','rb').read()).hexdigest()[:8]
    for lang in LANGS:
        render(lang, meta, ver, year)
    print('foto:', len(names), 'non usate:', missing, '· temi:', len(THEMES), '· lingue:', ', '.join(LANGS))

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)

def render(lang, meta, ver, year):
    ALBUM, CHAPTERS = load(lang)
    T = UI[lang]
    slug = ALBUM['slug']
    base = lang_path(lang)                         # '' per l'italiano, 'en/' per l'inglese
    names = list(all_names(CHAPTERS))
    total = len(names)
    lightbox = lambda up: LIGHTBOX.format(rotate=T['rotate'], close=T['close'], up=up, ver=ver)
    # dove si trova ogni foto nell'album (per le pagine dei temi)
    where = {p[0]: (ch, p) for ch in CHAPTERS for b in ch['blocks'] for p in blocks_photos(b)}

    # ----- album -----
    up = '../' * (base + f'{slug}/').count('/')
    n = [0]
    def fig(p, cls=''):
        n[0] += 1
        return make_fig(meta, T, up, n[0], p, cls)
    def block(b):
        k = b[0]
        if k in ('full', 'wide'): return fig(b[1], 'wide')
        if k == 'group': return '<div class="group">' + ''.join(fig(p) for p in b[1]) + '</div>'
        if k == 'offset':
            main, side, rev = b[1], b[2], b[3]
            # con rev la foto laterale sta a sinistra: viene prima anche nell'ordine di lettura e nella numerazione
            figs = [(main, 'span-main'), (side, 'side')]
            if rev: figs.reverse()
            return f'<div class="grid-offset{" rev" if rev else ""}">' + ''.join(fig(*f) for f in figs) + '</div>'
        raise ValueError(k)

    chapters_html = ''
    for ch in CHAPTERS:
        chapters_html += f'''<section class="ch" id="cap-{ch["num"].lower()}">
  <header class="ch-head">
    <p class="ch-meta"><span>{T["chapter"]} {ch["num"]}</span><span>{ch["date"]}</span></p>
    <h2>{esc(ch["title"])}</h2>
    <p class="intro">{esc(ch["intro"])}</p>
  </header>
  {"".join(block(b) for b in ch["blocks"])}
</section>
'''
    lenses = sorted({meta[x]['lens'] for x in names}, key=lambda l: ['16mm', 'RF24', 'RF100'].index(next(k for k in ['16mm', 'RF24', 'RF100'] if l.startswith(k))))
    lens_html = '<br>'.join(LENS[l][1] for l in lenses)
    map_kw = dict(titles=ALBUM.get('map_names'), relief_href=f'{up}assets/rilievo-usa.png', quota_href=f'{up}assets/quota-usa.png', lang=lang)
    album = page_head(lang, f'{ALBUM["title"]} · {AUTHOR}', ALBUM.get('meta_description') or ALBUM['lede'], f'{slug}/', up, ver, year) + gnav(lang, f'{slug}/', up) + f'''<header class="hero">
  <img src="{up}{PAGE_DIR}/{ALBUM["hero"]}.jpg" alt="{esc(ALBUM["hero_alt"])}" fetchpriority="high">
  <div class="hero-text">
    <h1>{esc(ALBUM["hero_title"])}</h1>
    <p class="facts">{ALBUM["kicker"][0]}, {ALBUM["kicker"][1]}</p>
  </div>
</header>
<main>
  <section class="opening">
    <p class="lede">{esc(ALBUM["lede"])}</p>
    <figure class="route-map" id="mappa">
      <div class="map-head"><p class="kicker">{T["route_kicker"]}</p><h2 class="map-title">{T["route_title"]}</h2></div>
      {mappa.svg(**map_kw)}{mappa.svg(mobile=True, **map_kw)}
    </figure>
  </section>
{chapters_html}
  <footer class="colophon">
    <h2>Colophon</h2>
    <dl>
      <div><dt>{T["col_photos"]}</dt><dd>{AUTHOR}</dd></div>
      <div><dt>{T["col_camera"]}</dt><dd>Canon EOS R7</dd></div>
      <div><dt>{T["col_lenses"]}</dt><dd>{lens_html}</dd></div>
      <div><dt>{T["col_dev"]}</dt><dd>Adobe Lightroom</dd></div>
      <div><dt>{T["col_map"]}</dt><dd>{T["map_credit"]}</dd></div>
    </dl>
    {"".join(f'<p class="copy">{esc(x)}</p>' for x in ALBUM.get('footer_copy') or [f'© {year} {AUTHOR}. {T["rights"]}'])}
    <p class="copy"><a class="backlink more" href="../">{T["all_albums"]}</a></p>
  </footer>
</main>
''' + lightbox(up) + '</body>\n</html>\n'
    write(f'{OUT}/{base}{slug}/index.html', album)

    # ----- temi -----
    for th in THEMES:
        path = f'temi/{th["slug"]}/'
        up = '../' * (base + path).count('/')
        name, desc = th[lang]
        figs = []
        for i, pn in enumerate(th['photos'], 1):
            ch, p = where[pn]
            src = f'<p class="from"><a href="{up}{base}{slug}/#cap-{ch["num"].lower()}">{esc(T["from_album"].format(album=ALBUM["title"], num=ch["num"]))}</a></p>'
            figs.append(make_fig(meta, T, up, i, p, extra=src))
        others = ''.join(tile(up, base, o, lang, T) for o in THEMES if o is not th)
        page = page_head(lang, f'{name} · {AUTHOR}', desc, path, up, ver, year) + gnav(lang, path, up) + f'''<main>
  <header class="theme-head">
    <h1>{esc(name)}</h1>
    <p>{esc(desc)}</p>
  </header>
  <section><div class="masonry">
{"".join(figs)}
  </div></section>
  <section class="others">
    <h2>{T["other_themes"]}</h2>
    <ul class="tiles">{others}</ul>
  </section>
</main>
''' + foot(lang, year) + lightbox(up) + '</body>\n</html>\n'
        write(f'{OUT}/{base}{path}index.html', page)

    # ----- home -----
    up = '../' * base.count('/')
    hm = meta[HOME_IMAGE]
    tiles = ''.join(tile(up, base, th, lang, T) for th in THEMES)
    cards = ''.join(f'<article class="card"><h3>{esc(h)}</h3><p>{esc(p)}</p><a class="more" href="{href.format(up=up, base=base)}"'
                    + (' target="_blank" rel="noopener"' if href.startswith('http') else '') + f'>{esc(l)}</a></article>'
                    for h, p, l, href in T['projects'])
    facts = T['album_facts'].format(k0=ALBUM['kicker'][0], k1=ALBUM['kicker'][1], n=total, c=len(CHAPTERS))
    mail = f'<a class="mail" href="mailto:{EMAIL}">{EMAIL}</a>' if EMAIL else ''
    home = page_head(lang, f'{SITE_TITLE} · {T["home_title"]}', T['home_desc'].format(author=AUTHOR), '', up, ver, year) + gnav(lang, '', up) + f'''<main>
  <section class="home-hero">
    <h1>{AUTHOR}</h1>
    <p class="sub">{esc(T["home_sub"])}</p>
    <div class="shot"><img src="{up}{PAGE_DIR}/{HOME_IMAGE}.jpg" width="{hm["w"]}" height="{hm["h"]}" alt="{esc(T["home_alt"])}" fetchpriority="high"></div>
  </section>
  <section class="sec" id="album">
    <div class="sec-head"><h2>{T["albums_h"]}</h2><p>{T["albums_p"]}</p></div>
    <a class="feature" href="{slug}/">
      <img src="{up}{PAGE_DIR}/{ALBUM["hero"]}.jpg" alt="{esc(ALBUM["cover_alt"])}" loading="lazy" decoding="async">
      <div class="feature-text"><h3>{esc(ALBUM["title"])}</h3><p>{esc(facts)}</p><span class="more">{T["open_album"]}</span></div>
    </a>
  </section>
  <section class="sec" id="temi">
    <div class="sec-head"><h2>{T["themes_h"]}</h2><p>{T["themes_p"]}</p></div>
    <ul class="tiles">{tiles}</ul>
  </section>
  <section class="sec" id="progetti">
    <div class="sec-head"><h2>{T["projects_h"]}</h2><p>{T["projects_p"]}</p></div>
    <div class="cards">{cards}</div>
  </section>
  <section class="sec contact" id="contatti">
    <div class="sec-head"><h2>{T["contact_h"]}</h2><p>{T["contact_p"]}</p></div>
    {mail}
    <ul><li><a class="more" href="{GITHUB}" target="_blank" rel="noopener">GitHub</a></li></ul>
  </section>
</main>
''' + foot(lang, year) + '''<script>document.addEventListener('contextmenu',function(e){if(e.target.tagName==='IMG')e.preventDefault();});</script>
</body>
</html>
'''
    write(f'{OUT}/{base}index.html', home)

if __name__ == '__main__':
    build()
