"""Genera tutte le pagine del sito in tutte le lingue: la home e una pagina per ogni album.

Il codice non contiene testi né dati. Struttura (vedi common/README.md):
  index.html                     home nella lingua principale (deve stare qui: è la pagina d'ingresso del sito)
  home/en/index.html             home nelle altre lingue;  home/texts/<lingua>.json  i suoi testi
  <album>/index.html             album nella lingua principale;  <album>/en/index.html  nelle altre lingue
  <album>/photos/2880/          foto originali (JPEG da 2880 px): l'unica cosa da esportare
  <album>/photos/web/           copie WebP leggere in più misure, generate dalla build (common/code/images.py)
  <album>/texts/<lingua>.json    testi dell'album;  <album>/structure.json  capitoli e impaginazione
  <album>/map/                   mappa (facoltativa): route.json, geodata.json, relief.png, elevation.png
  common/                        stile, script, config.json, testi comuni (texts/<lingua>.json) e questo codice (code/)

Uso, dalla cartella principale del repository:  python3 common/code/build_site.py"""
import hashlib, html, json, os, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.dirname(HERE)                 # cartella common/
ROOT = os.path.dirname(COMMON)                 # cartella principale del repository
OUT = os.environ.get('OUT', ROOT)              # dove scrivere le pagine (di default: il repository)
FULL_SIZE = '2880'                             # sottocartella di <album>/photos con gli originali
sys.path.insert(0, HERE)
from route_map import RouteMap, arabic
import images

def read_json(*path):
    return json.load(open(os.path.join(*path), encoding='utf-8'))

CONFIG = read_json(COMMON, 'config.json')
AUTHOR = CONFIG['author']
SITE_URL = CONFIG['site_url']
LANGS = tuple(CONFIG['languages'])             # la prima è la lingua principale (pagine nella radice)
MAIN = LANGS[0]
UI = {l: read_json(COMMON, 'texts', f'{l}.json') for l in LANGS}                          # testi comuni
HOME_UI = {l: {**UI[l], **read_json(ROOT, 'home', 'texts', f'{l}.json')} for l in LANGS}    # + testi della home
esc = html.escape


# ---------- album ----------
def blocks_photos(b):
    """Le foto di un blocco, in ordine."""
    if b[0] in ('full', 'wide'): return [b[1]]
    if b[0] == 'group': return list(b[1])
    if b[0] == 'offset': return [b[1], b[2]]
    raise ValueError(b[0])

class Album:
    """Un album: tutto sta nella sua cartella <slug>/ (struttura, testi, foto, mappa)."""
    def __init__(self, slug):
        self.slug = slug
        self.folder = os.path.join(ROOT, slug)
        st = read_json(self.folder, 'structure.json')
        self.info = st
        self.chapters = st['chapters']
        self.notime = set(st.get('no_time', []))
        self.gps = {k: (tuple(v) if v else None) for k, v in st.get('gps', {}).items()}
        self.names = [n for ch in self.chapters for b in ch['blocks'] for n in blocks_photos(b)]
        mapdir = os.path.join(self.folder, 'map')
        self.map = RouteMap(mapdir) if os.path.exists(os.path.join(mapdir, 'route.json')) else None
        self.check()

    def photo(self, name, size=FULL_SIZE):
        """Percorso della foto, relativo alla radice del sito."""
        return f'{self.slug}/photos/{size}/{name}.jpg'

    def check(self):
        assert len(self.names) == len(set(self.names)), f'{self.slug}: foto duplicate'
        for size in (FULL_SIZE,):
            missing = [n for n in self.names + [self.info['hero'], self.info.get('preview', self.info['hero'])] if not os.path.exists(os.path.join(ROOT, self.photo(n, size)))]
            assert not missing, f'Mancano in {self.slug}/photos/{size}: {missing}'
        folder = os.path.join(ROOT, self.slug, 'photos', FULL_SIZE)
        self.unused = sorted(set(os.path.splitext(f)[0] for f in os.listdir(folder) if f.endswith('.jpg')) - set(self.names) - {self.info['hero']})

    def texts(self, lang):
        """Testi dell'album nella lingua data. Se manca qualcosa, usa la lingua principale e lo segnala."""
        main = json.load(open(os.path.join(self.folder, 'texts', f'{MAIN}.json'), encoding='utf-8'))
        if lang == MAIN:
            t = main
        else:
            t = json.load(open(os.path.join(self.folder, 'texts', f'{lang}.json'), encoding='utf-8'))
            missing = [k for k in main if k not in t]
            missing += [f'capitolo {n}' for n in main['chapters'] if n not in t.get('chapters', {})]
            missing += [n for n in main['captions'] if n not in t.get('captions', {})]
            if missing:
                print(f'ATTENZIONE: in {self.slug}/texts/{lang}.json mancano (uso {MAIN}):', ', '.join(missing))
            t = {**main, **t, 'chapters': {**main['chapters'], **t.get('chapters', {})},
                 'captions': {**main['captions'], **t.get('captions', {})}}
        missing = [n for n in self.names if n not in t['captions']]
        assert not missing, f'Didascalie mancanti in {self.slug}/texts/{MAIN}.json: {missing}'
        return t


# ---------- foto ----------
def process(path):
    """Legge dal file a piena risoluzione i dati di scatto, le dimensioni e la posizione GPS."""
    im = Image.open(os.path.join(ROOT, path))
    ex = im.getexif(); sub = ex.get_ifd(0x8769)
    t = float(sub[33434]); sh = f'1/{round(1/t)} s' if t < 1 else f'{t:g} s'
    info = dict(
        exif=f'{float(sub[37386]):g} mm · f/{float(sub[33437]):g} · {sh} · ISO {sub[34855]}',
        date=sub.get(36867, '')[:10], time=sub.get(36867, '')[11:16], lens=sub.get(42036), camera=ex.get(272, ''), gps=None)
    g = ex.get_ifd(0x8825)
    if g and 2 in g:
        dm = lambda v, r: (float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600) * (-1 if r in ('S', 'W') else 1)
        info['gps'] = (dm(g[2], g[1]), dm(g[4], g[3]))
    info['w'], info['h'] = ImageOps.exif_transpose(im).size
    return path, info


def fmt_date(d, T):
    """'2026:04:05' -> '5 aprile 2026' / 'April 5, 2026', secondo date_format e months nei testi comuni."""
    y, mo, dd = d.split(':')
    return T['date_format'].format(d=int(dd), m=T['months'][int(mo) - 1], y=y)

def fmt_time(t, T):
    """'18:34' -> '18:34' oppure '6:34 pm' se la lingua usa le 12 ore (time_12h nei testi comuni)."""
    h, mi = map(int, t.split(':'))
    if not T.get('time_12h'):
        return f'{h:02d}:{mi:02d}'
    return f'{(h - 1) % 12 + 1}:{mi:02d} {"am" if h < 12 else "pm"}'


# ---------- lingue ----------
HOME = 'home'

def page_path(page, lang):
    """Percorso di una pagina (relativo alla radice del sito). page = HOME oppure il nome di un album.
    Home: index.html nella radice per la lingua principale, home/<lingua>/ per le altre.
    Album: <album>/ per la lingua principale, <album>/<lingua>/ per le altre."""
    if page == HOME:
        return '' if lang == MAIN else f'{HOME}/{lang}/'
    return f'{page}/' if lang == MAIN else f'{page}/{lang}/'

def href(page, lang, up):
    return (up + page_path(page, lang)) or './'

def lang_switch(lang, page, up):
    if len(LANGS) == 1:                                  # una sola lingua: niente selettore
        return ''
    links = []
    for l in LANGS:
        cur = ' aria-current="page"' if l == lang else ''
        links.append(f'<a href="{href(page, l, up)}" lang="{l}" hreflang="{l}" data-lang="{l}"{cur}>{l.upper()}</a>')
    return f'<div class="lang" role="group" aria-label="{UI[lang]["lang_nav"]}">' + '<span aria-hidden="true">/</span>'.join(links) + '</div>'

def lang_script(lang, page, up):
    """Lingua automatica. Se il visitatore ha già scelto una lingua con il selettore, vale quella (salvata nel browser).
    Altrimenti, solo sulle pagine della lingua principale: se il browser non la indica tra le lingue preferite,
    si passa alla seconda lingua. I motori di ricerca non vengono reindirizzati: trovano le versioni grazie a hreflang."""
    if len(LANGS) == 1:                                  # una sola lingua: serve solo il segnale per le animazioni
        return '<script>document.documentElement.className+=" js"</script>'
    alt = {l: href(page, l, up) for l in LANGS}
    fallback = LANGS[1] if len(LANGS) > 1 else MAIN
    return ('<script>document.documentElement.className+=" js";(function(){var L=%s,M=%s,F=%s,A=%s,s=null;try{s=localStorage.getItem("lang")}catch(e){}'
            'var t=s;if(!t&&L===M&&!/bot|crawl|spider|slurp|preview|lighthouse/i.test(navigator.userAgent)){'
            'var ls=navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||""];'
            'if(!ls.some(function(x){return new RegExp("^"+M+"\\\\b","i").test(x)}))t=F;}'
            'if(t&&t!==L&&A[t])location.replace(A[t]+location.hash);'
            'document.addEventListener("click",function(e){var a=e.target.closest&&e.target.closest("a[data-lang]");if(!a)return;'
            'try{localStorage.setItem("lang",a.getAttribute("data-lang"))}catch(_){}if(location.hash)a.href=a.href.split("#")[0]+location.hash;});'
            '})();</script>') % (json.dumps(lang), json.dumps(MAIN), json.dumps(fallback), json.dumps(alt))


# ---------- parti comuni ----------
def page_head(lang, title, desc, page, up, ver, year):
    T = UI[lang]
    alternates = ''.join(f'<link rel="alternate" hreflang="{l}" href="{SITE_URL}{page_path(page, l)}">\n' for l in LANGS)
    if len(LANGS) > 1:
        alternates += f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}{page_path(page, LANGS[1])}">\n'
    other = ''.join(f'<meta property="og:locale:alternate" content="{UI[l]["locale"]}">\n' for l in LANGS if l != lang)
    return f'''<!doctype html>
<html lang="{T["html_lang"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#000000">
{lang_script(lang, page, up)}
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{AUTHOR}">
<meta name="copyright" content="© {year} {AUTHOR}. {T["rights"]}">
<meta name="robots" content="noai, noimageai">
<link rel="canonical" href="{SITE_URL}{page_path(page, lang)}">
{alternates}<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}{page_path(page, lang)}">
<meta property="og:image" content="{SITE_URL}{CONFIG["og_image"]}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{T["locale"]}">
{other}<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{up}common/style.css?v={ver}">
<script src="{up}common/site.js?v={ver}" defer></script>
</head>
<body class="{'home' if page == HOME else 'album'}">
'''

def gnav(lang, page, up):
    """Barra di navigazione fissa: nome, sezioni della home, selettore di lingua."""
    T = UI[lang]; home = href(HOME, lang, up); h = '' if page == HOME else home
    links = ''.join(f'<a href="{h}#{a}">{esc(t)}</a>' for a, t in T['menu'].items())
    return (f'<header class="gnav"><nav class="gnav-in" aria-label="{T["nav"]}"><a class="brand" href="{home}">{AUTHOR}</a>'
            f'<div class="gnav-links">{links}</div>{lang_switch(lang, page, up)}</nav></header>\n')

def foot(lang, year):
    return f'<footer class="foot"><p>{esc(UI[lang]["foot"].format(year=year, author=AUTHOR))}</p></footer>\n'

LIGHTBOX = ('<div class="lb" id="lb" hidden><img alt=""><p class="lb-cap"></p><p class="lb-rot" hidden><svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">'
            '<rect x="9" y="3" width="10" height="22" rx="2"/><path d="M13 21.5h2"/></svg>{rotate}</p><button type="button" class="lb-x" aria-label="{close}">{close}</button></div>\n'
            '<script src="{up}common/album.js?v={ver}"></script>\n')


# ---------- foto: copie leggere in più misure ----------
WEB = {}   # originale -> [(larghezza, copia WebP)], riempito da build()
MOBILE = '(max-width: 760px)'     # sotto questa larghezza le foto vanno una sotto l'altra (style.css)
MAIN_W = 'min(1200px, 100vw)'     # larghezza della colonna principale

def pic(src, up, sizes):
    """Attributi src/srcset/sizes di un'immagine: il browser sceglie la copia più piccola che basta."""
    v = WEB[src]
    fallback = next((p for w, p in v if w >= 1600), v[-1][1])
    return (f'src="{up}{fallback}" srcset="{", ".join(f"{up}{p} {w}w" for w, p in v)}" sizes="{sizes}"')

def largest(src, up):
    return up + WEB[src][-1][1]

def cover_sizes(w, h):
    """Foto a tutto schermo ritagliata (object-fit: cover): se lo schermo è più stretto della foto, conta l'altezza."""
    return f'(max-aspect-ratio: {w}/{h}) {100 * w / h:.0f}vh, 100vw'


# ---------- pagine ----------
def render_album(al, lang, meta, ver):
    T = UI[lang]; A = al.texts(lang); year = al.info['year']
    path = page_path(al.slug, lang)
    up = '../' * path.count('/')
    n = [0]

    def fig(name, cls='', share=1.0):
        n[0] += 1
        title, text = A['captions'][name]
        m = meta[al.photo(name, FULL_SIZE)]
        parts = []
        if m['date']:
            parts.append(f'<i>{fmt_date(m["date"], T)}</i>')
        if name not in al.notime and m['time']:
            parts.append(f'<i>{fmt_time(m["time"], T)}</i>')
        gps = al.gps[name] if name in al.gps else m['gps']
        if gps:
            la, lo = gps
            txt = f'{abs(la):.4f}° {"N" if la >= 0 else "S"}, {abs(lo):.4f}° {"E" if lo >= 0 else "W"}'
            parts.append(f'<a href="https://www.openstreetmap.org/?mlat={la:.5f}&amp;mlon={lo:.5f}#map=13/{la:.5f}/{lo:.5f}" target="_blank" rel="noopener" title="{T["open_map"]}"><i>{txt}</i></a>')
        where = f'<span class="where">{" · ".join(parts)}</span>' if parts else ''
        sizes = f'{MOBILE} 100vw, {MAIN_W}' if share == 1 else f'{MOBILE} 100vw, calc({MAIN_W} * {share:.3f})'
        img = (f'<img {pic(al.photo(name), up, sizes)} data-full="{largest(al.photo(name), up)}" '
               f'width="{m["w"]}" height="{m["h"]}" alt="{esc(title.rstrip("."))}" loading="lazy" decoding="async">')
        return (f'<figure class="fig {cls}" style="--r:{m["w"]/m["h"]:.4f}">\n'
                f'  <button class="ph" type="button" aria-label="{T["open_full"]}: {esc(title)}">{img}</button>\n'
                f'  <figcaption><span class="no">{n[0]:02d}</span><p class="cap"><strong>{esc(title)}</strong> {esc(text)}</p>'
                f'<p class="meta">{where}<span class="cam">{" · ".join("<i>"+esc(x)+"</i>" for x in m["exif"].split(" · "))}</span></p></figcaption>\n</figure>')

    def block(b):
        k = b[0]
        if k in ('full', 'wide'): return fig(b[1], 'wide')
        if k == 'group':
            # nella riga ogni foto prende spazio in proporzione al suo formato (style.css: flex: var(--r))
            r = {p: meta[al.photo(p)]['w'] / meta[al.photo(p)]['h'] for p in b[1]}
            return '<div class="group">' + ''.join(fig(p, share=r[p] / sum(r.values())) for p in b[1]) + '</div>'
        if k == 'offset':
            main, side, rev = b[1], b[2], b[3]
            # con rev la foto laterale sta a sinistra: viene prima anche nell'ordine di lettura e nella numerazione
            figs = [(main, 'span-main', 8 / 12), (side, 'side', 4 / 12)]
            if rev: figs.reverse()
            return f'<div class="grid-offset{" rev" if rev else ""}">' + ''.join(fig(*f) for f in figs) + '</div>'
        raise ValueError(k)

    chapters_html = ''
    for ch in al.chapters:
        c = A['chapters'][ch['num']]
        chapters_html += f'''<section class="ch" id="chapter-{arabic(ch["num"])}">
  <header class="ch-head">
    <p class="ch-meta"><span>{T["chapter"]} {arabic(ch["num"])}</span><span>{c["date"]}</span></p>
    <h2>{esc(c["title"])}</h2>
    <p class="intro">{esc(c["intro"])}</p>
  </header>
  {"".join(block(b) for b in ch["blocks"])}
</section>
'''
    # indice dei capitoli: compare in basso mentre si scorrono i capitoli (common/site.js), toccandolo si apre l'elenco
    tot = len(al.chapters)
    first = A['chapters'][al.chapters[0]['num']]['title'] if tot else ''
    items = ''.join(f'<li style="--i:{k}"><a href="#chapter-{arabic(ch["num"])}"><span>{arabic(ch["num"])}</span>{esc(A["chapters"][ch["num"]]["title"])}</a></li>'
                    for k, ch in enumerate(al.chapters))
    chnav = (f'<nav class="chnav" aria-label="{T["chapters_nav"]}"><ol class="chnav-list" id="chnav-list">{items}</ol>'
             f'<button class="chnav-btn" type="button" aria-expanded="false" aria-controls="chnav-list">'
             f'<span class="chnav-n"><b>1</b> / {tot}</span><span class="chnav-t">{esc(first)}</span>'
             f'<svg class="chnav-i" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 7.5 6 4l3.5 3.5"/></svg>'
             f'<svg class="chnav-ring" aria-hidden="true"><path/></svg></button></nav>\n') if tot > 1 else ''
    shots = [meta[al.photo(x, FULL_SIZE)] for x in al.names]
    hm = meta[al.photo(al.info['hero'])]
    lens_order = list(CONFIG['lenses'])
    lenses = sorted({s['lens'] for s in shots}, key=lambda l: lens_order.index(l) if l in lens_order else len(lens_order))
    lens_html = '<br>'.join(CONFIG['lenses'].get(l, l) for l in lenses)
    cameras = ', '.join(sorted({s['camera'] for s in shots if s['camera']}))
    map_html, map_row = '', ''
    if al.map:
        layer = lambda f: f'{up}{al.slug}/map/{f}' if os.path.exists(os.path.join(al.folder, 'map', f)) else None   # rilievo facoltativo
        names = {**{n: c['title'] for n, c in A['chapters'].items()}, **A.get('map_names', {})}   # nomi delle tappe: titoli dei capitoli, salvo diversa indicazione
        kw = dict(relief_href=layer('relief.png'), quota_href=layer('elevation.png'),
                  titles=names, text=(A['map_description'], T['map_go']))
        map_html = f'''
    <figure class="route-map" id="map">
      <div class="map-head"><p class="kicker">{T["route_kicker"]}</p><h2 class="map-title">{A["map_title"]}</h2></div>
      {al.map.svg(**kw)}{al.map.svg(mobile=True, **kw)}
    </figure>'''
        map_row = f'\n      <div><dt>{T["col_map"]}</dt><dd>{A["map_credit"]}</dd></div>'
    page = page_head(lang, f'{A["title"]} · {AUTHOR}', A['meta_description'], al.slug, up, ver, year) + gnav(lang, al.slug, up) + f'''<header class="cover">
  <picture><img {pic(al.photo(al.info["hero"]), up, cover_sizes(hm["w"], hm["h"]))} alt="{esc(A["hero_alt"])}" fetchpriority="high"></picture>
  <div class="cover-text">
    <h1>{esc(A["title"])}</h1>
  </div>
  <span class="cue" aria-hidden="true"></span>
</header>
<main>
  <section class="opening">
    <p class="lede">{esc(A["lede"])}</p>{map_html}
  </section>
{chapters_html}
  <footer class="colophon">
    <h2>Colophon</h2>
    <dl>
      <div><dt>{T["col_photos"]}</dt><dd>{AUTHOR}</dd></div>
      <div><dt>{T["col_camera"]}</dt><dd>{cameras}</dd></div>
      <div><dt>{T["col_lenses"]}</dt><dd>{lens_html}</dd></div>
      <div><dt>{T["col_dev"]}</dt><dd>{al.info["software"]}</dd></div>{map_row}
    </dl>
    {"".join(f'<p class="copy">{esc(x)}</p>' for x in A['footer_copy'] or [f'© {year} {AUTHOR}. {T["rights"]}'])}
    <p class="copy"><a class="backlink more" href="{href(HOME, lang, up)}">{T["all_albums"]}</a></p>
  </footer>
</main>
''' + chnav + LIGHTBOX.format(rotate=T['rotate'], close=T['close'], up=up, ver=ver) + '</body>\n</html>\n'
    write(f'{OUT}/{path}index.html', page)

def render_home(albums, lang, meta, ver):
    T = HOME_UI[lang]
    path = page_path(HOME, lang)
    up = '../' * path.count('/')
    year = max(al.info['year'] for al in albums)
    cover = CONFIG['home_cover']
    cover_dims = {k: Image.open(os.path.join(ROOT, v)).size for k, v in cover.items()}
    cards = []
    for k, al in enumerate(albums):
        A = al.texts(lang)
        # anteprima nella home: una foto diversa dalla copertina dell'album ("preview" in structure.json)
        # se gli album sono dispari, il primo occupa tutta la riga (style.css)
        wide = k == 0 and len(albums) % 2 == 1
        img = pic(al.photo(al.info.get("preview", al.info["hero"])), up, f'{MOBILE} 100vw, {MAIN_W}' if wide else f'{MOBILE} 100vw, calc({MAIN_W} / 2)')
        cards.append(f'''      <a class="alb" href="{href(al.slug, lang, up)}"><div class="im"><img {img} alt="" loading="lazy" decoding="async"></div>'''
                     f'''<div class="cap"><h3>{esc(A["title"])}</h3></div></a>
''')
    email = CONFIG.get('email')
    mail = f'<a class="mail" href="mailto:{email}">{email}</a>' if email else ''
    github = f'<ul><li><a class="more" href="{CONFIG["github"]}" target="_blank" rel="noopener">GitHub</a></li></ul>' if CONFIG.get('github') else ''
    page = page_head(lang, f'{AUTHOR} · {T["home_title"]}', T['home_desc'].format(author=AUTHOR), HOME, up, ver, year) + gnav(lang, HOME, up) + f'''<main>
  <header class="cover">
    <picture>
      <source media="(orientation: portrait)" srcset="{", ".join(f"{up}{p} {w}w" for w, p in WEB[cover["portrait"]])}" sizes="{cover_sizes(*cover_dims["portrait"])}">
      <img {pic(cover["landscape"], up, cover_sizes(*cover_dims["landscape"]))} alt="{esc(T["home_alt"])}" fetchpriority="high">
    </picture>
    <div class="cover-text"><h1>{AUTHOR}</h1></div>
    <span class="cue" aria-hidden="true"></span>
  </header>
  <section class="statement"><p>{esc(T["home_sub"])}</p></section>
  <section class="sec" id="albums">
    <div class="sec-head"><h2>{T["albums_h"]}</h2><p>{T["albums_p"]}</p></div>
    <div class="albums">
{"".join(cards)}    </div>
  </section>
  <section class="sec contact" id="contact">
    <div class="sec-head"><h2>{T["contact_h"]}</h2><p>{T["contact_p"]}</p></div>
    {mail}
    {github}
  </section>
</main>
''' + foot(lang, year) + '''<script>document.addEventListener('contextmenu',function(e){if(e.target.tagName==='IMG')e.preventDefault();});</script>
</body>
</html>
'''
    write(f'{OUT}/{path}index.html', page)

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(text)

def build():
    albums = [Album(slug) for slug in CONFIG['albums']]
    paths = {al.photo(n, FULL_SIZE) for al in albums for n in al.names + [al.info['hero'], al.info.get('preview', al.info['hero'])]}
    WEB.update(images.build(list(paths) + list(CONFIG['home_cover'].values()), ROOT))
    with ThreadPoolExecutor(8) as ex:
        meta = dict(ex.map(process, sorted(paths)))
    ver = hashlib.md5(b''.join(open(f'{COMMON}/{f}','rb').read() for f in ('style.css', 'album.js', 'site.js'))).hexdigest()[:8]
    for lang in LANGS:
        for al in albums:
            render_album(al, lang, meta, ver)
        render_home(albums, lang, meta, ver)
    for al in albums:
        print(f'{al.slug}: {len(al.names)} foto, {len(al.chapters)} capitoli' + (f' · non usate: {al.unused}' if al.unused else ''))
    print('lingue:', ', '.join(LANGS))

if __name__ == '__main__':
    build()
