# Temi: le stesse fotografie degli album, raccolte per soggetto.
# Ogni tema diventa una pagina (temi/<slug>/ in italiano, en/temi/<slug>/ in inglese) e una tessera nella home.
# 'photos' elenca i nomi dei file (senza .jpg) nell'ordine in cui compaiono; 'cover' è la foto della tessera.
# Didascalie e testi delle foto vengono dagli album, nella lingua della pagina.

THEMES = [
    dict(slug='paesaggi', cover='20260406-3W9A6974-HDR',
         it=('Paesaggi', 'Canyon, archi e deserti, dalla prima luce all’ultima.'),
         en=('Landscapes', 'Canyons, arches and desert, from first light to last.'),
         photos=['20260405-3W9A6381', '20260406-3W9A6974-HDR', '20260405-3W9A6401', '20260406-3W9A6754-HDR',
                 '20260405-3W9A6475', '20260406-3W9A6794-HDR', '20260407-3W9A7089', '20260407-3W9A7127',
                 '20260407-3W9A7145', '20260407-3W9A7168', '20260408-3W9A7624', '20260408-3W9A7628',
                 '20260408-3W9A7636', '20260408-3W9A7647', '20260408-3W9A7649', '20260409-3W9A7868',
                 '20260409-3W9A8143', '20260409-3W9A8157', '20260411-3W9A8691']),
    dict(slug='animali', cover='20260410-3W9A8531',
         it=('Animali', 'Chi abita i parchi: bisonti, cervi, scoiattoli e qualche lucertola.'),
         en=('Wildlife', 'The locals: bison, deer, squirrels and the odd lizard.'),
         photos=['20260410-3W9A8531', '20260405-3W9A6450', '20260408-3W9A7575', '20260405-3W9A6512',
                 '20260407-3W9A7153', '20260407-3W9A7154', '20260408-3W9A7608', '20260410-3W9A8319',
                 '20260410-3W9A8525', '20260410-3W9A8400', '20260410-3W9A8424', '20260410-3W9A8472',
                 '20260411-3W9A8732']),
    dict(slug='strada', cover='20260411-3W9A8771',
         it=('Strada', 'Cartelli, confini e chilometri di asfalto dritto.'),
         en=('On the road', 'Signs, state lines and miles of straight blacktop.'),
         photos=['20260407-3W9A7333-HDR', '20260407-3W9A7076', '20260407-3W9A7083', '20260405-3W9A6419',
                 '20260409-3W9A8247', '20260411-3W9A8750', '20260411-3W9A8757', '20260411-3W9A8771']),
    dict(slug='alba-e-tramonto', cover='20260406-3W9A7060',
         it=('Alba e tramonto', 'Le ore per cui vale la pena svegliarsi presto o fare tardi.'),
         en=('First and last light', 'The hours worth getting up early, or staying out late, for.'),
         photos=['20260409-3W9A7813-HDR', '20260406-3W9A7060', '20260405-3W9A6590-HDR', '20260407-3W9A7364-HDR',
                 '20260408-3W9A7399', '20260407-3W9A7388', '20260408-3W9A7651', '20260408-3W9A7660',
                 '20260409-3W9A7816', '20260409-3W9A8251', '20260410-3W9A8624', '20260410-3W9A8632',
                 '20260406-3W9A6861-2']),
]
