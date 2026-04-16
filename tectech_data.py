# Values come from the file model found in:
# https://docs.google.com/spreadsheets/d/1uWtNCHW6uhdZ3IxzKSQ8yKZuQMgxUQgIFn7x0lzx7yY

allowed_values = {

    "typeMateriel": {"ORDINATEUR_FIXE", "ORDINATEUR_PORTABLE", "SMARTPHONE", "TABLETTE"},

    "statut": {"A_TRAITER", "EN_COURS_DE_TRAITEMENT", "NON_REEMPLOYABLE", "PRET_A_COMMANDER", "EN_COURS_DE_LIVRAISON",
               "PRET_A_DISTRIBUER", "DISTRIBUE", "SAV"},

    "systemeExploitation": {"Android", "iOS", "Linux", "MacOS", "Windows"},

    "categorie": {"PREMIUM", "A", "B", "C", "D"},

    "webcam": {True, False},

    "lecteurDVD": {True, False},

    "marque": {"ACER", "ADATA", "ALCATEL", "ALTICE", "ALTYK", "APPLE", "ARCHO", "AST", "ASUS", "BELINEA", "BENQ",
               "BLACKBERRY", "BLACKVIEW", "BLUEBIRD", "BOUYGUES TELECOM", "CANON", "CLEVO", "COMPAQ", "DANEW", "DELL",
               "DOOGEE", "DORO", "EIZO", "EMACHINES", "EPSON", "ESSENTIEL B", "FUJITSU", "GATEWAY", "GETAC", "GIGABYTE",
               "GOOGLE", "HAIER", "HISENSE", "HONOR", "HP", "HTC", "HUAWEI", "HYUNDAI", "IBM", "IIYAMA", "KLIPAD",
               "LENOVO", "LG", "LINCPLUS", "LOGICOM", "MEDION", "MEIZU", "MICROSOFT", "MIRAXESS", "MOTION COMPUTING",
               "MOTOROLA", "MSI", "NEC", "NOKIA", "ONE PLUS", "ORANGE", "ORDISSIMO", "PACKARD BELL", "PANASONIC",
               "PHILIPS", "RAZER", "REALME", "SAGEM", "SAMSUNG", "SCHNEIDER", "SONY", "THOMSON", "TOSHIBA", "VIEWSONIC",
               "VIVO", "WESTERN DIGITAL", "WHEATEK", "WIKO", "WINCOR", "WORTMANN", "XIAOMI", "ZTE"}}


internal_to_external_fnames = {
    'typeMateriel': 'Type de matériel',
    'idMaterielReconditionneur': 'ID du matériel chez le reconditionneur',
    'statut': 'Statut',
    'idStock': 'ID du stock',
    'numeroSerie': 'Numero de serie',
    'IMEI1': 'IMEI 1',
    'IMEI2': 'IMEI 2',
    'idEsn': 'ID ESN',
    'model': 'Modèle',
    'marque': 'Marque',
    'processeur': 'Processeur',
    'typeDisqueDur1': 'Type disque dur 1',
    'tailleDisqueDur1': 'Taille disque dur 1',
    'typeDisqueDur2': 'Type disque dur 2',
    'tailleDisqueDur2': 'Taille disque dur 2',
    'RAM': 'RAM',
    'systemeExploitation': "Système d'exploitation",
    'categorie': 'Catégorie',
    'lecteurDVD': 'Lecteur DVD',
    'webcam': 'Webcam',
    'commentaire': 'Commentaire'
}
external_to_internal_fnames = {internal_to_external_fnames[k]: k for k in internal_to_external_fnames}

internal_to_external_snames = {
    "NON_REEMPLOYABLE": "Non réemployable",
    "PRET_A_COMMANDER": "Prêt à commander",
    "EN_COURS_DE_TRAITEMENT": "En cours de traitement",
    "A_TRAITER": "À traiter",
    "SAV": "SAV",
    "PRET_A_DISTRIBUER": "Prêt à distribuer",
    "DISTRIBUE": "Distribué",
    "EN_COURS_DE_LIVRAISON": "En cours de livraison"
}
external_to_internal_snames = {internal_to_external_snames[k]: k for k in internal_to_external_snames}

esn_to_idstock = {
    "LV": "S-0052",
    "VI": "S-0053",
    "MB": "S-0054",
    "ST": "S-0055",
    "SD": "S-0089",
    "CR": "S-0090",
    "RO": "S-0091",
    "LI": "S-0092",
    "LY": "S-0093",
    "GR": "S-0094",
    "MA": "S-0095",
    "BX": "S-0096",
}
idstock_to_esn = {esn_to_idstock[k]: k for k in esn_to_idstock}
