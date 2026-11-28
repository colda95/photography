"""Versioni leggere delle foto per il web.

L'unico originale di ogni foto è il JPEG da 2880 px (per gli album: <album>/photos/<capitolo>/).
Da lì la build ricava da sola una serie di copie in più larghezze, nella cartella web/ accanto
(per gli album: <album>/photos/web/<nome>-<larghezza>.jpg). Il browser sceglie la più piccola che
basta per lo schermo.

Qualità prima di tutto: la copia più grande è l'originale identico, byte per byte (nessuna ricompressione);
le più piccole sono JPEG ad alta qualità con il colore a piena risoluzione (4:4:4) e una nitidezza leggera
dopo il ridimensionamento, come l'"output sharpening" di Lightroom. (Il WebP a parità di peso spiana la grana
e i dettagli fini: per delle fotografie non va bene.)

Le copie si rifanno solo se mancano o se l'originale è più recente; quelle che non servono più
(foto tolte o rinominate) vengono cancellate."""
import os, shutil
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageFilter, ImageOps

WIDTHS = (1600, 2880)                     # larghezze generate (mai più grandi dell'originale)
QUALITY = 90                             # qualità JPEG delle copie ridotte


def web_dir(src):
    """Cartella delle copie: <album>/photos/<capitolo>/x.jpg -> <album>/photos/web/; home/photos/x.jpg -> home/photos/web/."""
    d = os.path.dirname(src)
    return os.path.join(os.path.dirname(d) if os.path.basename(os.path.dirname(d)) == 'photos' else d, 'web')


def plan(src):
    """Le copie previste per un originale: [(larghezza, percorso)]. Legge solo le dimensioni, non la foto."""
    with Image.open(src) as im:
        w, h = im.size
        if im.getexif().get(0x0112, 1) in (5, 6, 7, 8):     # foto ruotata dai dati EXIF
            w, h = h, w
    widths = sorted({x for x in WIDTHS if x < w} | {min(w, WIDTHS[-1])})
    stem = os.path.splitext(os.path.basename(src))[0]
    return [(x, os.path.join(web_dir(src), f'{stem}-{x}.jpg')) for x in widths]


def _make(src):
    todo = [(w, p) for w, p in plan(src) if not os.path.exists(p) or os.path.getmtime(p) < os.path.getmtime(src)]
    if not todo:
        return 0
    os.makedirs(web_dir(src), exist_ok=True)
    with Image.open(src) as im:
        icc = im.info.get('icc_profile')          # profilo colore dell'originale: i colori restano quelli di Lightroom
        exif_rotated = im.getexif().get(0x0112, 1) != 1
        full = ImageOps.exif_transpose(im).convert('RGB')
        for w, p in todo:
            if w == full.width and not exif_rotated:
                shutil.copyfile(src, p + '.tmp')  # misura piena: l'originale identico
            else:
                out = full if w == full.width else full.resize((w, round(full.height * w / full.width)), Image.LANCZOS)
                if w != full.width:
                    out = out.filter(ImageFilter.UnsharpMask(radius=0.6, percent=45, threshold=1))
                out.save(p + '.tmp', 'JPEG', quality=QUALITY, subsampling=0, optimize=True, progressive=True, icc_profile=icc)
            os.replace(p + '.tmp', p)
    return len(todo)


def build(sources, root):
    """Prepara le copie di tutte le foto (percorsi relativi a root). Restituisce {originale: [(larghezza, copia)]}."""
    srcs = sorted(set(sources))
    with ProcessPoolExecutor() as ex:
        made = sum(ex.map(_make, [os.path.join(root, s) for s in srcs]))
    result = {s: [(w, os.path.relpath(p, root).replace(os.sep, '/')) for w, p in plan(os.path.join(root, s))] for s in srcs}
    # pulizia: nelle cartelle web/ resta solo quello che serve
    keep = {os.path.join(root, p) for v in result.values() for _, p in v}
    stale = 0
    for d in {web_dir(os.path.join(root, s)) for s in srcs}:
        for f in os.listdir(d):
            p = os.path.join(d, f)
            if p not in keep and os.path.isfile(p):
                try:
                    os.remove(p); stale += 1
                except OSError as e:
                    print(f'  non riesco a cancellare {os.path.relpath(p, root)}: {e}')
    print(f'foto per il web: {sum(len(v) for v in result.values())} copie' + (f', {made} nuove' if made else '') + (f', {stale} vecchie tolte' if stale else ''))
    return result
