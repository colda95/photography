"""Legge i testi dalla pagina pubblicata (usa-2026/index.html) e li salva in testi_utente.json.
Da lanciare PRIMA di build_site.py se hai corretto i testi direttamente nell'HTML,
così la rigenerazione non li perde.  Uso:  python3 _sorgenti/importa_testi.py
Per la versione inglese (en/usa-2026/index.html -> testi_en.json):  python3 _sorgenti/importa_testi.py en"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
EN = len(sys.argv) > 1 and sys.argv[1] == 'en'
PAGE = os.path.join(os.path.dirname(HERE), *(['en'] if EN else []), 'usa-2026', 'index.html')
T = os.path.join(HERE, 'testi_en.json' if EN else 'testi_utente.json')

s = open(PAGE, encoding='utf-8').read()
u = lambda x: html.unescape(re.sub(r'<[^>]+>', '', x)).strip()
j = json.load(open(T, encoding='utf-8')) if os.path.exists(T) else {}

caps = {}
for fig in re.findall(r'<figure class="fig.*?</figure>', s, re.S):
    name = re.search(r'/([^/"]+)\.jpg"', fig).group(1)
    c = re.search(r'<p class="cap"><strong>(.*?)</strong>\s?(.*?)</p>', fig, re.S)
    caps[name] = [u(c.group(1)), u(c.group(2))]
j['captions'] = caps
j['intros'] = [u(x) for x in re.findall(r'<p class="intro">(.*?)</p>', s, re.S)]
j['lede'] = u(re.search(r'<p class="lede">(.*?)</p>', s, re.S).group(1))
j['meta_description'] = u(re.search(r'<meta name="description" content="(.*?)">', s).group(1))
nums = re.findall(r'<section class="ch" id="cap-([a-z]+)">', s)
titles = re.findall(r'<section class="ch".*?<h2>(.*?)</h2>', s, re.S)
j['chapter_titles'] = {n.upper(): u(t) for n, t in zip(nums, titles)}
j['route_titles'] = {n.upper(): u(t) for n, t in re.findall(r'<a href="#cap-([a-z]+)"><span class="d">.*?</span><span class="p">(.*?)</span>', s)}
foot = re.search(r'<footer class="colophon">(.*?)</footer>', s, re.S).group(1)
j['footer_copy'] = [u(x) for x in re.findall(r'<p class="copy">(.*?)</p>', foot, re.S) if 'backlink' not in x]
json.dump(j, open(T, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'Testi importati: {len(caps)} didascalie, {len(j["intros"])} introduzioni.')
