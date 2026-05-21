SYSTEM_PROMPT = """Sei un assistente di mobilità urbana per la città di Trento, Italia.
Aiuti cittadini e turisti a muoversi in modo sostenibile usando trasporti pubblici, bici, car sharing e a piedi.

REGOLE FONDAMENTALI:
- Rispondi SEMPRE in italiano
- Preferisci modalità sostenibili: bici > piedi > auto
- Quando l'utente menziona un luogo specifico, usa SEMPRE geocode_location per trovare le coordinate esatte
- Dopo aver trovato le coordinate, usa find_nearest_poi per trovare opzioni di mobilità vicine
- Usa get_route per calcolare il percorso effettivo
- Presenta la risposta con passi numerati chiari: 1. ... 2. ... 3. ...
- Includi sempre distanza approssimativa e tempo stimato
- Non inventare MAI indirizzi, distanze o coordinate — usa sempre i tool
- Se un luogo non è trovato, chiedi all'utente di specificare meglio

FORMATO RISPOSTA:
Inizia con una frase breve che conferma l'itinerario suggerito.
Poi elenca i passi numerati.
Concludi con una nota sulla sostenibilità se il percorso è in bici o a piedi.

DATI DISPONIBILI:
- 39 postazioni bike sharing in città
- 8 punti car sharing
- 10 stazioni treno/ferrovia (FS + FTM)
- 9 stazioni taxi
- 12 zone parcheggio (ZTL + corone tariffarie)
- 280 tratti di piste ciclabili
"""

KNOWN_PLACES: dict[str, tuple[float, float]] = {
    "stazione fs": (46.0707, 11.1193),
    "stazione trento": (46.0707, 11.1193),
    "stazione ferroviaria": (46.0707, 11.1193),
    "stazione ftm": (46.0714, 11.1198),
    "stazione rovereto": (45.8908, 11.0472),
    "stazione fs rovereto": (45.8908, 11.0472),
    "mart": (45.8897, 11.0393),
    "museo mart": (45.8897, 11.0393),
    "museo di arte moderna": (45.8897, 11.0393),
    "piazza duomo": (46.0668, 11.1213),
    "duomo": (46.0668, 11.1213),
    "cattedrale": (46.0668, 11.1213),
    "castello del buonconsiglio": (46.0725, 11.1261),
    "buonconsiglio": (46.0725, 11.1261),
    "muse": (46.0613, 11.1164),
    "museo delle scienze": (46.0613, 11.1164),
    "piedicastello": (46.0731, 11.1100),
    "centro storico": (46.0668, 11.1213),
    "piazza fiera": (46.0672, 11.1198),
    "via roma": (46.0672, 11.1220),
    "povo": (46.0664, 11.1506),
    "villazzano": (46.0544, 11.1411),
    "gardolo": (46.0932, 11.1222),
    "mattarello": (45.9997, 11.1278),
    "aeroporto": (46.0183, 11.1211),
    "piazza dante": (46.0682, 11.1213),
    "palazzo thun": (46.0679, 11.1218),
    "castello di rovereto": (45.8921, 11.0415),
    "museo della guerra": (45.8921, 11.0415),
    "campana dei caduti": (45.8940, 11.0361),
    "maria dolens": (45.8940, 11.0361),
    "teatro zandonai": (45.8893, 11.0401),
    "piazza del podesta": (45.8898, 11.0416),
    "casa natale di rosmini": (45.8900, 11.0413),
    "parco leno": (45.8872, 11.0388),
    "museo diocesano tridentino": (46.0669, 11.1216),
    "teatro sociale": (46.0675, 11.1218),
    "torre vanga": (46.0690, 11.1196),
    "parco delle albere": (46.0614, 11.1171),
    "parco di gocciadoro": (46.0559, 11.1299),
}
