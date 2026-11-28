"""Calcola il rilievo (ombreggiatura) e le quote alte per la mappa di un album, da un modello del terreno SRTM (GeoTIFF).
Uso:  python3 common/code/relief.py <album> [file.tif]     es.  python3 common/code/relief.py usa-2026
      (senza file, usa il primo .tif nella cartella map/ dell'album)
Serve:  pip3 install numpy pillow tifffile imagecodecs
Il GeoTIFF deve coprire almeno l'area della mappa (area in album/<album>/map/route.json): se è più grande, viene ritagliato.
Scrive album/<album>/map/relief.png e <album>/map/elevation.png."""
import math, os, sys
import numpy as np, tifffile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from route_map import RouteMap

SLUG = sys.argv[1].split('/')[-1]                     # nome dell'album (la cartella in album/)
DEST = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'album', SLUG, 'map')
M = RouteMap(DEST)
LON0, LON1, LAT0, LAT1, K, CL = M.m.LON0, M.m.LON1, M.m.LAT0, M.m.LAT1, M.m.K, M.CL
TIF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DEST, sorted(f for f in os.listdir(DEST) if f.endswith('.tif'))[0])

with tifffile.TiffFile(TIF) as tf:
    page = tf.pages[0]
    z = page.asarray()
    scale, tie = page.tags.get(33550), page.tags.get(33922)      # georeferenziazione del GeoTIFF
    if scale and tie:
        sx, sy, x0, y0 = scale.value[0], scale.value[1], tie.value[3], tie.value[4]
        c0, c1 = round((LON0 - x0) / sx), round((LON1 - x0) / sx)
        r0, r1 = round((y0 - LAT1) / sy), round((y0 - LAT0) / sy)
        assert c0 >= 0 and r0 >= 0 and c1 <= z.shape[1] and r1 <= z.shape[0], \
            f'Il modello del terreno ({x0:.2f}/{x0 + sx * z.shape[1]:.2f}, {y0 - sy * z.shape[0]:.2f}/{y0:.2f}) non copre tutta l\'area della mappa'
        z = z[r0:r1, c0:c1]
z = z.astype(np.float32)
z[z <= -100] = np.nan
z = np.nan_to_num(z, nan=float(np.nanmedian(z)))
S = 1.5                                           # risoluzione rispetto alla mappa (per schermi ad alta densità)
Wo, Ho = int((LON1 - LON0) * CL * K * S), int((LAT1 - LAT0) * K * S)
w2, h2 = Wo * 2, Ho * 2
a = np.asarray(Image.fromarray(z, 'F').resize((w2, h2), Image.BILINEAR))
dx = (LON1 - LON0) / w2 * 111320 * math.cos(math.radians((LAT0 + LAT1) / 2))
dy = (LAT1 - LAT0) / h2 * 110574
gy, gx = np.gradient(a, dy, dx)
slope = np.arctan(2.2 * np.hypot(gx, gy))         # esagerazione verticale 2.2
aspect = np.arctan2(-gx, gy)
az, alt = math.radians(315), math.radians(45)     # luce da nord-ovest, 45° di altezza
hs = np.clip(np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect), 0, 1)
shade = np.clip((np.sin(alt) - hs) / np.sin(alt), 0, 1)
alpha = Image.fromarray((shade ** 0.85 * 210).astype(np.uint8), 'L').resize((Wo, Ho), Image.LANCZOS)
alpha = alpha.point(lambda v: (v // 8) * 8)       # 32 livelli: file molto più leggero
out = Image.new('RGBA', (Wo, Ho), (0, 0, 0, 0)); out.putalpha(alpha)
out.quantize(colors=32, method=Image.Quantize.FASTOCTREE).save(os.path.join(DEST, 'relief.png'), optimize=True)
print(f'Scritto {SLUG}/map/relief.png', Wo, Ho)

# Strato delle quote alte (sopra i 1900 m circa), usato per la tinta verde-grigia delle montagne
from PIL import ImageFilter
e = np.asarray(Image.fromarray(z, 'F').resize((Wo // 2, Ho // 2), Image.BILINEAR))
hi = np.clip((e - 1900) / 900, 0, 1) ** 0.9
q = Image.fromarray((hi * 255).astype(np.uint8), 'L').filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: (v // 16) * 16)
qo = Image.new('RGBA', q.size, (0, 0, 0, 0)); qo.putalpha(q)
qo.quantize(colors=16, method=Image.Quantize.FASTOCTREE).save(os.path.join(DEST, 'elevation.png'), optimize=True)
print(f'Scritto {SLUG}/map/elevation.png')
