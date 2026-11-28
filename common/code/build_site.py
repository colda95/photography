"""Genera tutte le pagine del sito in tutte le lingue: la home e una pagina per ogni album.

Il codice non contiene testi né dati. Struttura (vedi common/README.md):
  index.html                     home nella lingua principale (deve stare qui: è la pagina d'ingresso del sito)
  home/en/index.html             home nelle altre lingue;  home/texts/<lingua>.json  i suoi testi
  <album>/index.html             album nella lingua principale;  <album>/en/index.html  nelle altre lingue
  <album>/photos/<n>-<nome>/    foto originali (JPEG da 2880 px), una cartella per capitolo: 1-grand-canyon, 2-…
  <album>/photos/web/           copie leggere in più misure, generate dalla build (common/code/images.py)
  <album>/texts/<lingua>.json    testi dell'album;  <album>/structure.json  copertina, anteprima e impaginazione (facoltativa)
  <album>/map/                   mappa (facoltativa): route.json, geodata.json, relief.png, elevation.png
  common/                        stile, script, config.json, testi comuni (texts/<lingua>.json) e questo codice (code/)

Uso, dalla cartella principale del repository:  python3 common/code/build_site.py"""
import hashlib, html, json, os, re, sys
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.dirname(HERE)                 # cartella common/
ROOT = os.path.dirname(COMMON)                 # cartella principale del repository
OUT = os.environ.get('OUT', ROOT)              # dove scrivere le pagine (di default: il repository)
ALBUM_DIR = 'album'                            # cartella che contiene tutti gli album
CHAPTER_DIR = re.compile(r'^(\d+)(?:[-_ ].*)?$')  # cartella di un capitolo: numero, poi un nome a piacere
sys.path.insert(0, HERE)
from route_map import RouteMap, arabic
import images, world_map

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
_said = set()
def warn(msg):
    """Avviso per chi pubblica: stampato una volta sola anche se la pagina è generata più volte."""
    if msg not in _said:
        _said.add(msg); print('ATTENZIONE: ' + msg)


# ---------- album ----------
def blocks_photos(b):
    """Le foto di un blocco, in ordine."""
    if b[0] in ('full', 'wide'): return [b[1]]
    if b[0] == 'group': return list(b[1])
    if b[0] == 'offset': return [b[1], b[2]]
    raise ValueError(b[0])

def auto_layout(names, ratio):
    """Impaginazione automatica di una serie di foto in ordine di scatto, con un ritmo che alterna:
    orizzontale a tutta larghezza, poi due orizzontali affiancate, poi di nuovo una grande;
    due verticali vicine affiancate; una verticale sola accanto all'orizzontale vicina."""
    blocks, i, pair = [], 0, False
    wide = lambda n: ratio(n) >= 1
    while i < len(names):
        n = names[i]
        nxt = names[i + 1] if i + 1 < len(names) else None
        if wide(n):
            if pair and nxt and wide(nxt) and (i + 2 >= len(names) or wide(names[i + 2])):
                blocks.append(['group', [n, nxt]]); i += 2
            else:
                blocks.append(['wide', n]); i += 1
            pair = not pair
        elif nxt and not wide(nxt):
            blocks.append(['group', [n, nxt]]); i += 2
        elif nxt:
            blocks.append(['offset', nxt, n, True]); i += 2      # verticale a sinistra: viene prima nel tempo
        elif blocks and blocks[-1][0] == 'wide':
            blocks.append(['offset', blocks.pop()[1], n, False]); i += 1
        else:
            blocks.append(['group', [n]]); i += 1
    return blocks

class Album:
    """Un album: tutto sta nella sua cartella <slug>/ (struttura, testi, foto, mappa).

    I capitoli sono le cartelle in <slug>/photos/ che iniziano con un numero (1-grand-canyon, 2-page, …):
    il numero dà l'ordine e collega il capitolo ai suoi testi; dentro, le foto vanno in ordine di scatto.
    L'impaginazione di un capitolo si può scrivere in structure.json ("layout"); se manca, la fa arrange()."""
    def __init__(self, name):
        # self.slug è il percorso dell'album nel sito (album/<nome>): cartella, indirizzo della pagina, foto
        self.name = name.split('/')[-1]
        self.slug = f'{ALBUM_DIR}/{self.name}'
        slug = self.slug
        self.folder = os.path.join(ROOT, slug)
        st = read_json(self.folder, 'structure.json')
        self.info = st
        self.notime = set(st.get('no_time', []))
        self.gps = {k: (tuple(v) if v else None) for k, v in st.get('gps', {}).items()}
        pdir = os.path.join(self.folder, 'photos')
        self.where, self.chapters = {}, []
        found = sorted((int(m.group(1)), d) for d in os.listdir(pdir)
                       if os.path.isdir(os.path.join(pdir, d)) and (m := CHAPTER_DIR.match(d)))
        nums = [n for n, _ in found]
        assert len(nums) == len(set(nums)), f'{slug}/photos: due cartelle con lo stesso numero di capitolo: {found}'
        for d in sorted(os.listdir(pdir)):
            if os.path.isdir(os.path.join(pdir, d)) and d != 'web' and not CHAPTER_DIR.match(d):
                warn(f'{slug}/photos/{d} non inizia con un numero: non è un capitolo, le sue foto non compaiono')
        for n, d in found:
            files = sorted(os.listdir(os.path.join(pdir, d)))
            for f in files:
                stem, ext = os.path.splitext(f)
                if ext.lower() in ('.jpeg', '.png', '.tif', '.tiff', '.heic') or ext == '.JPG':
                    warn(f'{slug}/photos/{d}/{f} ignorata: servono JPEG con estensione .jpg')
                if ext != '.jpg':
                    continue
                assert stem not in self.where, f'{slug}: la foto {stem} è in due capitoli ({self.where.get(stem)} e {d})'
                self.where[stem] = d
            self.chapters.append({'num': str(n), 'dir': d, 'photos': [f[:-4] for f in files if f.endswith('.jpg')],
                                  'blocks': st.get('layout', {}).get(str(n))})
        self.names = list(self.where)          # tutte le foto; arrange() le mette nell'ordine della pagina
        mapdir = os.path.join(self.folder, 'map')
        self.map = RouteMap(mapdir) if os.path.exists(os.path.join(mapdir, 'route.json')) else None
        self.check()

    def photo(self, name):
        """Percorso dell'originale, relativo alla radice del sito."""
        return f'{self.slug}/photos/{self.where[name]}/{name}.jpg'

    def check(self):
        assert self.chapters, f'{self.slug}/photos: nessuna cartella di capitolo (1-…, 2-…)'
        for k in ('hero', 'preview'):
            n = self.info.get(k, self.info['hero'])
            assert n in self.where, f'{self.slug}/structure.json: la foto "{k}" ({n}) non è in nessuna cartella di capitolo'

    def arrange(self, meta):
        """Ordina le foto di ogni capitolo per ora di scatto e completa l'impaginazione.
        Un capitolo senza "layout" in structure.json viene impaginato da solo; se il layout c'è ma nella cartella
        ci sono foto in più, queste si aggiungono in fondo al capitolo (così una foto aggiunta compare sempre)."""
        info = lambda n: meta[self.photo(n)]
        when = lambda n: (info(n)['date'], info(n)['time'], n)
        for ch in self.chapters:
            photos = sorted(ch['photos'], key=when)
            given = ch['blocks'] or []
            used = [n for b in given for n in blocks_photos(b)]
            wrong = [n for n in used if self.where.get(n) != ch['dir']]
            assert not wrong, f'{self.slug}/structure.json, capitolo {ch["num"]}: {wrong} non sono nella cartella {ch["dir"]}'
            extra = [n for n in photos if n not in used]
            if given and extra:
                print(f'{self.slug}, capitolo {ch["num"]}: impaginate in automatico in fondo al capitolo: {", ".join(extra)}')
            ch['blocks'] = given + auto_layout(extra, lambda n: info(n)['w'] / info(n)['h'])
        self.names = [n for ch in self.chapters for b in ch['blocks'] for n in blocks_photos(b)]

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
        if missing:
            warn(f'didascalie da scrivere in {self.slug}/texts/{lang}.json: {", ".join(missing)}')
        for ch in self.chapters:              # capitolo senza testi: titolo dal nome della cartella
            if ch['num'] not in t['chapters']:
                warn(f'capitolo {ch["num"]} senza testi in {self.slug}/texts/{lang}.json')
                name = CHAPTER_DIR.sub(lambda m: ch['dir'][len(m.group(1)):], ch['dir']).strip('-_ ').replace('-', ' ')
                t['chapters'][ch['num']] = {'title': name[:1].upper() + name[1:], 'date': '', 'intro': ''}
        return t


# ---------- foto ----------
def process(path):
    """Legge dal file a piena risoluzione i dati di scatto, le dimensioni e la posizione GPS.
    Se qualche dato manca (foto unite, scansioni, telefono…) mostra solo quelli che ci sono."""
    im = Image.open(os.path.join(ROOT, path))
    ex = im.getexif(); sub = ex.get_ifd(0x8769)
    parts = []
    if 37386 in sub: parts.append(f'{float(sub[37386]):g} mm')
    if 33437 in sub: parts.append(f'f/{float(sub[33437]):g}')
    if 33434 in sub:
        t = float(sub[33434]); parts.append(f'1/{round(1/t)} s' if t < 1 else f'{t:g} s')
    if 34855 in sub: parts.append(f'ISO {sub[34855]}')
    info = dict(
        exif=' · '.join(parts),
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
WEB = {}   # originale -> [(larghezza, copia)], riempito da build()
MOBILE = '(max-width: 760px)'     # sotto questa larghezza le foto vanno una sotto l'altra (style.css)
MAIN_W = 'min(1200px, 100vw)'     # larghezza della colonna principale

def url(path):
    """Percorso sicuro per l'HTML: spazi e caratteri speciali nei nomi dei file vengono codificati (in srcset uno spazio romperebbe tutto)."""
    return quote(path)

def pic(src, up, sizes):
    """Attributi src/srcset/sizes di un'immagine: il browser sceglie la copia più piccola che basta."""
    v = WEB[src]
    fallback = next((p for w, p in v if w >= 1600), v[-1][1])
    return (f'src="{up}{url(fallback)}" srcset="{", ".join(f"{up}{url(p)} {w}w" for w, p in v)}" sizes="{sizes}"')

def largest(src, up):
    return up + url(WEB[src][-1][1])

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
        title, text = A['captions'].get(name, ['', ''])
        m = meta[al.photo(name)]
        parts = []
        if m['date']:
            parts.append(f'<i>{fmt_date(m["date"], T)}</i>')
        if name not in al.notime and m['time']:
            parts.append(f'<i>{fmt_time(m["time"], T)}</i>')
        gps = al.gps[name] if name in al.gps else m['gps']
        if gps:
            la, lo = gps
            txt = f'{"N" if la >= 0 else "S"} {abs(la):.4f}°, {"E" if lo >= 0 else "W"} {abs(lo):.4f}°'   # lettera prima del numero
            parts.append(f'<a href="https://www.openstreetmap.org/?mlat={la:.5f}&amp;mlon={lo:.5f}#map=13/{la:.5f}/{lo:.5f}" target="_blank" rel="noopener" title="{T["open_map"]}"><i>{txt}</i></a>')
        where = f'<span class="where">{" · ".join(parts)}</span>' if parts else ''
        sizes = f'{MOBILE} 100vw, {MAIN_W}' if share == 1 else f'{MOBILE} 100vw, calc({MAIN_W} * {share:.3f})'
        img = (f'<img {pic(al.photo(name), up, sizes)} data-full="{largest(al.photo(name), up)}" '
               f'width="{m["w"]}" height="{m["h"]}" alt="{esc(title.rstrip("."))}" loading="lazy" decoding="async">')
        return (f'<figure class="fig {cls}" style="--r:{m["w"]/m["h"]:.4f}">\n'
                f'  <button class="ph" type="button" aria-label="{T["open_full"]}: {esc(title)}">{img}</button>\n'
                f'  <figcaption><span class="no">{n[0]:02d}</span><p class="cap"><strong>{esc(title)}</strong> {esc(text)}</p>'
                f'<p class="meta">{where}<span class="cam">{" · ".join("<i>"+esc(x)+"</i>" for x in m["exif"].split(" · ") if x)}</span></p></figcaption>\n</figure>')

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
    shots = [meta[al.photo(x)] for x in al.names]
    hm = meta[al.photo(al.info['hero'])]
    # obiettivi: il nome scritto dalla fotocamera diventa quello di config.json (più nomi possono indicare lo stesso obiettivo)
    order = list(dict.fromkeys(CONFIG['lenses'].values()))
    lenses = sorted({CONFIG['lenses'].get(s['lens'], s['lens']) for s in shots if s['lens']},
                    key=lambda l: (order.index(l) if l in order else len(order), l))
    lens_html = '<br>'.join(lenses)
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

def places_section(lang, T, world):
    """Mappa del mondo della home (world_map.py): solo la mappa, senza titolo né didascalie."""
    if not world:
        return ''
    label = esc(T['places_alt'])
    return f'''  <section class="sec places" id="places" aria-label="{label}">
    <figure class="world"><div class="world-scroll">{world_map.svg(ROOT, world, label=label)}</div><span class="world-cue" aria-hidden="true"></span></figure>
  </section>
'''

def render_home(albums, lang, meta, ver, world=None):
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
      <source media="(orientation: portrait)" srcset="{", ".join(f"{up}{url(p)} {w}w" for w, p in WEB[cover["portrait"]])}" sizes="{cover_sizes(*cover_dims["portrait"])}">
      <img {pic(cover["landscape"], up, cover_sizes(*cover_dims["landscape"]))} alt="{esc(T["home_alt"])}" fetchpriority="high">
    </picture>
    <div class="cover-text"><h1>{AUTHOR}</h1></div>
    <span class="cue" aria-hidden="true"></span>
  </header>
  <section class="statement"><p>{esc(T["home_sub"])}</p></section>
{places_section(lang, T, world)}  <section class="sec" id="albums">
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
    paths = {al.photo(n) for al in albums for n in al.names}
    WEB.update(images.build(list(paths) + list(CONFIG['home_cover'].values()), ROOT))
    with ThreadPoolExecutor(8) as ex:
        meta = dict(ex.map(process, sorted(paths)))
    for al in albums:
        al.arrange(meta)
    ver = hashlib.md5(b''.join(open(f'{COMMON}/{f}','rb').read() for f in ('style.css', 'album.js', 'site.js'))).hexdigest()[:8]
    # luoghi per la mappa della home: database della libreria Foto (solo sul Mac) + GPS delle foto degli album
    extra = [meta[al.photo(n)]['gps'] for al in albums for n in al.names if meta[al.photo(n)]['gps']]
    world = world_map.load_places(ROOT, CONFIG.get('places_db', 'places/foto_geo.sqlite'), 'home/places.json', extra)
    print(f'mappa della home: {len(world)} luoghi')
    for lang in LANGS:
        for al in albums:
            render_album(al, lang, meta, ver)
        render_home(albums, lang, meta, ver, world)
    for al in albums:
        print(f'{al.slug}: {len(al.names)} foto, {len(al.chapters)} capitoli')
    print('lingue:', ', '.join(LANGS))

if __name__ == '__main__':
    build()
