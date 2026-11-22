# Come è fatto il sito

## Struttura

```
index.html                  home (deve stare qui: è la pagina d'ingresso del sito)
home/
  photos/landscape.jpg      foto di copertina della home su computer (orizzontale, 2880 px)
  photos/portrait.jpg       foto di copertina della home su telefono (verticale, 2880 px)
  photos/web/               copie leggere generate dalla build (non toccare)
  texts/it.json, en.json    testi della home
usa-2026/                   un album: tutto quello che lo riguarda sta qui
  index.html                pagina dell'album
  photos/2880/              foto originali, JPEG da 2880 px (da qui si leggono anche i dati di scatto); solo sul Mac, non su GitHub
  photos/web/               copie in più misure, generate dalla build (non toccare)
  texts/it.json, en.json    titolo, date, introduzioni, didascalie, testi della mappa
  structure.json            capitoli, ordine e impaginazione delle foto
  map/                      facoltativa: route.json (area, tappe, percorso, etichette),
                            geodata.json (fiumi, laghi, confini), relief.png, elevation.png, modello del terreno .tif
common/
  style.css                 stile di tutte le pagine (colori, testi, animazioni)
  site.js                   animazioni e barra di navigazione, su tutte le pagine
  album.js                  foto a schermo intero negli album
  og-red-earth.jpg          immagine mostrata quando si condivide un link del sito
  config.json               autore, indirizzo, email, GitHub, lingue, elenco degli album, foto di copertina della home, obiettivi
  texts/it.json, en.json    testi comuni: menu, pulsanti, colophon, piè di pagina
  code/                     i programmi che generano le pagine
```

Le pagine `index.html` sono generate: non si modificano a mano (se lo fai, vedi `import_texts.py` sotto).

## Aggiungere un album

1. Crea una cartella con un nome breve senza spazi, che sarà anche l'indirizzo: per esempio `islanda-2027/`.
2. Esporta le foto da Lightroom in JPEG da 2880 px sul lato lungo e mettile in `islanda-2027/photos/2880/`. Le versioni leggere per il web le crea la build.
3. Copia `usa-2026/structure.json` e adattalo: foto d'apertura dell'album (`hero`), foto d'anteprima nella home (`preview`, meglio diversa da `hero`), anno, software, capitoli con le foto.
   Blocchi: `["full", foto]`, `["wide", foto]`, `["group", [foto, foto, …]]`, `["offset", principale, laterale, invertito]`.
4. Copia `usa-2026/texts/it.json` ed `en.json` e scrivi titolo, date, introduzioni e didascalie (una per foto, con il nome del file come chiave).
5. Aggiungi `"islanda-2027"` in `albums` dentro `common/config.json`: l'ordine è quello della home.
6. Mappa (facoltativa): `python3 common/code/make_map.py islanda-2027`. Ricava le tappe dalle coordinate GPS delle foto di ogni capitolo, calcola l'area, scarica fiumi, laghi, confini e nomi delle regioni da Natural Earth e sistema le etichette perché non si accavallino. Poi si può rifinire a mano `map/route.json` (punti intermedi del percorso, posizione delle etichette, nomi di fiumi e montagne) e i testi della mappa negli `texts/*.json`. Per il rilievo serve il modello del terreno: lo script spiega come scaricarlo. Senza cartella `map/` la pagina esce senza mappa.
7. Rigenera.

## Testi e lingue

- Il sito è in inglese, che è l'unica lingua in `languages` dentro `common/config.json`. I titoli degli album possono restare in italiano: si scrivono come preferisci in `<album>/texts/en.json`.
- Per correggere un testo, modifica il JSON e rigenera. Le didascalie sono legate al nome della foto, i capitoli al loro numero.
- I testi italiani (`texts/it.json` in `common/`, `home/` e negli album) restano conservati ma non vengono usati. Per riattivare l'italiano, aggiungi `"it"` in `languages`: la prima lingua dell'elenco sta nella radice del sito, le altre in una sottocartella, e compaiono il selettore di lingua e il passaggio automatico in base al browser.
- Email in Contatti: scrivila in `email` dentro `common/config.json` (vuota = non mostrata).

## Animazioni

Tutte le animazioni usano la stessa curva e le stesse durate, definite in cima a `common/style.css` (`--ease`, `--t-in`, `--t-hover`, `--rise`): cambiandole lì cambiano su tutto il sito. Chi ha attivato "Riduci movimento" sul proprio dispositivo vede le pagine ferme.

## Comandi

Serve Python 3 con Pillow (`pip3 install Pillow`). Dalla cartella principale del sito:

```
python3 common/code/build_site.py                  # rigenera tutte le pagine
python3 -m http.server 8000                          # anteprima su http://localhost:8000
python3 common/code/import_texts.py usa-2026      # solo se hai corretto a mano l'HTML dell'album
python3 common/code/make_map.py usa-2026 --force   # rifà da zero la mappa dell'album (perde le rifiniture a mano)
python3 common/code/relief.py usa-2026            # ricalcola il rilievo della mappa (pip3 install numpy tifffile imagecodecs)
```

## Controllo dell'impaginazione

Prima di pubblicare: `python3 common/code/check_layout.py`. Apre ogni pagina come la vedrebbero un iPhone (verticale e orizzontale), un tablet, un portatile e uno schermo grande, e segnala qualunque elemento esca dai bordi o testo non allineato agli altri. Serve una volta sola: `pip3 install playwright && python3 -m playwright install chromium`.

Le regole che tengono l'impaginazione robusta stanno in `common/style.css`: tutte le pagine usano la stessa colonna, gli stessi stili per titoli e testi (sempre allineati a sinistra, su tutta la larghezza), e nessun elemento dentro la pagina può diventare più largo dello spazio disponibile.

## Regole da ricordare

- Ogni foto usata deve esistere in `photos/2880`: la build controlla e si ferma se ne manca una, e segnala le foto presenti ma non usate.
- Foto leggere: per ogni originale la build crea in `photos/web/` copie larghe 1600 e 2880 px (`common/code/images.py`): la 2880 è l'originale identico, le altre sono JPEG ad alta qualità (90, colore 4:4:4) con una nitidezza leggera dopo il ridimensionamento. Niente WebP: a parità di peso spiana la grana delle foto. Ogni pagina lascia scegliere al browser la più piccola che basta per lo schermo; a schermo intero si apre la più grande. Le copie si rifanno solo se l'originale cambia, e quelle che non servono più vengono cancellate. Vanno pubblicate su GitHub insieme al resto.
- Le foto originali (`*/photos/2880/` e le copertine `home/photos/*.jpg`) restano solo sul Mac: sono escluse da GitHub (`.gitignore`), dove vanno solo le copie in `photos/web/`. Servono per rigenerare il sito, quindi tienine una copia di sicurezza (Time Machine, disco esterno o cloud).
- Dopo aver modificato `style.css` o `album.js`, rigenera: le pagine li richiamano con un numero di versione calcolato dal loro contenuto.
- Mappe: fiumi, laghi e confini da Natural Earth (pubblico dominio); rilievo dal modello del terreno NASA SRTM a 90 m (da OpenTopography). I file `.tif` restano fuori da GitHub (`.gitignore`).
