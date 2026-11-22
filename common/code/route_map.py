"""Disegna la mappa del percorso di un album (SVG in linea), a partire da dati geografici reali.
Il codice è comune a tutti gli album; i dati di ogni mappa stanno nella cartella map/ dell'album:
  route.json               area, scala, etichette, tappe, percorso
  geodata.json             fiumi, laghi e confini (Natural Earth, pubblico dominio)
  relief.png, elevation.png  rilievo e quote alte, calcolati con relief.py
I colori vengono dal foglio di stile (classi .map-*)."""
import json, math, os
from types import SimpleNamespace


def _smooth(p, n=2):
    """Arrotonda le spezzate (algoritmo di Chaikin) mantenendo gli estremi."""
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p, p[1:]):
            q += [(0.75*a[0]+0.25*b[0], 0.75*a[1]+0.25*b[1]), (0.25*a[0]+0.75*b[0], 0.25*a[1]+0.75*b[1])]
        q.append(p[-1]); p = q
    return p


ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}

def arabic(num):
    """Numero della tappa da mostrare sulla mappa: 'VII' -> '7' (i capitoli possono essere scritti in numeri romani)."""
    if num.isdigit() or not all(c in ROMAN for c in num.upper()):
        return num
    v = [ROMAN[c] for c in num.upper()]
    return str(sum(-a if a < b else a for a, b in zip(v, v[1:] + [0])))


def _curve(p, t=0.32):
    """Linea morbida (Catmull-Rom) che passa esattamente per tutti i punti: niente spigoli nel percorso."""
    if len(p) < 3:
        return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in p)
    d = [f'M{p[0][0]:.1f},{p[0][1]:.1f}']
    for i in range(len(p) - 1):
        p0, p1, p2, p3 = p[max(i - 1, 0)], p[i], p[i + 1], p[min(i + 2, len(p) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3)
        d.append(f'C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}')
    return ' '.join(d)


def _pill(x, y, num, s):
    """Etichetta numerata a forma di pillola: si allarga se il numero romano è lungo."""
    h = 22 * s
    w = max(h, (9 + 6.4 * len(num)) * s)
    return (f'<rect x="{x-w/2:.1f}" y="{y-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h/2:.1f}" class="map-stop"/>'
            f'<text x="{x:.1f}" y="{y+3.6*s:.1f}" class="map-num" text-anchor="middle" style="font-size:{10*s:.1f}px">{num}</text>')


class RouteMap:
    """La mappa di un album. folder = <slug>/map."""

    def __init__(self, folder):
        p = json.load(open(os.path.join(folder, 'route.json'), encoding='utf-8'))
        a = p['area']
        self.m = m = SimpleNamespace(
            LON0=a['lon0'], LON1=a['lon1'], LAT0=a['lat0'], LAT1=a['lat1'], K=p['scale'], LAT_REF=p['lat_ref'], PAD=p['pad'],
            RIVER_WIDTH=p['river_width'], WATER_LABELS=p['water_labels'], REGION_LABELS=p['region_labels'],
            STATES=p['states'], MOBILE_HIDDEN_STATES=p['mobile_hidden_states'], MARKERS=p['markers'], WAYPOINTS=p['waypoints'],
            STOPS=p['stops'], ROUTE=[tuple(x) for x in p['route']],
            SHIFT={False: {k: tuple(v) for k, v in p['shift']['desktop'].items()},
                   True: {k: tuple(v) for k, v in p['shift']['mobile'].items()}})
        geo = os.path.join(folder, 'geodata.json')          # fiumi, laghi, confini: se mancano, la mappa esce senza
        self.data = json.load(open(geo, encoding='utf-8')) if os.path.exists(geo) else dict(rivers=[], lakes=[], borders=[])
        self.CL = math.cos(math.radians(m.LAT_REF))
        self.W = int((m.LON1 - m.LON0) * self.CL * m.K) + m.PAD * 2
        self.H = int((m.LAT1 - m.LAT0) * m.K) + m.PAD * 2

    def X(self, lon): return self.m.PAD + (lon - self.m.LON0) * self.CL * self.m.K
    def Y(self, lat): return self.m.PAD + (self.m.LAT1 - lat) * self.m.K

    def _path(self, lonlat, closed=False):
        p = [(self.X(lo), self.Y(la)) for lo, la in lonlat]
        d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in p)
        return d + (' Z' if closed else '')

    def svg(self, relief_href, quota_href, titles=None, text=('', ''), mobile=False):
        """mobile=True: versione per schermi stretti, con segni più grandi e senza nomi delle tappe.
        titles = nomi delle tappe per numero di capitolo; text = (descrizione della mappa, testo del link alle tappe).
        Entrambi nella lingua della pagina."""
        m, X, Y, W, H, PAD = self.m, self.X, self.Y, self.W, self.H, self.m.PAD
        t = titles or {}
        s = 2.6 if mobile else 1.0
        shift = m.SHIFT[mobile]
        lons = range(math.ceil(m.LON0), math.floor(m.LON1) + 1)
        lats = range(math.ceil(m.LAT0), math.floor(m.LAT1) + 1)
        # inquadratura: tutta la mappa su computer; su telefono solo la zona del percorso, altrimenti sarebbe minuscola
        vx, vy, vw, vh = PAD, PAD, W - 2 * PAD, H - 2 * PAD
        if mobile:
            pts = [(X(r[1]) + shift.get(r[4], (0, 0))[0], Y(r[0]) + shift.get(r[4], (0, 0))[1]) for r in m.STOPS]
            pts += [(X(lo), Y(la)) for la, lo in m.ROUTE]
            x0, x1, y0, y1 = min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)
            margin = 0.2 * max(x1 - x0, y1 - y0) + 40
            x0, x1, y0, y1 = x0 - margin, x1 + margin, y0 - margin, y1 + margin
            w, h = x1 - x0, y1 - y0
            if w / h < 1.0: x0 -= (h - w) / 2; x1 += (h - w) / 2
            elif w / h > 1.35: y0 -= (w / 1.35 - h) / 2; y1 += (w / 1.35 - h) / 2
            x0, y0 = max(x0, PAD), max(y0, PAD); x1, y1 = min(x1, W - PAD), min(y1, H - PAD)
            vx, vy, vw, vh = round(x0), round(y0), round(x1 - x0), round(y1 - y0)
        o = [f'<svg class="map {"map-mobile" if mobile else "map-desktop"}" viewBox="{vx} {vy} {vw} {vh}" role="img" aria-label="{text[0]}">']
        o.append(f'<rect x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" class="map-land"/>')
        if not mobile:
            for lon in lons:
                o.append(f'<text x="{X(lon)+4:.1f}" y="{H-PAD-6}" class="map-deg">{abs(lon)}° {"W" if lon < 0 else "E"}</text>')
            for lat in lats:
                o.append(f'<text x="{W-PAD-4}" y="{Y(lat)-5:.1f}" class="map-deg" text-anchor="end">{abs(lat)}° {"N" if lat >= 0 else "S"}</text>')
        for lon in lons:
            o.append(f'<line x1="{X(lon):.1f}" y1="{PAD}" x2="{X(lon):.1f}" y2="{H-PAD}" class="map-grid"/>')
        for lat in lats:
            o.append(f'<line x1="{PAD}" y1="{Y(lat):.1f}" x2="{W-PAD}" y2="{Y(lat):.1f}" class="map-grid"/>')
        o.append(f'<rect x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" class="map-frame"/>')
        sfx = '-m' if mobile else ''
        cid = 'map-clip' + sfx
        # i livelli raster sono maschere: il colore arriva dal foglio di stile tramite questi filtri
        tint = lambda name: (f'<filter id="map-f-{name}{sfx}" color-interpolation-filters="sRGB"><feFlood class="map-flood-{name}"/>'
                             f'<feComposite in2="SourceAlpha" operator="in"/></filter>')
        # niente cornice: rilievo, fiumi e confini sfumano verso i bordi nel colore della pagina (le scritte restano nitide)
        # sfumatura morbida (curva "smoothstep"), più ampia su telefono; in più un'ellisse che spegne gli angoli,
        # così non si vede il rettangolo dell'immagine: la mappa nasce e svanisce nel nero della pagina
        edge = 0.3 if mobile else 0.22
        ease = [(k / 8, (k / 8) ** 2 * (3 - 2 * k / 8)) for k in range(9)]
        stops = lambda: ''.join(f'<stop offset="{edge*a:.3f}" stop-color="#fff" stop-opacity="{v:.3f}"/>' for a, v in ease) + \
            ''.join(f'<stop offset="{1-edge*a:.3f}" stop-color="#fff" stop-opacity="{v:.3f}"/>' for a, v in reversed(ease))
        mask = lambda mid, gid: (f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="{vx}" y="{vy}" width="{vw}" height="{vh}">'
                                 f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="url(#{gid})"/></mask>')
        fx, fy, fr = f'map-fx{sfx}', f'map-fy{sfx}', f'map-fr{sfx}'
        o.append(f'<defs><clipPath id="{cid}"><rect x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}"/></clipPath>{tint("high")}{tint("shade")}'
                 f'<linearGradient id="{fx}g" x1="0" y1="0" x2="1" y2="0">{stops()}</linearGradient>{mask(fx, fx + "g")}'
                 f'<linearGradient id="{fy}g" x1="0" y1="0" x2="0" y2="1">{stops()}</linearGradient>{mask(fy, fy + "g")}'
                 f'<radialGradient id="{fr}g" cx=".5" cy=".5" r=".72">'
                 + ''.join(f'<stop offset="{0.55 + 0.45 * a:.3f}" stop-color="#fff" stop-opacity="{1 - v:.3f}"/>' for a, v in ease)
                 + f'</radialGradient>{mask(fr, fr + "g")}</defs>')
        o.append(f'<g clip-path="url(#{cid})"><g mask="url(#{fx})"><g mask="url(#{fy})"><g mask="url(#{fr})">')
        if quota_href:
            o.append(f'<image href="{quota_href}" x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" preserveAspectRatio="none" class="map-high" filter="url(#map-f-high{sfx})"/>')
        if relief_href:
            o.append(f'<image href="{relief_href}" x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" preserveAspectRatio="none" class="map-hill" filter="url(#map-f-shade{sfx})"/>')
        for b in self.data['borders']:
            o.append(f'<path class="map-border" style="stroke-width:{1.2*s:.1f}" d="{self._path(b)}"/>')
        for lake in self.data['lakes']:
            o.append(f'<path class="map-lake" d="{self._path(lake["pts"], True)}"/>')
        for r in self.data['rivers']:
            w = m.RIVER_WIDTH.get(r['name'], 1.0) * (1.8 if mobile else 1)
            o.append(f'<path class="map-river" style="stroke-width:{w:.1f}" d="{self._path(_smooth(r["pts"]))}"/>')
        o.append('</g></g></g></g>')
        for name, la, lo, anc in m.STATES:
            if mobile and name in m.MOBILE_HIDDEN_STATES:
                continue
            o.append(f'<text x="{X(lo):.1f}" y="{Y(la):.1f}" class="map-state" text-anchor="{anc}">{name}</text>')
        if not mobile:
            for name, la, lo, kind in m.REGION_LABELS:
                o.append(f'<text x="{X(lo):.1f}" y="{Y(la):.1f}" class="map-{kind}" text-anchor="middle">{name}</text>')
            for name, la, lo, anc, _ in m.WATER_LABELS:
                o.append(f'<text x="{X(lo):.1f}" y="{Y(la):.1f}" class="map-water" text-anchor="{anc}">{name}</text>')
            for la, lo, name in m.MARKERS:
                o.append(f'<circle cx="{X(lo):.1f}" cy="{Y(la):.1f}" r="3" class="map-fc"/>'
                         f'<text x="{X(lo)+8:.1f}" y="{Y(la)+16:.1f}" class="map-small">{name}</text>')
        # percorso: passa per le posizioni disegnate delle tappe
        pos = {}
        for la, lo, name, sub, num, dx, dy, anc in m.STOPS:
            sx_, sy_ = shift.get(num, (0, 0))
            pos[(la, lo)] = (X(lo) + sx_, Y(la) + sy_)
        pts = [pos.get((la, lo), (X(lo), Y(la))) for la, lo in m.ROUTE]
        o.append(f'<path class="map-route" style="stroke-width:{3*s:.1f}" d="{_curve(pts)}"/>')
        for (la, lo, lab, dx, dy, anc) in m.WAYPOINTS:
            o.append(f'<circle cx="{X(lo):.1f}" cy="{Y(la):.1f}" r="{4*s:.1f}" class="map-way" style="stroke-width:{2*s:.1f}"/>')
            if not mobile:
                o.append(f'<text x="{X(lo)+dx:.1f}" y="{Y(la)+dy:.1f}" class="map-small" text-anchor="{anc}">{lab}</text>')
        for la, lo, name, sub, num, dx, dy, anc in m.STOPS:
            x, y = pos[(la, lo)]
            name = t.get(num, name)
            if num:
                o.append(f'<a href="#chapter-{arabic(num)}" class="map-link"><title>{text[1]} {arabic(num)}: {name}</title>' + _pill(x, y, arabic(num), s)
                         + ('' if mobile else f'<text x="{x+dx+(6 if anc=="start" else -6 if anc=="end" else 0):.1f}" y="{y+dy-4:.1f}" class="map-lab" text-anchor="{anc}">{name}</text>') + '</a>')
            else:
                q = 8 * s
                o.append(f'<rect x="{x-q:.1f}" y="{y-q:.1f}" width="{2*q:.1f}" height="{2*q:.1f}" class="map-start"/>')
                if not mobile:
                    o.append(f'<text x="{x+dx:.1f}" y="{y+dy-24:.1f}" class="map-lab" text-anchor="{anc}">{name}</text>')
        km = 100 / 111.32 * m.K
        sx, sy = vx + vw - 60 * s - km, vy + vh - 44 * s        # scala in basso a destra
        o.append(f'<g class="map-scale" style="stroke-width:{1.5*s:.1f}"><line x1="{sx:.1f}" y1="{sy}" x2="{sx+km:.1f}" y2="{sy}"/>'
                 f'<line x1="{sx:.1f}" y1="{sy-5*s}" x2="{sx:.1f}" y2="{sy+5*s}"/><line x1="{sx+km:.1f}" y1="{sy-5*s}" x2="{sx+km:.1f}" y2="{sy+5*s}"/></g>'
                 f'<text x="{sx:.1f}" y="{sy-10*s:.1f}" class="map-small">100 km</text></svg>')
        return ''.join(o)
