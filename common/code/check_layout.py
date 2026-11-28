"""Controllo automatico dell'impaginazione: apre ogni pagina del sito a varie larghezze di schermo
(iPhone, tablet, portatile, schermo grande) e segnala tutto ciò che esce dai bordi della pagina e i testi che non partono dalla stessa linea a sinistra.

Uso, dalla cartella principale del sito:  python3 common/code/check_layout.py
Serve una volta sola:  pip3 install playwright && python3 -m playwright install chromium
Esce con un errore se trova problemi, così si può usare prima di ogni pubblicazione."""
import asyncio, glob, http.server, os, sys, threading
from functools import partial

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCREENS = [('iPhone verticale', 390, 844, True), ('iPhone orizzontale', 844, 390, True), ('tablet verticale', 768, 1024, True),
           ('portatile', 1280, 800, False), ('schermo grande', 1920, 1080, False)]
JS = """() => {
  const W = document.documentElement.clientWidth, out = [];
  const clipped = el => { for (let p = el.parentElement; p; p = p.parentElement) {
      const o = getComputedStyle(p).overflowX; if (['hidden', 'clip', 'auto', 'scroll'].includes(o)) return p !== document.body && p !== document.documentElement; } return false; };   // dentro un riquadro che taglia o scorre di lato (es. la mappa del mondo su telefono): va bene, il riquadro stesso viene controllato
  for (const el of document.querySelectorAll('body *')) {
    if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') continue;
    const r = el.getBoundingClientRect();
    if (!r.width || getComputedStyle(el).position === 'fixed' && el.closest('.lb')) continue;
    if ((r.right > W + 1 || r.left < -1) && !clipped(el))
      out.push(`${el.tagName.toLowerCase()}${el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\\s+/).join('.') : ''} (${Math.round(r.left)}…${Math.round(r.right)} su ${W})`);
  }
  // allineamento: titoli e testi descrittivi devono partire tutti dalla stessa linea a sinistra
  const lefts = {};
  for (const el of document.querySelectorAll('.sec-head, .statement p, .lede, .ch-head, .map-head, .colophon h2, .albums')) {
    const l = Math.round(el.getBoundingClientRect().left); (lefts[l] = lefts[l] || []).push(el.className || el.tagName.toLowerCase());
  }
  const keys = Object.keys(lefts);
  if (keys.length > 1) out.push('testi non allineati: ' + keys.map(k => k + 'px ← ' + [...new Set(lefts[k])].join(', ')).join(' | '));
  return {scroll: document.documentElement.scrollWidth - W, items: out.slice(0, 8), total: out.length};
}"""


async def main(base, pages, executable=None):
    from playwright.async_api import async_playwright
    problems = 0
    async with async_playwright() as p:
        b = await p.chromium.launch(**({'executable_path': executable} if executable else {}))
        for name, w, h, mobile in SCREENS:
            ctx = await b.new_context(viewport={'width': w, 'height': h}, is_mobile=mobile, has_touch=mobile, reduced_motion='reduce')
            pg = await ctx.new_page()
            for page in pages:
                await pg.goto(base + page, wait_until='load')
                await pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager')")
                await pg.wait_for_timeout(800)
                res = await pg.evaluate(JS)
                if res['scroll'] > 1 or res['total']:
                    problems += 1
                    print(f'✗ {page} · {name} ({w}×{h}): la pagina sborda di {res["scroll"]} px, {res["total"]} elementi fuori dai bordi')
                    for it in res['items']: print('    ', it)
                else:
                    print(f'✓ {page} · {name}')
            await ctx.close()
        await b.close()
    return problems


if __name__ == '__main__':
    pages = sorted(p for p in glob.glob('**/index.html', root_dir=ROOT, recursive=True) if not p.startswith(('common/', '.')))
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = partial(Quiet, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    n = asyncio.run(main(f'http://127.0.0.1:{srv.server_address[1]}/', pages, os.environ.get('CHROME')))
    srv.shutdown()
    print('\nNessun problema di impaginazione.' if not n else f'\n{n} problemi di impaginazione da correggere.')
    sys.exit(1 if n else 0)
