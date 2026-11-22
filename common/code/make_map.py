"""Prepara la mappa del percorso di un album, partendo dalle foto. Stesso aspetto per tutti gli album.

Uso:  python3 common/code/make_map.py <album>              es.  python3 common/code/make_map.py islanda-2027
      python3 common/code/make_map.py <album> --force      ricrea anche route.json se esiste già

Cosa fa, nella cartella <album>/map/:
  route.json    tappe (una per capitolo, nella posizione media delle sue foto con GPS), percorso che le unisce
                nell'ordine dei capitoli, area e scala della mappa, nomi di stati e regioni. Se esiste già, non lo tocca
                (a meno di --force): così le correzioni fatte a mano restano.
  geodata.json  fiumi, laghi e confini dell'area, scaricati da Natural Earth (pubblico dominio).
E aggiunge ai testi dell'album (texts/<lingua>.json) i testi della mappa che mancano, da rivedere.

Il rilievo (relief.png, elevation.png) richiede un modello del terreno: lo script spiega come scaricarlo.
Senza rilievo la mappa funziona lo stesso, solo più piatta.

Dopo, in route.json si può rifinire a mano: posizione delle etichette (dx, dy, allineamento), punti intermedi del
percorso (route) per seguire le strade, etichette di fiumi e montagne (water_labels, region_labels)."""
import json, math, os, statistics, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_site as B

NE = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{}.geojson'
CACHE = os.path.join(tempfile.gettempdir(), 'natural-earth')
WIDTH = 1200                      # larghezza della mappa in pixel (come quella di usa-2026)
ASPECT = 1.45                     # proporzione larghezza / altezza
DEFAULT_TEXTS = {
    'it': dict(map_title='{n} tappe', map_description='Mappa del percorso, con le tappe numerate come i capitoli',
               map_credit='Fiumi, laghi e confini: Natural Earth<br>Altimetria del terreno: NASA SRTM, tramite OpenTopography'),
    'en': dict(map_title='{n} stops', map_description='Map of the route, with the stops numbered like the chapters',
               map_credit='Rivers, lakes and borders: Natural Earth<br>Terrain altimetry: NASA SRTM, via OpenTopography'),
}


def ne(name):
    """Scarica (una volta sola) un livello di Natural Earth."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + '.geojson')
    if not os.path.exists(path):
        print(f'  scarico {name} da Natural Earth…')
        urllib.request.urlretrieve(NE.format(name), path)
    return json.load(open(path, encoding='utf-8'))


def lines(geom):
    if not geom: return []
    t, c = geom['type'], geom['coordinates']
    return [c] if t == 'LineString' else c if t == 'MultiLineString' else []


def rings(geom):
    if not geom: return []
    t, c = geom['type'], geom['coordinates']
    return [c[0]] if t == 'Polygon' else [p[0] for p in c] if t == 'MultiPolygon' else []


def inside(pt, ring):
    """Il punto sta dentro il poligono? (metodo del raggio)"""
    x, y, ok = pt[0], pt[1], False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ok = not ok
    return ok


def clip(line, box):
    """Tratti di una linea che cadono nell'area (con un punto in più ai lati, per non interrompere il disegno)."""
    lo0, lo1, la0, la1 = box
    inside = [lo0 <= x <= lo1 and la0 <= y <= la1 for x, y in line]
    parts, cur = [], []
    for i, p in enumerate(line):
        near = inside[i] or (i > 0 and inside[i - 1]) or (i + 1 < len(line) and inside[i + 1])
        if near:
            cur.append([round(p[0], 4), round(p[1], 4)])
        elif cur:
            parts.append(cur); cur = []
    if cur: parts.append(cur)
    return [p for p in parts if len(p) > 1]


def place_labels(stops, area, K, cl, pad=40):
    """Sceglie dove scrivere il nome di ogni tappa (a destra, a sinistra, sopra o sotto) per non accavallarlo
    agli altri nomi e alle tappe; stacca le tappe troppo vicine. Modifica stops e restituisce gli spostamenti."""
    X = lambda lo: pad + (lo - area['lon0']) * cl * K
    Y = lambda la: pad + (area['lat1'] - la) * K
    W, H = (area['lon1'] - area['lon0']) * cl * K + 2 * pad, (area['lat1'] - area['lat0']) * K + 2 * pad
    pos = [[X(s[1]), Y(s[0])] for s in stops]
    shift = {'desktop': {}, 'mobile': {}}
    for mode, size in (('desktop', 32), ('mobile', 62)):        # le pillole su telefono sono 2,6 volte più grandi
        p = [list(q) for q in pos]
        for i in range(len(p)):
            for j in range(i):
                dx, dy = p[i][0] - p[j][0], p[i][1] - p[j][1]
                d = math.hypot(dx, dy)
                if d < size:
                    ux, uy = (dx / d, dy / d) if d else (1, 0)
                    mx, my = ux * (size - d), uy * (size - d)
                    p[i][0] += mx; p[i][1] += my
                    shift[mode][stops[i][4]] = [round(p[i][0] - pos[i][0]), round(p[i][1] - pos[i][1])]
        if mode == 'desktop': pos = p
    boxes = [(x - 13, y - 13, x + 13, y + 13) for x, y in pos]          # le tappe sono ostacoli
    overlap = lambda a, b: max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    for s, (x, y) in zip(stops, pos):
        w = len(s[2]) * 11.5 + 4
        best = None
        for k, (dx, dy, anc) in enumerate(((8, 10, 'start'), (-8, 10, 'end'), (0, -12, 'middle'), (0, 34, 'middle'))):
            base = y + dy - 4
            x0 = x + dx + 6 if anc == 'start' else x + dx - 6 - w if anc == 'end' else x - w / 2
            box = (x0, base - 17, x0 + w, base + 5)
            cost = sum(overlap(box, o) for o in boxes) * 10 + k * 40
            cost += 1e4 * (box[0] < pad) + 1e4 * (box[2] > W - pad) + 1e4 * (box[1] < pad) + 1e4 * (box[3] > H - pad)
            if best is None or cost < best[0]:
                best = (cost, dx, dy, anc, box)
        s[5], s[6], s[7] = best[1], best[2], best[3]
        boxes.append(best[4])
    return shift


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        sys.exit(__doc__)
    slug, force = args[0], '--force' in sys.argv
    al = B.Album(slug)
    mapdir = os.path.join(al.folder, 'map')
    os.makedirs(mapdir, exist_ok=True)
    texts = {l: al.texts(l) for l in B.LANGS}
    main_t = texts[B.MAIN]

    # --- tappe dalle foto ---
    print(f'{slug}: leggo le posizioni GPS delle foto…')
    stops = []
    for ch in al.chapters:
        pts = []
        for n in [n for b in ch['blocks'] for n in B.blocks_photos(b)]:
            g = al.gps[n] if n in al.gps else B.process(al.photo(n, B.FULL_SIZE))[1]['gps']
            if g: pts.append(g)
        if not pts:
            print(f'  capitolo {ch["num"]}: nessuna foto con GPS, niente tappa sulla mappa'); continue
        la, lo = statistics.median(p[0] for p in pts), statistics.median(p[1] for p in pts)
        name = main_t.get('map_names', {}).get(ch['num']) or main_t['chapters'][ch['num']]['title']
        stops.append([round(la, 4), round(lo, 4), name, '', ch['num'], 8, 10, 'start'])
    if not stops:
        sys.exit('Nessuna foto con GPS: non posso disegnare la mappa.')

    # --- area e scala ---
    las, los = [s[0] for s in stops], [s[1] for s in stops]
    lat_ref = (min(las) + max(las)) / 2
    cl = math.cos(math.radians(lat_ref))
    span_la, span_lo = max(max(las) - min(las), .2), max(max(los) - min(los), .2)
    span_la, span_lo = span_la * 1.35 + .2, span_lo * 1.35 + .3            # margine per le etichette
    if span_lo * cl / span_la < ASPECT: span_lo = span_la * ASPECT / cl     # proporzione fissa, uguale per tutti gli album
    else: span_la = span_lo * cl / ASPECT
    cla, clo = (min(las) + max(las)) / 2, (min(los) + max(los)) / 2
    area = dict(lon0=round(clo - span_lo / 2, 3), lon1=round(clo + span_lo / 2, 3), lat0=round(cla - span_la / 2, 3), lat1=round(cla + span_la / 2, 3))
    box = (area['lon0'], area['lon1'], area['lat0'], area['lat1'])
    print(f'  area: lon {box[0]} / {box[1]}, lat {box[2]} / {box[3]}')

    # --- route.json ---
    route_path = os.path.join(mapdir, 'route.json')
    if os.path.exists(route_path) and not force:
        print('  route.json esiste già: lo lascio com\'è (usa --force per ricrearlo)')
        box = tuple(json.load(open(route_path))['area'][k] for k in ('lon0', 'lon1', 'lat0', 'lat1'))
    else:
        # nomi di stati e regioni: per ognuno, il punto più centrale della parte visibile sulla mappa
        # (con i contorni veri di Natural Earth; le regioni che si vedono appena restano senza nome)
        inner = (box[0] + span_lo * .08, box[1] - span_lo * .08, box[2] + span_la * .08, box[3] - span_la * .08)
        nx, ny = 28, 18
        grid = [(inner[0] + (inner[1] - inner[0]) * (i + .5) / nx, inner[2] + (inner[3] - inner[2]) * (j + .5) / ny) for i in range(nx) for j in range(ny)]
        found = {}
        for f in ne('ne_10m_admin_1_states_provinces')['features']:
            for r in rings(f['geometry']):
                xs, ys = [p[0] for p in r], [p[1] for p in r]
                if max(xs) < inner[0] or min(xs) > inner[1] or max(ys) < inner[2] or min(ys) > inner[3]:
                    continue
                for g in grid:
                    if g not in found and inside(g, r):
                        found[g] = f['properties'].get('name') or ''
        states = []
        for name in sorted(set(found.values())):
            pts = [g for g, n in found.items() if n == name]
            if not name or len(pts) < len(grid) * .04:
                continue
            mx, my = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            x, y = min(pts, key=lambda p: (p[0] - mx) ** 2 + ((p[1] - my) / cl) ** 2)
            states.append([name.upper(), round(y, 3), round(x, 3), 'middle'])
        scale = round(WIDTH / (span_lo * cl))
        shift = place_labels(stops, area, scale, cl)
        route = dict(area=area, scale=scale, lat_ref=round(lat_ref, 2), pad=40,
                     river_width={}, water_labels=[], region_labels=[], states=[s for s in states if s[0]],
                     mobile_hidden_states=[], markers=[], waypoints=[],
                     stops=stops, route=[[s[0], s[1]] for s in stops],
                     shift=shift)
        open(route_path, 'w', encoding='utf-8').write(json.dumps(route, ensure_ascii=False, indent=1) + '\n')
        print(f'  scritto {slug}/map/route.json: {len(stops)} tappe, {len(route["states"])} nomi di stati o regioni')

    # --- geodata.json da Natural Earth ---
    big = (box[0] - (box[1] - box[0]) * .2, box[1] + (box[1] - box[0]) * .2, box[2] - (box[3] - box[2]) * .2, box[3] + (box[3] - box[2]) * .2)
    rivers = []
    for f in ne('ne_10m_rivers_lake_centerlines')['features']:
        for ln in lines(f['geometry']):
            for part in clip(ln, big):
                rivers.append(dict(name=f['properties'].get('name') or '', rank=f['properties'].get('scalerank'), pts=part))
    lakes = []
    for f in ne('ne_10m_lakes')['features']:
        for r in rings(f['geometry']):
            if any(big[0] <= x <= big[1] and big[2] <= y <= big[3] for x, y in r):
                lakes.append(dict(name=f['properties'].get('name') or '', pts=[[round(x, 4), round(y, 4)] for x, y in r]))
    borders = []
    for layer in ('ne_10m_admin_0_boundary_lines_land', 'ne_10m_admin_1_states_provinces_lines'):
        for f in ne(layer)['features']:
            for ln in lines(f['geometry']):
                borders += clip(ln, big)
    geo = dict(rivers=rivers, lakes=lakes, borders=borders)
    open(os.path.join(mapdir, 'geodata.json'), 'w', encoding='utf-8').write(json.dumps(geo, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f'  scritto {slug}/map/geodata.json: {len(rivers)} tratti di fiume, {len(lakes)} laghi, {len(borders)} tratti di confine')

    # --- testi della mappa mancanti ---
    for l in B.LANGS:
        p = os.path.join(al.folder, 'texts', f'{l}.json')
        t = json.load(open(p, encoding='utf-8'))
        d = DEFAULT_TEXTS.get(l, DEFAULT_TEXTS['en'])
        added = [k for k in d if k not in t]
        for k in added:
            t[k] = d[k].format(n=len(stops))
        if added:
            open(p, 'w', encoding='utf-8').write(json.dumps(t, ensure_ascii=False, indent=1) + '\n')
            print(f'  aggiunti a {slug}/texts/{l}.json (da rivedere): {", ".join(added)}')

    # --- rilievo ---
    tifs = [f for f in os.listdir(mapdir) if f.endswith('.tif')]
    if tifs:
        print(f'  c\'è un modello del terreno ({tifs[0]}): per il rilievo lancia  python3 common/code/relief.py {slug}')
    else:
        print(f'''
Rilievo (facoltativo): scarica il modello del terreno da https://portal.opentopography.org/raster?opentopoID=OTSRTM.042013.4326.1
  (SRTM GL3, 90 m, formato GeoTIFF) con questi limiti:  ovest {box[0]}  est {box[1]}  sud {box[2]}  nord {box[3]}
  mettilo in {slug}/map/ e lancia:  python3 common/code/relief.py {slug}''')
    print('\nFatto. Rigenera il sito con  python3 common/code/build_site.py')


if __name__ == '__main__':
    main()
