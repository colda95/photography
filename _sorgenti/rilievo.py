"""Calcola l'ombreggiatura del rilievo per la mappa a partire da un modello del terreno SRTM (GeoTIFF).
Uso:  python3 _sorgenti/rilievo.py percorso/del/file.tif
Serve:  pip3 install numpy pillow tifffile imagecodecs
Il GeoTIFF deve coprire esattamente l'area della mappa (lon -116.1 / -108.15, lat 34.95 / 39.15)."""
import math, os, sys
import numpy as np, tifffile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mappa import LON0, LON1, LAT0, LAT1, K, CL

z = tifffile.imread(sys.argv[1]).astype(np.float32)
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
out.quantize(colors=32, method=Image.Quantize.FASTOCTREE).save(os.path.join(os.path.dirname(HERE), 'assets', 'rilievo-usa.png'), optimize=True)
print('Scritto assets/rilievo-usa.png', Wo, Ho)
