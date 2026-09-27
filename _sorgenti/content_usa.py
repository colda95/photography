# Contenuti dell'album "Terra rossa" (USA 2026).
# Blocchi: ('full', foto) · ('wide', foto) · ('group', [foto, ...]) · ('offset', principale, laterale, invertito)
# Foto: (file, titolo, didascalia[, opzioni])

ALBUM = dict(
    slug='usa-2026',
    title='Terra rossa',
    kicker=('Arizona, Utah e Nevada', '5–11 aprile 2026'),
    hero='20260407-3W9A7364-HDR',
    cover='20260409-3W9A7813-HDR',
    lede='Sette giorni nel Sud-Ovest americano, dalla Route 66 all’insegna di Las Vegas. Arenaria, strade dritte, animali al pascolo e molte sveglie prima dell’alba.',
    year=2026,
)

CHAPTERS = [
dict(num='I', date='5 aprile 2026', title='Route 66 e Grand Canyon',
 coords='36.0577° N · 112.1389° W · South Rim',
 intro='Si parte dalla Route 66, immancabile, e nel pomeriggio si arriva sul bordo sud del Grand Canyon. Dal parapetto il canyon non ha misura: solo gli strati di roccia danno un ordine al paesaggio. Il primo wow del viaggio arriva lì.',
 blocks=[
  ('full', ('20260405-3W9A6381', 'Il primo sguardo.', 'A metà pomeriggio la luce è dura e il canyon si legge per piani: le terrazze in primo piano, le pareti rosse, il bordo nord che sfuma nella foschia.')),
  ('wide', ('20260405-3W9A6401', 'Stratificazioni.', 'A 105 mm il canyon si comprime: pareti, terrazze e gole diventano un unico disegno di linee orizzontali.')),
  ('offset', ('20260405-3W9A6475', 'Tempo in orizzontale.', 'Gli strati visibili dal bordo raccontano quasi due miliardi di anni di storia geologica, sovrapposti come le pagine di un libro.'),
             ('20260405-3W9A6419', 'Precedenza ai muli.', 'All’inizio del sentiero un cartello ricorda chi comanda: quando passano i muli, si seguono le istruzioni della guida.'), False),
  ('group', [
   ('20260405-3W9A6450', 'Vista con scoiattolo.', 'Uno scoiattolo delle rocce si mette in posa, foto subito.'),
   ('20260405-3W9A6512', 'Il residente.', 'Più intimo, lo sfondo si scioglie negli stessi colori del canyon.'),
   ('20260405-3W9A6473', 'La parete.', 'Il calcare in primo piano, e dietro il canyon che sbiadisce nella foschia.')]),
  ('full', ('20260405-3W9A6590-HDR', 'Primo tramonto.', 'Alle 18:34 il sole basso accende solo le cime delle terrazze. Un panorama stretto e lunghissimo, per tenere dentro tutta la luce.')),
 ]),

dict(num='II', date='6 aprile 2026', title='Antelope Canyon e Horseshoe Bend',
 coords='36.8617° N · 111.3743° W · Page, Arizona',
 intro='Due volti della stessa arenaria: sotto terra, nella fessura dell’Upper Antelope Canyon, e poi a picco sul fiume Colorado a Horseshoe Bend, fino all’ultimo temporale della sera.',
 blocks=[
  ('wide', ('20260406-3W9A6754-HDR', 'Dentro la roccia.', 'La luce entra da una fenditura in alto e rimbalza sulle pareti levigate dalle piene improvvise. Il colore cambia a ogni metro: arancio dove batte il sole, viola dove non arriva.')),
  ('group', [
   ('20260406-3W9A6720', 'Verso l’alto.', 'ISO 25600: laggiù la luce è poca, ma il grano è un prezzo giusto per queste curve.'),
   ('20260406-3W9A6794-HDR', 'Pareti a onde.', 'Le venature dell’arenaria sono dune pietrificate di un deserto di circa duecento milioni di anni fa.')]),
  ('group', [
   ('20260406-3W9A6814-HDR', 'Il fondo.', 'La sabbia sul fondo riflette la luce e schiarisce le pareti dal basso.'),
   ('20260406-3W9A6861-2', 'Nel fascio di luce.', 'Chi esplora si ferma nell’unico punto illuminato del canyon e alza lo sguardo. In bianco e nero restano solo la luce e la forma della roccia.', {'notime': True})]),
  ('full', ('20260406-3W9A6974-HDR', 'Horseshoe Bend.', 'Il Colorado disegna il suo ferro di cavallo circa trecento metri sotto il bordo. Il 16 mm fatica a contenere l’ansa intera, dalla parete in primo piano al fiume. In basso, canottieri navigano l’acqua')),
  ('group', [
   ('20260406-3W9A6981', 'A valle.', 'Oltre l’ansa il fiume riprende la sua strada verso Lees Ferry e il Grand Canyon, con una striscia verde sulle rive.'),
   ('20260406-3W9A7060', 'Temporale al tramonto.', 'Alle 18:54 il sole trova uno spiraglio sotto le nuvole e accende l’orizzonte per pochi istanti in una tempesta di fuoco.')]),
 ]),

dict(num='III', date='7 aprile 2026', title='Monument Valley',
 coords='36.9386° N · 110.0908° W · Navajo Nation',
 intro='La US-163 attraversa il confine tra Arizona e Utah e porta dentro il paesaggio dei film western: mandrie al pascolo, cavalli liberi e i grandi butte di arenaria rimasti in piedi dove tutto il resto è stato eroso. In serata, la strada più fotografata della valle.',
 blocks=[
  ('group', [
   ('20260407-3W9A7076', 'Benvenuti in Utah.', 'Sulla US-163 si passa il confine, e il cartello promette “Life Elevated”.'),
   ('20260407-3W9A7083', 'E ritorno in Arizona.', 'Per chi viaggia nel senso opposto, il benvenuto nello stato del Grand Canyon.')]),
  ('wide', ('20260407-3W9A7089', 'I butte.', 'Torri di arenaria piantate nella sabbia rossa, sotto un cielo senza una nuvola di troppo.')),
  ('wide', ('20260407-3W9A7127', 'Il ginepro secco.', 'Un tronco morto in primo piano e, dietro, una delle Mitten, la sagoma più riconoscibile della valle.')),
  ('wide', ('20260407-3W9A7145', 'Fioritura.', 'Ad aprile la sabbia si copre di fiori bianchi e viola, bassi e fitti. Un privilegio.')),
  ('full', ('20260407-3W9A7153', 'Pascolo con vista.', 'Mucche Hereford brucano tra la salvia; sullo sfondo la linea delle mesa corre per tutto l’orizzonte.')),
  ('group', [
   ('20260407-3W9A7154', 'Il cavallo chiaro.', 'Un cavallo bruca tra erba secca e fiori viola. Più in alto sul pendio, piccoli come puntini, pascolano gli altri.'),
   ('20260407-3W9A7168', 'Totem Pole.', 'La guglia sottile del Totem Pole con le rocce di Yei Bi Chei. In basso le mucche riposano accanto a un ginepro.')]),
  ('group', [
   ('20260407-3W9A7175', 'Totem Pole, da vicino.', 'A 105 mm le guglie si staccano dalla parete. La più sottile supera i cento metri di altezza.'),
   ('20260407-3W9A7183', 'Cornice di roccia.', 'Un albero solitario tra due pareti, con i butte in lontananza.')]),
  ('wide', ('20260407-3W9A7180', 'La valle aperta.', 'Il fondovalle a metà pomeriggio: sabbia, cespugli e un butte al centro della scena.')),
  ('offset', ('20260407-3W9A7364-HDR', 'Ultima luce.', 'Mezz’ora dopo, dalla stessa strada: la luce radente scalda l’erba e i butte diventano color lilla.'),
             ('20260407-3W9A7333-HDR', 'Forrest Gump Point.', 'Sulla US-163, il punto in cui Forrest smette di correre. La linea gialla guida lo sguardo fino ai butte.'), True),
 ]),

dict(num='IV', date='7–8 aprile 2026', title='Monticello',
 coords='37.8606° N · 109.3756° W · Canyonlands Domes',
 intro='Una notte in una cupola vicino a Monticello, sotto un cielo pieno di stelle, e un risveglio presto, con il teleobiettivo pronto per chi abita il bosco di ginepri.',
 blocks=[
  ('offset', ('20260408-3W9A7399', 'Alba.', 'Alle 6:58 la prima luce tocca solo la casa bianca, in mezzo a un mare di ginepri ancora in ombra.'),
             ('20260407-3W9A7388', 'Notte.', 'Alle 22:32, lontano dalle città, il cielo si riempie di stelle sopra i ginepri.'), True),
  ('wide', ('20260408-3W9A7575', 'Cervo mulo.', 'Nel primo mattino, tra i cespugli, un cervo mulo si ferma a guardare prima di sparire nel bosco.')),
 ]),

dict(num='V', date='8 aprile 2026', title='Arches',
 coords='38.7329° N · 109.5749° W · Arches National Park',
 intro='Oltre duemila archi di pietra censiti in un solo parco, e all’orizzonte le cime ancora innevate delle La Sal Mountains. In serata, la strada verso ovest.',
 blocks=[
  ('wide', ('20260408-3W9A7595', 'Park Avenue.', 'Le pareti di arenaria allineate come i grattacieli di un viale.')),
  ('group', [
   ('20260408-3W9A7600', 'Equilibri.', 'Una roccia sospesa su un collo sottile, contro il cielo blu.'),
   ('20260408-3W9A7608', 'Lucertola.', 'Immobile al sole, quasi dello stesso colore della pietra.')]),
  ('wide', ('20260408-3W9A7604', 'La piana.', 'Distese di arenaria chiara e, in fondo, le file di pinnacoli rossi.')),
  ('offset', ('20260408-3W9A7610', 'Balanced Rock e i La Sal.', 'Balanced Rock, a sinistra, con le cime innevate delle La Sal Mountains sullo sfondo.'),
             ('20260408-3W9A7622', 'Balanced Rock.', 'Il masso in cima pesa circa 3.500 tonnellate e sembra poggiato lì per caso.'), True),
  ('full', ('20260408-3W9A7624', 'Neve sul deserto.', 'Le La Sal Mountains, che sfiorano i 3.900 metri, sopra la linea delle rocce rosse.')),
  ('group', [
   ('20260408-3W9A7626', 'Pinnacoli.', 'Guglie e torri di roccia, con le montagne innevate appena visibili dietro.'),
   ('20260408-3W9A7627', 'Turret Arch.', 'La torre e il suo arco, nella zona delle Windows.')]),
  ('group', [
   ('20260408-3W9A7628', 'Sotto l’arco.', 'Un ponte di roccia visto da sotto, sospeso nel blu.'),
   ('20260408-3W9A7636', 'Le pinne.', 'Lastre verticali di arenaria, le “fin”, da cui nel tempo nascono gli archi.')]),
  ('wide', ('20260408-3W9A7647', 'Vista sul parco.', 'Dall’alto, il parco si apre in un mosaico di rocce chiare, rosse e cespugli.')),
  ('wide', ('20260408-3W9A7649', 'Delicate Arch.', 'Il simbolo dello Utah, piccolo sull’orizzonte di roccia liscia.')),
  ('group', [
   ('20260408-3W9A7651', 'Sagoma.', 'In viaggio verso Bryce, alle 19:37, un cervo si ferma sul crinale controluce.'),
   ('20260408-3W9A7660', 'Pini al tramonto.', 'Venti minuti dopo il cielo si incendia dietro una fila di pini.')]),
 ]),

dict(num='VI', date='9 aprile 2026', title='Bryce Canyon',
 coords='37.5928° N · 112.1869° W · Anfiteatro di Bryce',
 intro='Sveglia prima dell’alba per vedere il sole entrare nell’anfiteatro, poi a piedi lungo il bordo e in auto lungo la strada panoramica, fino alle finestre di roccia più a sud.',
 blocks=[
  ('full', ('20260409-3W9A7813-HDR', 'Anfiteatro.', 'Alle 7:07 il sole si alza sull’orizzonte e accende gli hoodoo, le guglie di roccia modellate dal gelo e dal disgelo. Tra le guglie resiste qualche chiazza di neve di aprile.')),
  ('group', [
   ('20260409-3W9A7816', 'Il sole sale.', 'Pochi secondi dopo, la luce entra più a fondo tra le guglie.'),
   ('20260409-3W9A7868', 'Panorama.', 'Tutto l’anfiteatro in un solo sguardo, alle 7:13.')]),
  ('wide', ('20260409-3W9A7892', 'Oltre il bordo.', 'A metà mattina, dal bordo si vedono gli altopiani fino all’orizzonte.')),
  ('wide', ('20260409-3W9A8120', 'Castello.', 'Un hoodoo isolato, con le guglie più piccole allineate dietro.')),
  ('wide', ('20260409-3W9A8134', 'Nuvole su Bryce.', 'A mezzogiorno le nuvole disegnano ombre sull’anfiteatro.')),
  ('full', ('20260409-3W9A8143', 'Una città di pietra.', 'Migliaia di hoodoo, fitti come le case di una città vista dall’alto.')),
  ('group', [
   ('20260409-3W9A8148', 'Finestre nella parete.', 'Più a sud, lungo la strada panoramica, le pareti si bucano in piccole grotte.'),
   ('20260409-3W9A8157', 'Natural Bridge.', 'Un arco scavato dalla pioggia e dal gelo, con il bosco che si vede attraverso.')]),
 ]),

dict(num='VII', date='9–10 aprile 2026', title='Zion Mountain Ranch',
 coords='37.2463° N · 112.8034° W · Mount Carmel',
 intro='Due notti in un ranch a est di Zion, tra pascoli, carri d’epoca e una mandria di bisonti che si lascia avvicinare nelle ore di luce morbida.',
 blocks=[
  ('group', [
   ('20260409-3W9A8247', 'Horse Rides.', 'Il cartello del ranch indica la strada per le passeggiate a cavallo.'),
   ('20260409-3W9A8198', 'Orto.', 'Piantine in vaso, in attesa della primavera vera.')]),
  ('full', ('20260409-3W9A8251', 'Pascolo al tramonto.', 'Il prato del ranch alle 19:33, con un vecchio attrezzo agricolo abbandonato nell’erba.')),
  ('wide', ('20260410-3W9A8319', 'La mandria.', 'Alle 8 del mattino i bisonti pascolano sparsi sul prato.')),
  ('wide', ('20260410-3W9A8337', 'Carri.', 'Vecchi carri coperti, senza più telo, parcheggiati accanto alla staccionata.')),
  ('group', [
   ('20260410-3W9A8525', 'In cammino.', 'Un bisonte attraversa il prato mentre il resto della mandria continua a mangiare.'),
   ('20260410-3W9A8531', 'Faccia a faccia.', 'A 400 mm, uno sguardo dritto nell’obiettivo. La luce del tardo pomeriggio accende il pelo sul dorso.')]),
  ('group', [
   ('20260410-3W9A8624', 'Tramonto sul ranch.', 'Il sole scende dietro le colline e allunga le ombre sul pascolo.'),
   ('20260410-3W9A8632', 'Controluce.', 'Dal basso, tra i fili d’erba, lo stesso sole diventa una stella.')]),
 ]),

dict(num='VIII', date='10–11 aprile 2026', title='Zion',
 coords='37.2722° N · 112.9459° W · Zion National Park',
 intro='Il parco più visitato dello Utah, raccontato soprattutto dai suoi abitanti: scoiattoli striati, pecore bighorn, cervi nel sottobosco. E il fiume che ha scavato il canyon.',
 blocks=[
  ('group', [
   ('20260410-3W9A8400', 'Lo scoiattolo striato.', 'Un chipmunk su un masso di arenaria, a 400 mm.'),
   ('20260410-3W9A8424', 'Merenda.', 'Il cibo stretto tra le zampe, lo sguardo sempre attento.')]),
  ('group', [
   ('20260410-3W9A8472', 'Bighorn.', 'Una pecora bighorn del deserto su una cengia di arenaria. Il parco l’ha reintrodotta negli anni Settanta.'),
   ('20260411-3W9A8691', 'Il Virgin River.', 'Il fiume che ha scavato il canyon di Zion, verde e tranquillo sotto le pareti rosse.')]),
  ('wide', ('20260411-3W9A8732', 'Tra i rami.', 'Un cervo mulo cerca cibo nel sottobosco, quasi invisibile.')),
 ]),

dict(num='IX', date='11 aprile 2026', title='Verso Las Vegas',
 coords='36.0820° N · 115.1726° W · Las Vegas, Nevada',
 intro='L’ultimo giorno è quasi tutto strada. La Interstate 15 taglia l’angolo nord-ovest dell’Arizona, entra in Nevada e arriva fino all’insegna più famosa di Las Vegas.',
 blocks=[
  ('group', [
   ('20260411-3W9A8750', 'Di nuovo Arizona.', 'Sulla I-15 si rientra in Arizona per meno di cinquanta chilometri, nella gola del Virgin River.'),
   ('20260411-3W9A8757', 'Nevada.', 'Poco dopo, l’ultimo confine del viaggio.')]),
  ('wide', ('20260411-3W9A8771', 'Welcome to Fabulous Las Vegas.', 'Alle 18:17, il cartello del 1959 che segna l’arrivo in città. Fine del viaggio. Forse.')),
 ]),
]


# Coordinate corrette a mano (lat, lon), o None per non mostrarle.
# Le foto di Arches erano tutte geotaggate sullo stesso punto: qui ci sono le posizioni dei luoghi fotografati.
GPS = {
    '20260407-3W9A7333-HDR': (37.10264, -109.98919),  # Forrest Gump Point, US-163
    '20260407-3W9A7364-HDR': (37.10264, -109.98919),
    '20260408-3W9A7595': (38.63167, -109.60222),      # Park Avenue
    '20260408-3W9A7600': (38.62776, -109.60290),      # Queen Nefertiti Rock
    '20260408-3W9A7604': (38.66166, -109.58825),      # Petrified Dunes Viewpoint
    '20260408-3W9A7608': None,                        # lucertola: luogo non riconoscibile
    '20260408-3W9A7610': (38.70130, -109.56450),      # Balanced Rock
    '20260408-3W9A7622': (38.70130, -109.56450),
    '20260408-3W9A7624': (38.70130, -109.56450),      # dai pressi di Balanced Rock
    '20260408-3W9A7626': None,                        # Windows Road: punto preciso non riconoscibile
    '20260408-3W9A7627': (38.68436, -109.53496),      # Turret Arch, The Windows
    '20260408-3W9A7628': (38.68436, -109.53496),      # North Window, The Windows
    '20260408-3W9A7636': None,                        # pinne: punto preciso non riconoscibile
    '20260408-3W9A7647': None,                        # Salt Valley: punto preciso non verificato
    '20260408-3W9A7649': (38.74352, -109.49934),      # Delicate Arch (l'arco, visto dal belvedere)
}
