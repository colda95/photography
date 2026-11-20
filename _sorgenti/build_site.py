import copy, hashlib, html, os, shutil, json, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

# Genera le pagine del sito (copertina e album), in italiano e in inglese,
# a partire da content_usa.py, testi_utente.json (italiano) e testi_en.json (inglese).
# Italiano: index.html e usa-2026/index.html.  Inglese: en/index.html e en/usa-2026/index.html.
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
LANGS = ('it', 'en')                           # la prima è la lingua principale (pagine nella radice)
sys.path.insert(0, HERE)
from content_usa import ALBUM as ALBUM_IT, CHAPTERS as CHAPTERS_IT
import mappa
try:
    from content_usa import GPS as GPS_FIX
except ImportError:
    GPS_FIX = {}

# Testi dell'interfaccia (tutto ciò che non dipende dall'album).
UI = {
    'it': dict(
        html_lang='it', locale='it_IT', rights='Tutti i diritti riservati.', lang_nav='Lingua',
        open_full='Apri a schermo intero', open_map='Apri sulla mappa', chapter='Capitolo', nav='Navigazione',
        route_kicker='Il percorso', route_title='Nove tappe, tre stati',
        col_photos='Fotografie', col_camera='Fotocamera', col_lenses='Obiettivi', col_dev='Sviluppo', col_map='Mappa',
        map_credit='Fiumi, laghi e confini: Natural Earth<br>Rilievo: NASA SRTM, tramite OpenTopography',
        all_albums='← Tutti gli album', rotate='Ruota il telefono per vederla più grande', close='Chiudi',
        home_kicker=('Fotografie', 'Album di viaggio'), home_title='Fotografie',
        home_desc='Album fotografici di viaggio di {author}.',
        home_sub='Viaggi raccontati per immagini, scattati con una Canon EOS R7 e sviluppati in Lightroom.',
        facts='{n} fotografie · {c} capitoli', open_album='Apri l’album →'),
    'en': dict(
        html_lang='en', locale='en_US', rights='All rights reserved.', lang_nav='Language',
        open_full='Open full screen', open_map='Open on the map', chapter='Chapter', nav='Navigation',
        route_kicker='The route', route_title='Nine stops, three states',
        col_photos='Photographs', col_camera='Camera', col_lenses='Lenses', col_dev='Processing', col_map='Map',
        map_credit='Rivers, lakes and borders: Natural Earth<br>Relief: NASA SRTM, via OpenTopography',
        all_albums='← All albums', rotate='Rotate your phone to see it larger', close='Close',
        home_kicker=('Photography', 'Travel albums'), home_title='Photography',
        home_desc='Travel photo albums by {author}.',
        home_sub='Journeys told in pictures, shot on a Canon EOS R7 and edited in Lightroom.',
        facts='{n} photographs · {c} chapters', open_album='Open the album →'),
}
TEXTS = {'it': 'testi_utente.json', 'en': 'testi_en.json'}


def load(lang):
    """Album e capitoli con i testi della lingua scelta. I testi nei file JSON hanno la precedenza su content_usa.py."""
    album, chapters = copy.deepcopy(ALBUM_IT), copy.deepcopy(CHAPTERS_IT)
    album.update(hero_title='Terra<br>rossa', hero_alt='La US-163 verso Monument Valley all’ultima luce',
                 cover_alt='Alba sull’anfiteatro di Bryce Canyon', map_names=None)
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
SIZES = (1200, 2000)
esc = html.escape

def xmp_packet(year):
    return (f'<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?><x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            f'<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">'
            f'<dc:creator><rdf:Seq><rdf:li>{AUTHOR}</rdf:li></rdf:Seq></dc:creator>'
            f'<dc:rights><rdf:Alt><rdf:li xml:lang="x-default">© {year} {AUTHOR}. Tutti i diritti riservati.</rdf:li></rdf:Alt></dc:rights>'
            f'<xmpRights:Marked>True</xmpRights:Marked></rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>').encode('utf-8')

def process(name, outdir, year):
    """Legge dal file a piena risoluzione i dati di scatto, le dimensioni e la posizione GPS."""
    src = f'{SRC}/{name}.jpg'
    im = Image.open(src)
    ex = im.getexif(); sub = ex.get_ifd(0x8769)
    icc = im.info.get('icc_profile')
    t = float(sub[33434]); sh = f'1/{round(1/t)} s' if t < 1 else f'{t:g} s'
    lens = sub.get(42036)
    info = dict(
        exif=f'{float(sub[37386]):g} mm · f/{float(sub[33437]):g} · {sh} · ISO {sub[34855]}',
        time=sub.get(36867, '')[11:16], date=sub.get(36867, '')[:10], lens=lens, gps=None)
    g = ex.get_ifd(0x8825)
    if g and 2 in g:
        dm = lambda v, r: (float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600) * (-1 if r in ('S', 'W') else 1)
        info['gps'] = (dm(g[2], g[1]), dm(g[4], g[3]))
    im = ImageOps.exif_transpose(im).convert('RGB')
    info['w'], info['h'] = im.size
    return name, info

def all_names(chapters=CHAPTERS_IT):
    for ch in chapters:
        for b in ch['blocks']:
            if b[0] in ('full', 'wide'): yield b[1][0]
            elif b[0] == 'group':
                for p in b[1]: yield p[0]
            elif b[0] == 'offset': yield b[1][0]; yield b[2][0]

def lang_path(lang, path=''):
    """Percorso di una pagina (relativo alla radice del sito) nella lingua data."""
    return path if lang == LANGS[0] else f'{lang}/{path}'

def lang_href(l, path, up):
    return (up + lang_path(l, path)) or './'

def lang_switch(lang, path, up):
    """Selettore IT / EN. up = percorso dalla pagina corrente alla radice del sito."""
    links = []
    for l in LANGS:
        cur = ' aria-current="page"' if l == lang else ''
        links.append(f'<a href="{lang_href(l, path, up)}" lang="{l}" hreflang="{l}" data-lang="{l}"{cur}>{l.upper()}</a>')
    return f'<nav class="lang" aria-label="{UI[lang]["lang_nav"]}">' + '<span aria-hidden="true">/</span>'.join(links) + '</nav>'

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

def build():
    slug = ALBUM_IT['slug']; year = ALBUM_IT['year']
    missing_page = [n for n in all_names() if not os.path.exists(f'{ROOT}/{PAGE_DIR}/{n}.jpg')]
    assert not missing_page, f'Mancano in {PAGE_DIR}: {missing_page}'
    names = list(all_names())
    assert len(names) == len(set(names)), 'foto duplicate'
    missing = sorted(set(os.path.splitext(f)[0] for f in os.listdir(SRC)) - set(names))
    extra = [n for n in names if not os.path.exists(f'{SRC}/{n}.jpg')]
    assert not extra, extra
    with ThreadPoolExecutor(8) as ex:
        meta = dict(ex.map(lambda n: process(n, f'{OUT}/{slug}/img', year), names + [ALBUM_IT['hero'], ALBUM_IT['cover']]))
    ver = hashlib.md5(open(f'{ROOT}/assets/style.css','rb').read() + open(f'{ROOT}/assets/album.js','rb').read()).hexdigest()[:8]
    for lang in LANGS:
        total = render(lang, meta, ver)
    print('foto:', total, 'non usate:', missing, '· lingue:', ', '.join(LANGS))

def render(lang, meta, ver):
    ALBUM, CHAPTERS = load(lang)
    T = UI[lang]
    slug = ALBUM['slug']; year = ALBUM['year']
    base = lang_path(lang)                         # '' per l'italiano, 'en/' per l'inglese
    up_home = '../' * base.count('/')              # dalla copertina alla radice del sito
    up_album = up_home + '../'                     # dall'album alla radice del sito
    os.makedirs(f'{OUT}/{base}{slug}', exist_ok=True)
    names = list(all_names(CHAPTERS))

    n = [0]
    def img_tag(name, alt, sizes, cls='', eager=False):
        m = meta[name]
        return (f'<img src="{up_album}{PAGE_DIR}/{name}.jpg" data-full="{up_album}{REPO_DIR}/{name}.jpg" '
                f'width="{m["w"]}" height="{m["h"]}" alt="{esc(alt)}"'
                + ('' if eager else ' loading="lazy"') + f' decoding="async"{cls}>')

    def fig(p, cls='', sizes='(max-width: 760px) 100vw, 60vw'):
        name, title, text = p[:3]; opt = p[3] if len(p) > 3 else {}
        n[0] += 1; m = meta[name]
        parts = []
        if not opt.get('notime') and m['time']:
            parts.append(f'<i>{m["time"]}</i>')
        gps = GPS_FIX[name] if name in GPS_FIX else m['gps']
        if gps:
            la, lo = gps
            txt = f'{abs(la):.4f}° {"N" if la >= 0 else "S"}, {abs(lo):.4f}° {"E" if lo >= 0 else "W"}'
            parts.append(f'<a href="https://www.openstreetmap.org/?mlat={la:.5f}&amp;mlon={lo:.5f}#map=13/{la:.5f}/{lo:.5f}" target="_blank" rel="noopener" title="{T["open_map"]}"><i>{txt}</i></a>')
        where = f'<span class="where">{" · ".join(parts)}</span>' if parts else ''
        return (f'<figure class="fig {cls}" style="--r:{m["w"]/m["h"]:.4f}">\n'
                f'  <button class="ph" type="button" aria-label="{T["open_full"]}: {esc(title)}">{img_tag(name, title.rstrip("."), sizes)}</button>\n'
                f'  <figcaption><span class="no">{n[0]:02d}</span><p class="cap"><strong>{esc(title)}</strong> {esc(text)}</p><p class="meta">{where}<span class="cam">{" · ".join("<i>"+esc(x)+"</i>" for x in m["exif"].split(" · "))}</span></p></figcaption>\n</figure>')

    def block(b):
        k = b[0]
        if k == 'full': return fig(b[1], 'wide', '(max-width: 1320px) 100vw, 1240px')
        if k == 'wide': return fig(b[1], 'wide', '(max-width: 1320px) 100vw, 1240px')
        if k == 'group':
            tot = sum(meta[p[0]]['w'] / meta[p[0]]['h'] for p in b[1])
            return '<div class="group">' + ''.join(
                fig(p, sizes=f'(max-width: 760px) 100vw, {round(100 * (meta[p[0]]["w"]/meta[p[0]]["h"]) / tot)}vw') for p in b[1]) + '</div>'
        if k == 'offset':
            main, side, rev = b[1], b[2], b[3]
            # con rev la foto laterale sta a sinistra: viene prima anche nell'ordine di lettura e nella numerazione
            figs = [(main, 'span-main', '(max-width: 760px) 100vw, 66vw'), (side, 'side', '(max-width: 760px) 100vw, 33vw')]
            if rev: figs.reverse()
            return f'<div class="grid-offset{" rev" if rev else ""}">' + ''.join(fig(*f) for f in figs) + '</div>'
        raise ValueError(k)

    chapters_html = ''
    for ch in CHAPTERS:
        chapters_html += f'''<section class="ch" id="cap-{ch["num"].lower()}">
  <header class="ch-head">
    <p class="kicker"><span>{T["chapter"]} {ch["num"]}</span><span>{ch["date"]}</span></p>
    <h2>{esc(ch["title"])}</h2>
    <p class="intro">{esc(ch["intro"])}</p>
  </header>
  {"".join(block(b) for b in ch["blocks"])}
</section>
'''
    lenses = sorted({meta[x]['lens'] for x in names}, key=lambda l: ['16mm', 'RF24', 'RF100'].index(next(k for k in ['16mm', 'RF24', 'RF100'] if l.startswith(k))))
    lens_html = '<br>'.join(LENS[l][1] for l in lenses)
    total = n[0]
    hero = ALBUM['hero']

    def head(title, desc, css, path, up):
        alternates = ''.join(f'<link rel="alternate" hreflang="{l}" href="{SITE_URL}{lang_path(l, path)}">\n' for l in LANGS)
        alternates += f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}{lang_path("en", path)}">\n'
        other = ''.join(f'<meta property="og:locale:alternate" content="{UI[l]["locale"]}">\n' for l in LANGS if l != lang)
        return f'''<!doctype html>
<html lang="{T["html_lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
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
<link rel="stylesheet" href="{css}">
</head>
<body>
'''
    up = up_album
    map_kw = dict(titles=ALBUM.get('map_names'), relief_href=f'{up}assets/rilievo-usa.png', quota_href=f'{up}assets/quota-usa.png', lang=lang)
    album = head(f'{ALBUM["title"]} · {AUTHOR}', ALBUM.get('meta_description') or ALBUM['lede'], f'{up}assets/style.css?v={ver}', f'{slug}/', up) + f'''<header class="hero">
  <nav class="topbar" aria-label="{T["nav"]}"><a href="../">{AUTHOR}</a>{lang_switch(lang, f"{slug}/", up)}</nav>
  <img src="{up}{PAGE_DIR}/{hero}.jpg" alt="{esc(ALBUM["hero_alt"])}" fetchpriority="high">
  <div class="hero-text">
    <h1>{ALBUM["hero_title"]}</h1>
  </div>
</header>
<main>
  <section class="opening">
    <p class="lede">{esc(ALBUM["lede"])}</p>
    <figure class="route-map">
      <div class="map-head"><p class="kicker"><span>{T["route_kicker"]}</span></p><h2 class="map-title">{T["route_title"]}</h2></div>
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
    <p class="copy"><a class="backlink" href="../">{T["all_albums"]}</a></p>
  </footer>
</main>
<div class="lb" id="lb" hidden><img alt=""><p class="lb-cap"></p><p class="lb-rot" hidden><svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="9" y="3" width="10" height="22" rx="2"/><path d="M13 21.5h2"/></svg>{T["rotate"]}</p><button type="button" class="lb-x" aria-label="{T["close"]}">{T["close"]}</button></div>
<script src="{up}assets/album.js?v={ver}"></script>
</body>
</html>
'''
    open(f'{OUT}/{base}{slug}/index.html', 'w').write(album)

    cover = ALBUM['cover']; cm = meta[cover]; up = up_home
    home = head(f'{SITE_TITLE} · {T["home_title"]}', T['home_desc'].format(author=AUTHOR), f'{up}assets/style.css?v={ver}', '', up) + f'''<main>
  <section class="home">
    <header class="home-head">
      {lang_switch(lang, "", up)}
      <p class="kicker"><span>{T["home_kicker"][0]}</span><span>{T["home_kicker"][1]}</span></p>
      <h1>{AUTHOR}</h1>
      <p class="sub">{T["home_sub"]}</p>
    </header>
    <ol class="albums">
      <li class="album"><a href="{slug}/">
        <img src="{up}{PAGE_DIR}/{cover}.jpg" width="{cm["w"]}" height="{cm["h"]}" alt="{esc(ALBUM["cover_alt"])}">
        <div class="meta">
          <p class="facts">{ALBUM["kicker"][0]}<br>{ALBUM["kicker"][1]}<br>{T["facts"].format(n=total, c=len(CHAPTERS))}</p>
          <h2>{ALBUM["title"]}</h2>
          <span class="go">{T["open_album"]}</span>
        </div>
      </a></li>
    </ol>
    <footer class="home-foot">© {year} {AUTHOR}. {T["rights"]}</footer>
  </section>
</main>
<script>document.addEventListener('contextmenu',function(e){{if(e.target.tagName==='IMG')e.preventDefault();}});</script>
</body>
</html>
'''
    open(f'{OUT}/{base}index.html', 'w').write(home)
    return total

if __name__ == '__main__':
    build()
