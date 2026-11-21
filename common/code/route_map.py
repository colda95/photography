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
        self.data = json.load(open(os.path.join(folder, 'geodata.json'), encoding='utf-8'))
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
        o = [f'<svg class="map {"map-mobile" if mobile else "map-desktop"}" viewBox="{PAD} {PAD} {W-2*PAD} {H-2*PAD}" role="img" aria-label="{text[0]}">']
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
        o.append(f'<defs><clipPath id="{cid}"><rect x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}"/></clipPath>{tint("high")}{tint("shade")}</defs>')
        o.append(f'<g clip-path="url(#{cid})">')
        o.append(f'<image href="{quota_href}" x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" preserveAspectRatio="none" class="map-high" filter="url(#map-f-high{sfx})"/>')
        o.append(f'<image href="{relief_href}" x="{PAD}" y="{PAD}" width="{W-2*PAD}" height="{H-2*PAD}" preserveAspectRatio="none" class="map-hill" filter="url(#map-f-shade{sfx})"/>')
        for b in self.data['borders']:
            o.append(f'<path class="map-border" style="stroke-width:{1.2*s:.1f}" d="{self._path(b)}"/>')
        for lake in self.data['lakes']:
            o.append(f'<path class="map-lake" d="{self._path(lake["pts"], True)}"/>')
        for r in self.data['rivers']:
            w = m.RIVER_WIDTH.get(r['name'], 1.0) * (1.8 if mobile else 1)
            o.append(f'<path class="map-river" style="stroke-width:{w:.1f}" d="{self._path(_smooth(r["pts"]))}"/>')
        o.append('</g>')
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
        route = ' '.join('{:.1f},{:.1f}'.format(*pos.get((la, lo), (X(lo), Y(la)))) for la, lo in m.ROUTE)
        o.append(f'<polyline class="map-route" style="stroke-width:{3*s:.1f}" points="{route}"/>')
        for (la, lo, lab, dx, dy, anc) in m.WAYPOINTS:
            o.append(f'<circle cx="{X(lo):.1f}" cy="{Y(la):.1f}" r="{4*s:.1f}" class="map-way" style="stroke-width:{2*s:.1f}"/>')
            if not mobile:
                o.append(f'<text x="{X(lo)+dx:.1f}" y="{Y(la)+dy:.1f}" class="map-small" text-anchor="{anc}">{lab}</text>')
        for la, lo, name, sub, num, dx, dy, anc in m.STOPS:
            x, y = pos[(la, lo)]
            name = t.get(num, name)
            if num:
                o.append(f'<a href="#cap-{num.lower()}" class="map-link"><title>{text[1]} {num}: {name}</title>' + _pill(x, y, num, s)
                         + ('' if mobile else f'<text x="{x+dx+(6 if anc=="start" else -6 if anc=="end" else 0):.1f}" y="{y+dy-4:.1f}" class="map-lab" text-anchor="{anc}">{name}</text>') + '</a>')
            else:
                q = 8 * s
                o.append(f'<rect x="{x-q:.1f}" y="{y-q:.1f}" width="{2*q:.1f}" height="{2*q:.1f}" class="map-start"/>')
                if not mobile:
                    o.append(f'<text x="{x+dx:.1f}" y="{y+dy-24:.1f}" class="map-lab" text-anchor="{anc}">{name}</text>')
        km = 100 / 111.32 * m.K
        sx, sy = PAD + 40, H - PAD - 44
        o.append(f'<g class="map-scale" style="stroke-width:{1.5*s:.1f}"><line x1="{sx:.1f}" y1="{sy}" x2="{sx+km:.1f}" y2="{sy}"/>'
                 f'<line x1="{sx:.1f}" y1="{sy-5*s}" x2="{sx:.1f}" y2="{sy+5*s}"/><line x1="{sx+km:.1f}" y1="{sy-5*s}" x2="{sx+km:.1f}" y2="{sy+5*s}"/></g>'
                 f'<text x="{sx:.1f}" y="{sy-10*s:.1f}" class="map-small">100 km</text></svg>')
        return ''.join(o)
