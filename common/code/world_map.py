"""Mappa del mondo della home: i posti in cui ho fotografato, su una mappa a puntini.

Da dove vengono i luoghi:
  - places/foto_geo.sqlite (lo crea places/foto_geo.py dalla libreria Foto): resta solo sul Mac, non va su GitHub;
  - le coordinate GPS delle foto degli album.
Privacy: le coordinate esatte non finiscono mai nella pagina. Ogni luogo viene prima arrotondato al centro della sua
cella di una griglia di GRID_KM km (non si vede: i puntini sono molto più radi) e le date non si usano.
Il risultato va in home/places.json, l'unico file pubblicato: se il database non c'è (per esempio su un altro
computer), la build usa quello.

Disegno: la terra è fatta di puntini grigi su una griglia regolare (righe sfalsate, un puntino ogni DOT_KM km circa).
Si accendono in ocra i puntini entro LIT_KM km da un luogo. All'inizio è tutto nero: un'onda invisibile parte da Roma (ORIGIN) e scopre la mappa; ogni luogo accende comunque almeno il puntino della
griglia più vicino, anche dove la terra è troppo stretta per avere puntini suoi (isole piccole, coste frastagliate).
La mappa mostra solo l'area dei luoghi, che stanno sempre nella parte nitida (fuori dalle sfumature dei bordi):
aggiungendo luoghi si allarga da sola.
La terra viene da common/world.json (Natural Earth 1:50m, pubblico dominio, semplificata), in proiezione Natural Earth."""
import json, math, os, sqlite3

GRID_KM = 10                      # arrotondamento dei luoghi (privacy)
DOT_KM = 85                       # distanza tra i puntini della griglia
LIT_KM = 80                       # un puntino si accende se c'è un luogo entro questa distanza
DLAT = GRID_KM / 111.32
W = 1600                          # larghezza del disegno (unità SVG)
PAD_DEG = 4                       # aria attorno ai luoghi più estremi, in gradi
CLEAR = 0.75                      # i luoghi estremi stanno dove la sfumatura dei bordi è già oltre il 75% (quasi nitida)
EDGE_X, EDGE_Y = 0.16, 0.3          # quanto sfumano i bordi (frazione di larghezza e di altezza)
ORIGIN = (12.4964, 41.9028)       # Roma (lon, lat): da qui parte l'animazione dei puntini


def project(lon, lat):
    """Proiezione Natural Earth I (Šavrič et al.), in radianti."""
    l, p = math.radians(lon), math.radians(lat)
    p2 = p * p; p4 = p2 * p2
    x = l * (0.870700 - 0.131979 * p2 - 0.013791 * p4 + 0.003971 * p4 * p4 * p2 - 0.001529 * p4 * p4 * p4)
    y = p * (1.007226 + 0.015085 * p2 - 0.044475 * p4 * p2 + 0.028874 * p4 * p4 - 0.005916 * p4 * p4 * p2)
    return x, y


def cell(lat, lon):
    """Centro della cella di griglia (circa GRID_KM × GRID_KM km) che contiene il punto."""
    i = math.floor(lat / DLAT)
    clat = (i + 0.5) * DLAT
    dlon = DLAT / max(math.cos(math.radians(clat)), 0.05)
    j = math.floor(lon / dlon)
    return round(clat, 3), round((j + 0.5) * dlon, 3)


def load_places(root, db_rel, out_rel, extra=()):
    """Luoghi da disegnare: [(lat, lon)], già arrotondati. Aggiorna home/places.json."""
    db, out = os.path.join(root, db_rel), os.path.join(root, out_rel)
    if os.path.exists(db):
        con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
        rows = con.execute('SELECT lat, lon FROM luoghi WHERE rimossa = 0').fetchall()
        con.close()
        pts = [(la, lo) for la, lo in rows if la is not None and lo is not None and not (la == 0 and lo == 0)]
        cells = sorted({cell(la, lo) for la, lo in pts + list(extra)})
        txt = json.dumps({'grid_km': GRID_KM, 'places': [list(c) for c in cells]}, separators=(',', ':'))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if not os.path.exists(out) or open(out).read() != txt:
            open(out, 'w').write(txt)
        return cells
    if os.path.exists(out):
        data = json.load(open(out))
        return sorted({tuple(c) for c in data['places']} | {cell(la, lo) for la, lo in extra})
    return sorted({cell(la, lo) for la, lo in extra})


def _inside(x, y, poly):
    """Il punto è dentro il poligono (lista di (x, y))?"""
    c, j = False, len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def svg(root, places, label=''):
    """La mappa (un solo disegno: su telefono è più alta e si scorre di lato, vedi style.css)."""
    rings = json.load(open(os.path.join(root, 'common', 'world.json')))['rings']
    # area da mostrare: i luoghi, con un po' d'aria, devono stare nella parte nitida della mappa, cioè fuori dalle
    # fasce sfumate dei bordi (EDGE_X, EDGE_Y); la mappa si allarga quanto serve attorno a loro
    ps = [project(lo, la) for la, lo in places]
    pad = math.radians(PAD_DEG)
    ix0, ix1 = min(p[0] for p in ps) - pad, max(p[0] for p in ps) + pad
    iy0, iy1 = min(p[1] for p in ps) - pad, max(p[1] for p in ps) + pad
    tw = (ix1 - ix0) / (1 - 2 * EDGE_X * CLEAR)
    th = (iy1 - iy0) / (1 - 2 * EDGE_Y * CLEAR)
    X0, X1 = (ix0 + ix1 - tw) / 2, (ix0 + ix1 + tw) / 2
    Y0, Y1 = (iy0 + iy1 - th) / 2, (iy0 + iy1 + th) / 2
    k = W / (X1 - X0)
    H = (Y1 - Y0) * k
    pt = lambda lo, la: (lambda x, y: ((x - X0) * k, (Y1 - y) * k))(*project(lo, la))
    km = k / 6371 * 0.95                 # unità del disegno per km (circa, alle latitudini dei luoghi)

    # terra in unità del disegno, solo gli anelli che toccano l'area mostrata
    polys = [q for q in ([pt(r[i], r[i + 1]) for i in range(0, len(r), 2)] for r in rings)
             if max(p[0] for p in q) >= 0 and min(p[0] for p in q) <= W and max(p[1] for p in q) >= 0 and min(p[1] for p in q) <= H]
    pboxes = [(min(p[0] for p in q), max(p[0] for p in q), min(p[1] for p in q), max(p[1] for p in q)) for q in polys]
    on_land = lambda x, y: any(b[0] <= x <= b[1] and b[2] <= y <= b[3] and _inside(x, y, q) for b, q in zip(pboxes, polys))

    # griglia di puntini a righe sfalsate
    step = DOT_KM * km
    dy = step * math.sqrt(3) / 2
    node = lambda i, j: (j * step + (i % 2) * step / 2, i * dy)
    grid = [(i, j) for i in range(int(H / dy) + 1) for j in range(int(W / step) + 1)]
    land = {g for g in grid if on_land(*node(*g))}
    P = [pt(lo, la) for la, lo in places]
    lit, rl = set(), (LIT_KM * km) ** 2
    for x, y in P:
        near = [g for g in land if (node(*g)[0] - x) ** 2 + (node(*g)[1] - y) ** 2 < rl]
        if near:
            lit.update(near)
        else:                            # terra troppo stretta per la griglia: si accende il puntino più vicino
            i = round(y / dy)
            j = round((x - (i % 2) * step / 2) / step)
            lit.add(min(((a, b) for a in (i - 1, i, i + 1) for b in (j - 1, j, j + 1)),
                        key=lambda g: (node(*g)[0] - x) ** 2 + (node(*g)[1] - y) ** 2))
    # posizioni con un decimale: arrotondate all'intero, righe e colonne non sarebbero equidistanti (effetto "griglia")
    grey = ''.join(f'M{node(*g)[0]:.1f} {node(*g)[1]:.1f}h0' for g in sorted(land | lit))   # anche sotto quelli accesi: niente buchi
    # i puntini accesi compaiono a onda partendo da Roma (dove sono nato): --d va da 0 (Roma) a 1 (il più lontano)
    # comparsa: dal nero, un'onda invisibile parte da Roma (dove sono nato) e scopre la mappa allargandosi.
    # È una maschera circolare dal bordo morbido (raggio REV) che cresce da 0; i puntini accesi si accendono quando
    # il bordo li raggiunge: --d va da 0 (Roma) a 1 (fine dell'onda)
    rx, ry = pt(*ORIGIN)
    rev = max(math.hypot(cx - rx, cy - ry) for cx in (0, W) for cy in (0, H)) / 0.85
    dots = ''.join(f'<circle class="world-dot" cx="{node(*g)[0]:.2f}" cy="{node(*g)[1]:.2f}" r="{step * 0.3:.2f}" '
                   f'style="--d:{min(1, math.hypot(node(*g)[0] - rx, node(*g)[1] - ry) / (rev * 0.92)):.3f}"/>'
                   for g in sorted(lit, key=lambda g: math.hypot(node(*g)[0] - rx, node(*g)[1] - ry)))

    fx, _ = pt(10, 46)                  # su telefono la mappa si apre centrata sull'Europa
    # bordi sfumati nel nero della pagina: più ampi in alto e in basso, così la mappa si fonde con i testi vicini.
    # La sfumatura segue una curva morbida (smoothstep), senza un punto in cui si veda l'inizio
    def stops(edge):
        ease = [(k / 8, (k / 8) ** 2 * (3 - 2 * k / 8)) for k in range(9)]
        return (''.join(f'<stop offset="{edge * a:.3f}" stop-color="#fff" stop-opacity="{v:.3f}"/>' for a, v in ease) +
                ''.join(f'<stop offset="{1 - edge * a:.3f}" stop-color="#fff" stop-opacity="{v:.3f}"/>' for a, v in reversed(ease)))
    vb = f'x="0" y="0" width="{W}" height="{H:.0f}"'
    return (f'<svg class="world-svg" style="--ar:{W / H:.4f}" data-focus="{min(max(fx / W, 0), 1):.3f}" viewBox="0 0 {W} {H:.0f}" role="img" aria-label="{label}">'
            f'<defs><linearGradient id="wfx" x1="0" x2="1">{stops(EDGE_X)}</linearGradient>'
            f'<linearGradient id="wfy" x1="0" x2="0" y1="0" y2="1">{stops(EDGE_Y)}</linearGradient>'
            f'<mask id="wmx" maskUnits="userSpaceOnUse" {vb}><rect {vb} fill="url(#wfx)"/></mask>'
            f'<mask id="wmy" maskUnits="userSpaceOnUse" {vb}><rect {vb} fill="url(#wfy)"/></mask>'
            f'<radialGradient id="wrg"><stop offset=".85" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
            f'<mask id="wrv" maskUnits="userSpaceOnUse" {vb}><circle class="world-reveal" cx="{rx:.1f}" cy="{ry:.1f}" r="{rev:.1f}" fill="url(#wrg)"/></mask></defs>'
            f'<g mask="url(#wmx)"><g mask="url(#wmy)"><g mask="url(#wrv)">'
            f'<path class="world-grid" d="{grey}" stroke-width="{step * 0.5:.1f}"/>'
            f'<g class="world-lit">{dots}</g>'
            f'</g></g></g></svg>')
