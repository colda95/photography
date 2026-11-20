# Sorgenti del sito

Questa cartella contiene gli script che generano le pagine del sito. Non viene pubblicata come pagina: serve solo per rigenerare `index.html` e `usa-2026/index.html`.

## File

- `content_usa.py` — struttura dell'album: capitoli, ordine delle foto, impaginazione (foto larga, coppie, affiancate) e testi di partenza.
- `testi_utente.json` — i testi attuali (didascalie, introduzioni, titoli), comprese tutte le correzioni fatte a mano. Hanno la precedenza su `content_usa.py`.
- `testi_en.json` — la versione inglese degli stessi testi (stesse chiavi, stessi nomi di foto), più titolo dell'album, date dei capitoli e testi alternativi delle immagini. Quando cambi un testo italiano, aggiorna anche quello inglese: se una didascalia manca, la build lo segnala e usa l'italiano.
- `importa_testi.py` — rilegge i testi da `usa-2026/index.html` e aggiorna `testi_utente.json`. Con `en` (`python3 _sorgenti/importa_testi.py en`) fa lo stesso per `en/usa-2026/index.html` e `testi_en.json`.
- `temi.py` — i temi della home (Paesaggi, Animali, Strada, Alba e tramonto): nome e descrizione nelle due lingue, foto di copertina ed elenco delle foto. Ogni tema diventa una pagina in `temi/<nome>/`. Le foto devono essere già in un album: didascalie e testi vengono da lì.
- `build_site.py` — rigenera le pagine HTML in tutte e due le lingue. I testi fissi (home, menu, pulsanti, colophon, altri progetti) sono nel dizionario `UI` all'inizio del file; lì ci sono anche `EMAIL` (indirizzo mostrato in Contatti), `GITHUB` e `HOME_IMAGE` (la foto grande in cima alla home).

## Lingue

- Italiano: `index.html` e `usa-2026/`. Inglese: `en/index.html` e `en/usa-2026/`. Le foto e gli `assets` sono in comune.
- In alto a destra c'è il selettore IT / EN; la scelta resta salvata nel browser del visitatore.
- Chi apre una pagina italiana senza aver mai scelto e con un browser che non ha l'italiano tra le lingue preferite viene portato alla versione inglese. I motori di ricerca non vengono reindirizzati: trovano le due versioni tramite i link `hreflang`.
- `mappa.py` e `mappa_dati.json` — disegnano la mappa del percorso. Fiumi, laghi, confini e vette vengono da Natural Earth (pubblico dominio); il rilievo ombreggiato è in `assets/rilievo-usa.png`, calcolato con `rilievo.py` dal modello del terreno NASA SRTM a 90 m (scaricato da OpenTopography; il file .tif non va messo su GitHub, è escluso dal `.gitignore`).

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
