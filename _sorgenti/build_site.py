import hashlib, html, os, shutil, json, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

# Genera le pagine del sito (copertina e album) a partire da content_usa.py e testi_utente.json.
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
sys.path.insert(0, HERE)
from content_usa import ALBUM, CHAPTERS
import mappa
try:
    from content_usa import GPS as GPS_FIX
except ImportError:
    GPS_FIX = {}
# Testi modificati a mano nella pagina pubblicata: hanno la precedenza sul contenuto di partenza.
_T = os.path.join(HERE, 'testi_utente.json')
if os.path.exists(_T):
    _u = json.load(open(_T))
    ALBUM['lede'] = _u.get('lede', ALBUM['lede'])
    ALBUM['meta_description'] = _u.get('meta_description')
    ALBUM['footer_copy'] = _u.get('footer_copy')
    for _ch in CHAPTERS: _ch['title'] = _u.get('chapter_titles', {}).get(_ch['num'], _ch['title'])
    for _ch in CHAPTERS: _ch['route_title'] = _u.get('route_titles', {}).get(_ch['num'], _ch['title'])
    for _ch, _intro in zip(CHAPTERS, _u.get('intros', [])): _ch['intro'] = _intro
    def _fix(p):
        c = _u['captions'].get(p[0]); return (p[0], c[0], c[1], *p[3:]) if c else p
    for _ch in CHAPTERS:
        _ch['blocks'] = [(b[0], _fix(b[1])) if b[0] in ('full', 'wide') else (b[0], [_fix(p) for p in b[1]]) if b[0] == 'group'
                         else (b[0], _fix(b[1]), _fix(b[2]), b[3]) for b in _ch['blocks']]

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

def all_names():
    for ch in CHAPTERS:
        for b in ch['blocks']:
            if b[0] in ('full', 'wide'): yield b[1][0]
            elif b[0] == 'group':
                for p in b[1]: yield p[0]
            elif b[0] == 'offset': yield b[1][0]; yield b[2][0]

def build():
    slug = ALBUM['slug']; year = ALBUM['year']
    os.makedirs(f'{OUT}/{slug}', exist_ok=True)
    missing_page = [n for n in all_names() if not os.path.exists(f'{ROOT}/{PAGE_DIR}/{n}.jpg')]
    assert not missing_page, f'Mancano in {PAGE_DIR}: {missing_page}'
    names = list(all_names())
    assert len(names) == len(set(names)), 'foto duplicate'
    missing = sorted(set(os.path.splitext(f)[0] for f in os.listdir(SRC)) - set(names))
    extra = [n for n in names if not os.path.exists(f'{SRC}/{n}.jpg')]
    assert not extra, extra
    with ThreadPoolExecutor(8) as ex:
        meta = dict(ex.map(lambda n: process(n, f'{OUT}/{slug}/img', year), names + [ALBUM['hero'], ALBUM['cover']]))

    n = [0]
    def img_tag(name, alt, sizes, cls='', eager=False):
        m = meta[name]
        return (f'<img src="../{PAGE_DIR}/{name}.jpg" data-full="../{REPO_DIR}/{name}.jpg" '
                f'width="{m["w"]}" height="{m["h"]}" alt="{esc(alt)}"'
                + ('' if eager else ' loading="lazy"') + f' decoding="async"{cls}>')

    def fig(p, cls='', sizes='(max-width: 760px) 100vw, 60vw'):
        name, title, text = p[:3]; opt = p[3] if len(p) > 3 else {}
        n[0] += 1; m = meta[name]
        MESI = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic']
        parts = []
        if not opt.get('notime') and m['time']:
            parts.append(f'<i>{m["time"]}</i>')
        gps = GPS_FIX[name] if name in GPS_FIX else m['gps']
        if gps:
            la, lo = gps
            txt = f'{abs(la):.4f}° {"N" if la >= 0 else "S"}, {abs(lo):.4f}° {"E" if lo >= 0 else "W"}'
            parts.append(f'<a href="https://www.openstreetmap.org/?mlat={la:.5f}&amp;mlon={lo:.5f}#map=13/{la:.5f}/{lo:.5f}" target="_blank" rel="noopener" title="Apri sulla mappa"><i>{txt}</i></a>')
        where = f'<span class="where">{" · ".join(parts)}</span>' if parts else ''
        return (f'<figure class="fig {cls}" style="--r:{m["w"]/m["h"]:.4f}">\n'
                f'  <button class="ph" type="button" aria-label="Apri a schermo intero: {esc(title)}">{img_tag(name, title.rstrip("."), sizes)}</button>\n'
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
    <p class="kicker"><span>Capitolo {ch["num"]}</span><span>{ch["date"]}</span></p>
    <h2>{esc(ch["title"])}</h2>
    <p class="intro">{esc(ch["intro"])}</p>
  </header>
  {"".join(block(b) for b in ch["blocks"])}
</section>
'''
    route = ''.join(f'<li><a href="#cap-{c["num"].lower()}"><span class="d">{c["date"].replace(" 2026","")}</span><span class="p">{esc(c.get("route_title", c["title"]))}</span><span class="s">Cap. {c["num"]}</span></a></li>' for c in CHAPTERS)
    lenses = sorted({meta[x]['lens'] for x in names}, key=lambda l: ['16mm', 'RF24', 'RF100'].index(next(k for k in ['16mm', 'RF24', 'RF100'] if l.startswith(k))))
    lens_html = '<br>'.join(LENS[l][1] for l in lenses)
    total = n[0]
    hero = ALBUM['hero']

    head = lambda title, desc, css, path='': f'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="{AUTHOR}">
<meta name="copyright" content="© {year} {AUTHOR}. Tutti i diritti riservati.">
<meta name="robots" content="noai, noimageai">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}{path}">
<meta property="og:image" content="{SITE_URL}assets/og-terra-rossa.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="it_IT">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{css}">
</head>
<body>
'''
    ver = hashlib.md5(open(f'{ROOT}/assets/style.css','rb').read() + open(f'{ROOT}/assets/album.js','rb').read()).hexdigest()[:8]
    album = head(f'{ALBUM["title"]} · {AUTHOR}', ALBUM.get('meta_description') or ALBUM['lede'], f'../assets/style.css?v={ver}', f'{slug}/') + f'''<header class="hero">
  <nav class="topbar" aria-label="Navigazione"><a href="../">{AUTHOR}</a><a href="../">Tutti gli album</a></nav>
  <img src="../{PAGE_DIR}/{hero}.jpg" alt="La US-163 verso Monument Valley all’ultima luce" fetchpriority="high">
  <div class="hero-text">
    <h1>Terra<br>rossa</h1>
  </div>
</header>
<main>
  <section class="opening">
    <p class="lede">{esc(ALBUM["lede"])}</p>
    <figure class="route-map">
      <div class="map-head"><p class="kicker"><span>Il percorso</span></p><h2 class="map-title">Nove tappe, tre stati</h2></div>
      {mappa.svg()}{mappa.svg(mobile=True)}
      {mappa.legenda()}
      <figcaption class="map-note">Linea indicativa tra le tappe; posizioni dalle coordinate delle foto. Tocca un numero per andare al capitolo. Fiumi, laghi e confini: Natural Earth. Rilievo: NASA SRTM, tramite OpenTopography.</figcaption>
    </figure>
  </section>
{chapters_html}
  <footer class="colophon">
    <h2>Colophon</h2>
    <dl>
      <div><dt>Fotografie</dt><dd>{AUTHOR}</dd></div>
      <div><dt>Fotocamera</dt><dd>Canon EOS R7</dd></div>
      <div><dt>Obiettivi</dt><dd>{lens_html}</dd></div>
      <div><dt>Sviluppo</dt><dd>Adobe Lightroom</dd></div>
    </dl>
    {"".join(f'<p class="copy">{esc(x)}</p>' for x in ALBUM.get('footer_copy') or [f'© {year} {AUTHOR}. Tutti i diritti riservati.'])}
    <p class="copy"><a class="backlink" href="../">← Tutti gli album</a></p>
  </footer>
</main>
<div class="lb" id="lb" hidden><img alt=""><p class="lb-cap"></p><p class="lb-rot" hidden><svg viewBox="0 0 28 28" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="9" y="3" width="10" height="22" rx="2"/><path d="M13 21.5h2"/></svg>Ruota il telefono per vederla più grande</p><button type="button" class="lb-x" aria-label="Chiudi">Chiudi</button></div>
<script src="../assets/album.js?v={ver}"></script>
</body>
</html>
'''
    open(f'{OUT}/{slug}/index.html', 'w').write(album)

    cover = ALBUM['cover']; cm = meta[cover]
    home = head(f'{SITE_TITLE} · Fotografie', 'Album fotografici di viaggio di ' + AUTHOR + '.', f'assets/style.css?v={ver}') + f'''<main>
  <section class="home">
    <header class="home-head">
      <p class="kicker"><span>Fotografie</span><span>Album di viaggio</span></p>
      <h1>{AUTHOR}</h1>
      <p class="sub">Viaggi raccontati per immagini, scattati con una Canon EOS R7 e sviluppati in Lightroom.</p>
    </header>
    <ol class="albums">
      <li class="album"><a href="{slug}/">
        <img src="{PAGE_DIR}/{cover}.jpg" width="{cm["w"]}" height="{cm["h"]}" alt="Alba sull’anfiteatro di Bryce Canyon">
        <div class="meta">
          <p class="facts">{ALBUM["kicker"][0]}<br>{ALBUM["kicker"][1]}<br>{total} fotografie · {len(CHAPTERS)} capitoli</p>
          <h2>{ALBUM["title"]}</h2>
          <span class="go">Apri l’album →</span>
        </div>
      </a></li>
    </ol>
    <footer class="home-foot">© {year} {AUTHOR}. Tutti i diritti riservati.</footer>
  </section>
</main>
<script>document.addEventListener('contextmenu',function(e){{if(e.target.tagName==='IMG')e.preventDefault();}});</script>
</body>
</html>
'''
    open(f'{OUT}/index.html', 'w').write(home)
    print('foto:', total, 'non usate:', missing)

if __name__ == '__main__':
    build()
