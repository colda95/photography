"""Rilegge i testi dalla pagina pubblicata di un album e li salva in album/<album>/texts/<lingua>.json.
Serve solo se hai corretto dei testi direttamente nell'HTML: lancialo PRIMA di build_site.py,
così la rigenerazione non perde le correzioni.

Uso:  python3 common/code/import_texts.py usa-2026        (lingua principale: album/usa-2026/index.html)
      python3 common/code/import_texts.py usa-2026 en     (inglese: album/usa-2026/en/index.html)

Importa titolo, sommario, descrizione, titoli e introduzioni dei capitoli, didascalie e note in fondo.
I testi comuni (menu, pulsanti, colophon) vanno corretti in common/texts/<lingua>.json."""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.dirname(HERE)
ROOT = os.path.dirname(COMMON)
CONFIG = json.load(open(os.path.join(COMMON, 'config.json'), encoding='utf-8'))
NAME = sys.argv[1].split('/')[-1]                     # nome dell'album (la cartella in album/)
SLUG = f'album/{NAME}'
LANG = sys.argv[2] if len(sys.argv) > 2 else CONFIG['languages'][0]
assert NAME in CONFIG['albums'], f'Album sconosciuto: {NAME}'
assert LANG in CONFIG['languages'], f'Lingua sconosciuta: {LANG}'
PAGE = os.path.join(ROOT, SLUG, *([] if LANG == CONFIG['languages'][0] else [LANG]), 'index.html')
T = os.path.join(ROOT, SLUG, 'texts', f'{LANG}.json')

s = open(PAGE, encoding='utf-8').read()
u = lambda x: html.unescape(re.sub(r'<[^>]+>', '', x)).strip()
j = json.load(open(T, encoding='utf-8'))

for fig in re.findall(r'<figure class="fig.*?</figure>', s, re.S):
    name = re.search(r'/([^/"]+)\.jpg"', fig).group(1)
    c = re.search(r'<p class="cap"><strong>(.*?)</strong>\s?(.*?)</p>', fig, re.S)
    j['captions'][name] = [u(c.group(1)), u(c.group(2))]
for k, sec in re.findall(r'<section class="ch" id="chapter-(\d+)">(.*?)</section>', s, re.S):
    ch = j['chapters'].setdefault(k, {})              # i capitoli hanno lo stesso numero della loro cartella
    ch['title'] = u(re.search(r'<h2>(.*?)</h2>', sec, re.S).group(1))
    ch['intro'] = u(re.search(r'<p class="intro">(.*?)</p>', sec, re.S).group(1))
j['title'] = u(re.search(r'<header class="cover">.*?<h1>(.*?)</h1>', s, re.S).group(1))
j['lede'] = u(re.search(r'<p class="lede">(.*?)</p>', s, re.S).group(1))
j['meta_description'] = u(re.search(r'<meta name="description" content="(.*?)">', s).group(1))
foot = re.search(r'<footer class="colophon">(.*?)</footer>', s, re.S).group(1)
j['footer_copy'] = [u(x) for x in re.findall(r'<p class="copy">(.*?)</p>', foot, re.S) if 'backlink' not in x]

json.dump(j, open(T, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'Testi importati in {SLUG}/texts/{LANG}.json: {len(j["captions"])} didascalie, {len(j["chapters"])} capitoli.')
