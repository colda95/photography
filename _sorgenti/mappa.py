"""Mappa del percorso (SVG in linea), disegnata a partire da dati geografici reali.
I colori vengono dal foglio di stile (classi .map-*), quindi seguono anche il tema scuro.
Fiumi, laghi e confini: Natural Earth (pubblico dominio). Rilievo ombreggiato: Natural Earth Shaded Relief."""
import math

LON0, LON1, LAT0, LAT1 = -116.1, -108.15, 34.95, 39.15
K = 190                                   # pixel per grado di latitudine
CL = math.cos(math.radians(37))           # correzione della longitudine a 37° N
PAD = 40
W = int((LON1 - LON0) * CL * K) + PAD * 2
H = int((LAT1 - LAT0) * K) + PAD * 2
X = lambda lon: PAD + (lon - LON0) * CL * K
Y = lambda lat: PAD + (LAT1 - lat) * K
pts = lambda seq: ' '.join(f'{X(lo):.1f},{Y(la):.1f}' for la, lo in seq)

# Dati geografici reali (Natural Earth, pubblico dominio): fiumi, laghi, confini, vette.
# Estratti una volta per l'area della mappa in mappa_dati.json.
import json as _json, os as _os
DATA = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'mappa_dati.json')))
RIVER_WIDTH = {'Colorado': 2.4, 'Green': 1.7, 'San Juan': 1.7, 'Little Colorado': 1.3, 'Virgin': 1.4}
WATER_LABELS = [('Colorado', 38.62, -109.30, 'start', 0), ('Lake Powell', 37.45, -110.52, 'start', 0),
                ('Lake Mead', 35.93, -114.28, 'middle', 0), ('San Juan', 37.30, -109.30, 'middle', 0),
                ('Green', 38.80, -110.05, 'end', 0), ('Virgin', 36.90, -113.72, 'start', 0),
                ('Little Colorado', 35.72, -111.30, 'middle', 0)]
REGION_LABELS = [('ALTOPIANO DEL COLORADO', 38.82, -113.0, 'region'), ('GREAT BASIN', 37.75, -115.35, 'region'),
                 ('La Sal Mountains', 38.33, -109.23, 'relief'), ('Henry Mountains', 38.05, -110.80, 'relief'),
                 ('Kaibab Plateau', 36.45, -112.18, 'relief'),
                 ('Aquarius Plateau', 38.02, -111.55, 'relief'), ('Navajo Mountain', 37.03, -110.87, 'relief')]
PEAK_NAMES = {'Humphreys Peak': ('Humphreys Peak', 12, 4, 'start'), 'Wheeler Peak': ('Wheeler Peak', 12, 4, 'start'),
              'Mount Peale': ('Mount Peale', 12, 4, 'start')}
STATES = [('NEVADA', 38.45, -115.9, 'start'), ('UTAH', 38.35, -111.0, 'middle'), ('ARIZONA', 35.45, -110.9, 'middle'),
          ('COLORADO', 38.2, -108.6, 'middle'), ('NEW MEXICO', 35.45, -108.6, 'middle'), ('CALIFORNIA', 35.1, -115.95, 'start')]


def _smooth(p, n=2):
    """Arrotonda le spezzate (algoritmo di Chaikin) mantenendo gli estremi."""
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p, p[1:]):
            q += [(0.75*a[0]+0.25*b[0], 0.75*a[1]+0.25*b[1]), (0.25*a[0]+0.75*b[0], 0.25*a[1]+0.75*b[1])]
        q.append(p[-1]); p = q
    return p


def _path(lonlat, closed=False):
    p = [(X(lo), Y(la)) for lo, la in lonlat]
    d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in p)
    return d + (' Z' if closed else '')


STOPS = [  # lat, lon, nome, sottotitolo, capitolo, dx, dy, allineamento
    (36.1699, -115.1398, 'Las Vegas', '', '', -16, 30, 'end'),
    (36.0577, -112.1389, 'Grand Canyon', '5 aprile', 'I', 18, 8, 'start'),
    (36.8617, -111.3743, 'Antelope Canyon', '6 aprile', 'II', 16, 34, 'start'),
    (36.9386, -110.0908, 'Monument Valley', '7 aprile', 'III', 16, 34, 'start'),
    (37.8606, -109.3756, 'Blue Mountains', '7–8 aprile', 'IV', -18, 6, 'end'),
    (38.7013, -109.5645, 'Arches', '8 aprile', 'V', -16, 30, 'end'),
    (37.5928, -112.1869, 'Bryce Canyon', '9 aprile', 'VI', 16, -18, 'start'),
    (37.2463, -112.8034, 'Il Ranch', '9–10 aprile', 'VII', 16, 24, 'start'),
    (37.2722, -112.9459, 'Zion', '10–11 aprile', 'VIII', -14, -20, 'end'),
]
ROUTE = [(36.1699, -115.1398), (35.9, -114.6), (35.33, -112.88), (35.25, -112.19), (36.0577, -112.1389), (36.8617, -111.3743),
         (36.9386, -110.0908), (37.1026, -109.9892), (37.8606, -109.3756), (38.57, -109.55), (38.7013, -109.5645),
         (38.95, -110.3), (38.6, -111.6), (37.9625, -111.9943), (37.5928, -112.1869), (37.2463, -112.8034),
         (37.2722, -112.9459), (37.1, -113.5), (36.8, -114.07), (36.1699, -115.1398)]


# spostamenti di disegno (in unità della mappa) per staccare tappe vicine; la posizione reale resta nei dati
SHIFT = {False: {'VII': (26, 3)}, True: {'VII': (34, 10), 'VIII': (-30, -8)}}


def _pill(x, y, num, s):
    """Etichetta numerata a forma di pillola: si allarga se il numero romano è lungo."""
    h = 22 * s
    w = max(h, (9 + 6.4 * len(num)) * s)
    return (f'<rect x="{x-w/2:.1f}" y="{y-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}" class="map-stop"/>'
            f'<text x="{x:.1f}" y="{y+3.6*s:.1f}" class="map-num" text-anchor="middle" style="font-size:{10*s:.1f}px">{num}</text>')


def svg(titles=None, relief_href="../assets/rilievo-usa.png", mobile=False):
    """Mappa del percorso. mobile=True: versione per schermi stretti, con segni più grandi e senza nomi delle tappe."""
    t = titles or {}
    s = 2.6 if mobile else 1.0
    shift = SHIFT[mobile]
    o = [f'<svg class="map {"map-mobile" if mobile else "map-desktop"}" viewBox="0 0 {W} {H}" role="img" aria-label="Mappa del percorso tra Nevada, Arizona e Utah, con le tappe numerate come i capitoli">']
    if not mobile:
        for lon in range(-116, -108):
            o.append(f'<text x="{X(lon)+4:.1f}" y="{H-PAD-6}" class="map-deg">{abs(lon)}° W</text>')
        for lat in range(35, 40):
            o.append(f'<text x="{W-PAD-4}" y="{Y(lat)-5:.1f}" class="map-deg" text-anchor="end">{lat}° N</text>')
    for lon in range(-116, -108):
        o.append(f'<line x1="{X(lon):.1f}" y1="{PAD}" x2="{X(lon):.1f}" y2="{H-PAD}" class="map-grid"/>')
    for lat in range(35, 40):
        o.append(f'<line x1="{PAD}" y1="{Y(lat):.1f}" x2="{W-PAD}" y2="{Y(lat):.1f}" class="map-grid"/>')
    o.append(f'<rect x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" class="map-frame"/>')
    cid = 'map-clip-m' if mobile else 'map-clip'
    o.append(f'<defs><clipPath id="{cid}"><rect x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}"/></clipPath></defs>')
    o.append(f'<g clip-path="url(#{cid})">')
    o.append(f'<image href="{relief_href}" x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" preserveAspectRatio="none" class="map-hill"/>')
    for b in DATA['borders']:
        o.append(f'<path class="map-border" style="stroke-width:{1.2*s:.1f}" d="{_path(b)}"/>')
    for lake in DATA['lakes']:
        o.append(f'<path class="map-lake" d="{_path(lake["pts"], True)}"/>')
    for r in DATA['rivers']:
        w = RIVER_WIDTH.get(r['name'], 1.0) * (1.8 if mobile else 1)
        o.append(f'<path class="map-river" style="stroke-width:{w:.1f}" d="{_path(_smooth(r["pts"]))}"/>')
    o.append('</g>')
    for name, la, lo, anc in STATES:
        if mobile and name in ('NEW MEXICO', 'CALIFORNIA', 'COLORADO'):
            continue
        o.append(f'<text x="{X(lo):.1f}" y="{Y(la):.1f}" class="map-state" text-anchor="{anc}">{name}</text>')
    if not mobile:
        for name, la, lo, kind in REGION_LABELS:
            o.append(f'<text x="{X(lo):.1f}" y="{Y(la):.1f}" class="map-{kind}" text-anchor="middle">{name}</text>')
        for pk in DATA['peaks']:
            lo, la = pk['pt']; x, y = X(lo), Y(la)
            label, dx, dy, anc = PEAK_NAMES.get(pk['name'], (pk['name'], 12, 4, 'start'))
            o.append(f'<path d="M{x-6:.1f},{y+5:.1f} L{x:.1f},{y-6:.1f} L{x+6:.1f},{y+5:.1f} Z" class="map-peak"/>'
                     f'<text x="{x+dx:.1f}" y="{y+dy:.1f}" class="map-small" text-anchor="{anc}">{label} · {pk["elev"]} m</text>')
        for name, la, lo, anc, _ in WATER_LABELS:
            o.append(f'<text x="{X(lo):.1f}" y="{Y(la):.1f}" class="map-water" text-anchor="{anc}">{name}</text>')
        o.append(f'<circle cx="{X(-109.045):.1f}" cy="{Y(37.0):.1f}" r="3" class="map-fc"/>'
                 f'<text x="{X(-109.045)+8:.1f}" y="{Y(37.0)+16:.1f}" class="map-small">Four Corners</text>')
    # percorso: passa per le posizioni disegnate delle tappe
    pos = {}
    for la, lo, name, sub, num, dx, dy, anc in STOPS:
        sx_, sy_ = shift.get(num, (0, 0))
        pos[(la, lo)] = (X(lo) + sx_, Y(la) + sy_)
    route = ' '.join('{:.1f},{:.1f}'.format(*pos.get((la, lo), (X(lo), Y(la)))) for la, lo in ROUTE)
    o.append(f'<polyline class="map-route" style="stroke-width:{3*s:.1f}" points="{route}"/>')
    for (la, lo, lab, dx, dy, anc) in [(35.33, -112.88, 'Route 66', 0, 22, 'middle'), (37.1026, -109.9892, 'Forrest Gump Point', 10, -6, 'start')]:
        o.append(f'<circle cx="{X(lo):.1f}" cy="{Y(la):.1f}" r="{4*s:.1f}" class="map-way" style="stroke-width:{2*s:.1f}"/>')
        if not mobile:
            o.append(f'<text x="{X(lo)+dx:.1f}" y="{Y(la)+dy:.1f}" class="map-small" text-anchor="{anc}">{lab}</text>')
    for la, lo, name, sub, num, dx, dy, anc in STOPS:
        x, y = pos[(la, lo)]
        name = t.get(num, name)
        if num:
            o.append(f'<a href="#cap-{num.lower()}" class="map-link"><title>Vai al capitolo {num}: {name}</title>' + _pill(x, y, num, s)
                     + ('' if mobile else f'<text x="{x+dx+(6 if anc=="start" else -6 if anc=="end" else 0):.1f}" y="{y+dy-4:.1f}" class="map-lab" text-anchor="{anc}">{name}</text>') + '</a>')
        else:
            q = 8 * s
            o.append(f'<rect x="{x-q:.1f}" y="{y-q:.1f}" width="{2*q:.1f}" height="{2*q:.1f}" class="map-start"/>')
            if not mobile:
                o.append(f'<text x="{x+dx:.1f}" y="{y+dy-24:.1f}" class="map-lab" text-anchor="{anc}">{name}</text>')
    km = 100 / 111.32 * K
    sx, sy = PAD + 40, H - PAD - 44
    o.append(f'<g class="map-scale" style="stroke-width:{1.5*s:.1f}"><line x1="{sx:.1f}" y1="{sy}" x2="{sx+km:.1f}" y2="{sy}"/>'
             f'<line x1="{sx:.1f}" y1="{sy-5*s}" x2="{sx:.1f}" y2="{sy+5*s}"/><line x1="{sx+km:.1f}" y1="{sy-5*s}" x2="{sx+km:.1f}" y2="{sy+5*s}"/></g>'
             f'<text x="{sx:.1f}" y="{sy-10*s:.1f}" class="map-small">100 km</text></svg>')
    return ''.join(o)


def legenda(titles=None):
    """Elenco numerato delle tappe, mostrato sotto la mappa solo sugli schermi stretti."""
    t = titles or {}
    items = ''.join(f'<li><a href="#cap-{num.lower()}"><span class="n">{num}</span>{t.get(num, name)}</a></li>'
                    for la, lo, name, sub, num, dx, dy, anc in STOPS if num)
    return f'<ol class="map-legend">{items}</ol>'
