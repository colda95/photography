# Sorgenti del sito

Questa cartella contiene gli script che generano le pagine del sito. Non viene pubblicata come pagina: serve solo per rigenerare `index.html` e `usa-2026/index.html`.

## File

- `content_usa.py` — struttura dell'album: capitoli, ordine delle foto, impaginazione (foto larga, coppie, affiancate) e testi di partenza.
- `testi_utente.json` — i testi attuali (didascalie, introduzioni, titoli), comprese tutte le correzioni fatte a mano. Hanno la precedenza su `content_usa.py`.
- `importa_testi.py` — rilegge i testi da `usa-2026/index.html` e aggiorna `testi_utente.json`.
- `build_site.py` — rigenera le due pagine HTML.
- `mappa.py` e `mappa_dati.json` — disegnano la mappa del percorso. Fiumi, laghi, confini e vette vengono da Natural Earth (pubblico dominio); il rilievo ombreggiato è in `assets/rilievo-usa.png`, ricavato dal Natural Earth Shaded Relief.

## Come si usa

Serve Python 3 con Pillow (`pip3 install Pillow`). Dalla cartella principale del repository:

```
python3 _sorgenti/importa_testi.py   # solo se hai corretto testi direttamente nell'HTML
python3 _sorgenti/build_site.py
```

## Regole da ricordare

- Ogni foto deve esistere in **entrambe** le cartelle: `USA-2026-places-web-2048` (pagina) e `USA-2026-places-web-2880` (schermo intero). Se ne togli una, toglila da tutte e due e toglila anche da `content_usa.py`.
- `assets/style.css` e `assets/album.js` sono i file di stile e comportamento: la pagina li richiama con un numero di versione calcolato dal loro contenuto, quindi dopo averli modificati bisogna rigenerare le pagine.
- `LICENSE`, `README.md` e `.gitignore` si mantengono a mano.
