"""Versioni leggere delle foto per il web.

L'unico originale di ogni foto è il JPEG da 2880 px (per gli album: <album>/photos/2880/).
Da lì la build ricava da sola una serie di copie WebP in più larghezze, nella cartella web/ accanto
(per gli album: <album>/photos/web/<nome>-<larghezza>.webp). Il browser sceglie la più piccola che
basta per lo schermo: un telefono scarica circa un quarto di quello che scaricherebbe con le foto grandi.

Le copie si rifanno solo se mancano o se l'originale è più recente; quelle che non servono più
(foto tolte o rinominate) vengono cancellate."""
import os
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageOps

WIDTHS = (800, 1200, 1600, 2880)         # larghezze generate (mai più grandi dell'originale)
QUALITY = 80                             # qualità WebP: a occhio identica al JPEG, peso circa un terzo


def web_dir(src):
    """Cartella delle copie: <album>/photos/2880/x.jpg -> <album>/photos/web/; home/photos/x.jpg -> home/photos/web/."""
    d = os.path.dirname(src)
    return os.path.join(os.path.dirname(d) if os.path.basename(d).isdigit() else d, 'web')


def plan(src):
    """Le copie previste per un originale: [(larghezza, percorso)]. Legge solo le dimensioni, non la foto."""
    with Image.open(src) as im:
        w, h = im.size
        if im.getexif().get(0x0112, 1) in (5, 6, 7, 8):     # foto ruotata dai dati EXIF
            w, h = h, w
    widths = sorted({x for x in WIDTHS if x < w} | {min(w, WIDTHS[-1])})
    stem = os.path.splitext(os.path.basename(src))[0]
    return [(x, os.path.join(web_dir(src), f'{stem}-{x}.webp')) for x in widths]


def _make(src):
    todo = [(w, p) for w, p in plan(src) if not os.path.exists(p) or os.path.getmtime(p) < os.path.getmtime(src)]
    if not todo:
        return 0
    os.makedirs(web_dir(src), exist_ok=True)
    with Image.open(src) as im:
        icc = im.info.get('icc_profile')          # profilo colore dell'originale: i colori restano quelli di Lightroom
        im = ImageOps.exif_transpose(im).convert('RGB')
        for w, p in todo:
            h = round(im.height * w / im.width)
            out = im if w == im.width else im.resize((w, h), Image.LANCZOS)
            out.save(p + '.tmp', 'WEBP', quality=QUALITY, method=5, icc_profile=icc)
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
