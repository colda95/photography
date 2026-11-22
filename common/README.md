# Come è fatto il sito

## Struttura

```
index.html                  home in italiano (deve stare qui: è la pagina d'ingresso del sito)
home/
  en/index.html             home in inglese
  photos/landscape.jpg      foto di copertina della home su computer (orizzontale)
  photos/portrait.jpg       foto di copertina della home su telefono (verticale)
  texts/it.json, en.json    testi della home
usa-2026/                   un album: tutto quello che lo riguarda sta qui
  index.html                album in italiano
  en/index.html             album in inglese
  photos/2048/              foto mostrate nella pagina
  photos/2880/              foto a schermo intero (da qui si leggono anche i dati di scatto)
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
2. Metti le foto in `islanda-2027/photos/2048/` e `islanda-2027/photos/2880/`, con gli stessi nomi di file in entrambe.
3. Copia `usa-2026/structure.json` e adattalo: foto d'apertura dell'album (`hero`), foto d'anteprima nella home (`preview`, meglio diversa da `hero`), anno, software, capitoli con le foto.
   Blocchi: `["full", foto]`, `["wide", foto]`, `["group", [foto, foto, …]]`, `["offset", principale, laterale, invertito]`.
4. Copia `usa-2026/texts/it.json` ed `en.json` e scrivi titolo, date, introduzioni e didascalie (una per foto, con il nome del file come chiave).
5. Aggiungi `"islanda-2027"` in `albums` dentro `common/config.json`: l'ordine è quello della home.
6. Mappa (facoltativa): `python3 common/code/make_map.py islanda-2027`. Ricava le tappe dalle coordinate GPS delle foto di ogni capitolo, calcola l'area, scarica fiumi, laghi, confini e nomi delle regioni da Natural Earth e sistema le etichette perché non si accavallino. Poi si può rifinire a mano `map/route.json` (punti intermedi del percorso, posizione delle etichette, nomi di fiumi e montagne) e i testi della mappa negli `texts/*.json`. Per il rilievo serve il modello del terreno: lo script spiega come scaricarlo. Senza cartella `map/` la pagina esce senza mappa.
7. Rigenera.

## Testi e lingue

- Per correggere un testo, modifica il JSON della lingua giusta e rigenera. Le chiavi sono uguali in tutte le lingue.
- Se in una lingua manca un testo, la build lo segnala e usa quello italiano.
- Per aggiungere una lingua, aggiungi `<codice>.json` in `common/texts/`, `home/texts/` e nei `texts/` di ogni album, poi il codice in `languages` dentro `common/config.json`.
- Chi apre una pagina italiana con un browser che non ha l'italiano tra le lingue preferite viene portato all'inglese; la scelta fatta con il selettore IT / EN resta salvata nel browser.
- Foto di copertina della home: sostituisci `home/photos/landscape.jpg` (computer) e `home/photos/portrait.jpg` (telefono) con le tue, tenendo gli stessi nomi; oppure cambia i percorsi in `home_cover` dentro `common/config.json`. Conviene usare foto con cielo o spazio tranquillo in alto, dove sta il nome.
- Email in Contatti: scrivila in `email` dentro `common/config.json` (vuota = non mostrata).

## Animazioni

Tutte le animazioni usano la stessa curva e le stesse durate, definite in cima a `common/style.css` (`--ease`, `--t-in`, `--t-hover`, `--rise`): cambiandole lì cambiano su tutto il sito. Chi ha attivato "Riduci movimento" sul proprio dispositivo vede le pagine ferme.

## Comandi

Serve Python 3 con Pillow (`pip3 install Pillow`). Dalla cartella principale del sito:

```
python3 common/code/build_site.py                  # rigenera tutte le pagine
python3 -m http.server 8000                          # anteprima su http://localhost:8000
python3 common/code/import_texts.py usa-2026      # solo se hai corretto a mano l'HTML italiano dell'album
python3 common/code/import_texts.py usa-2026 en   # idem per l'HTML inglese
python3 common/code/make_map.py usa-2026 --force   # rifà da zero la mappa dell'album (perde le rifiniture a mano)
python3 common/code/relief.py usa-2026            # ricalcola il rilievo della mappa (pip3 install numpy tifffile imagecodecs)
```

## Regole da ricordare

- Ogni foto usata deve esistere in `photos/2048` e in `photos/2880`: la build controlla e si ferma se ne manca una, e segnala le foto presenti ma non usate.
- Dopo aver modificato `style.css` o `album.js`, rigenera: le pagine li richiamano con un numero di versione calcolato dal loro contenuto.
- Mappe: fiumi, laghi e confini da Natural Earth (pubblico dominio); rilievo dal modello del terreno NASA SRTM a 90 m (da OpenTopography). I file `.tif` restano fuori da GitHub (`.gitignore`).
