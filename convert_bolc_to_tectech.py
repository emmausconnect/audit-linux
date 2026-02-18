import sys
import argparse
import json

import tectech_data
from tectech import TecTapiBolcFileConversionError

# BOLC import file example
# 3337;;GRPC26-0008;Portable;B;Prêt à vendre;;Apple;;;MacBookPro12,1;75.4%;;;C02SX6JJFVH4;Intel Core i5-5257U;SSD;251;;;9;;;13.3;0;0;2837;;Rudy;26/01/2026 15:17:45;Linux: Linux Mint 22.2 Zara;;;;ESN

# Let's see what we actually have
# for i, f in enumerate(bmbolcfields):
#     if f.split(',')[0] != '""':
#         print(f"{i}: {f}")
# 0: Admin.iddon                 # id don
# 1: Admin.idrecond,             # identifiant du  matériel chez le reconditionneur
# 2: Admin.ECID,                 # identifiant EmmausEC
# 3: infos["Type"],              # type de matériel ( Portable , UC )
# 4: Admin.categorie,            # categorie  A B C D Premium INVENDABLE
# 5: Admin.bolcstatut,           # Prêt à vendre, En reconditionnement ...
# 7: infos["Marque"],            # Marque: HP , Lenovo ...
# 10: infos["Modele"],            # Modele ...
# 11: infos["Batterie"],          # % de batterie residuel ...
# 13: Admin.observations,         # Observations
# 14: infos["NumeroSerie"],       # Numero de serie
# 15: infos["Processeur"],        # Type de Processeur
# 16: infos["DisqueType"],        # Type de disque HDD/SSD
# 17: infos["DisqueTaille"],      # Capacite disque
# 20: infos["RAM"],               # RAM
# 22: infos["Webcam"],            # Webcam présente ?
# 23: infos["Ecran"],             # Info taille ecran
# 24: infos["NoteTechnique"],     # Pondération technique
# 25: infos["NoteEsthetique"],    # Pondération esthetique
# 26: infos["CPUMARK"],           # Indice processeur
# 28: Admin.benevole,             # Nom du benevole
# 29: bolcdate,                   # date de l'audit
# 30: infosystem,                 # Commentaire sur le reconditionnement : on y met l'OS cible
# 34: Admin.origine               # Origine du reconditionnement: utilisation diverse selon les sites

# some fields must be None/null or of type int
# with open('materielInput.json', 'r') as jf:
#     fs = json.load(jf)
# [(x, fs['properties'][x]) for x in fs['properties'] if fs['properties'][x].get('nullable') and fs['properties'][x].get('type') == 'number']
# [('tailleDisqueDur1', {'type': 'number', 'nullable': True}), ('tailleDisqueDur2', {'type': 'number', 'nullable': True}), ('RAM', {'type': 'number', 'nullable': True})]


def from_bolc_to_tectech(vals: list, idlot: str, idmaterielreconditionneur: str) -> dict:
    # From a file that was ready to send to BOLC, create a dictionary suitable for updating a "materiel" on tec.tech
    # A BOLC-style file contains a single CSV line with 35 fields, like:
    # 3337;;GRPC26-0008;Portable;B;Prêt à vendre;;Apple;;;MacBookPro12,1;75.4%;;;C02SX6JJFVH4;Intel Core i5-5257U;SSD;251;;;9;;;13.3;0;0;2837;;Rudy;26/01/2026 15:17:45;Linux: Linux Mint 22.2 Zara;;;;ESN
    # A dictionary for updating a "materiel" on tec.tech is to be used as payload for api/materiel and looks like:
    #   {"id": "M-2015", "numeroSerie": "FDCDXS2", "RAM": 16, ...}
    # with a mandatory "id", and values compliant with specific types for other fields
    # Here, we will leave "id" aside and provide as many other fields as we can
    bolc_to_tectech_types = {
        "UC": "ORDINATEUR_FIXE",
        "Portable": "ORDINATEUR_PORTABLE",
        "Tablette": "TABLETTE"
    }
    bolc_to_tectech_statuts = {
        "En reconditionnement": "EN_COURS_DE_TRAITEMENT",
        "Prêt à vendre": "PRET_A_DISTRIBUER",
        "En attente": "A_TRAITER",
        "HS": "NON_REEMPLOYABLE",
        "A entrer dans Salesforce": "A_TRAITER"}
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

    def __nullableint(s):
        try:
            return int(s)
        except ValueError:
            return None

    try:
        if len(vals) != 35:
            raise TecTapiBolcFileConversionError

        d = dict()

        # 0: Admin.iddon                 # id don
        ## ==> we use idLot instead
        d['idLot'] = idlot
        # 1: Admin.idrecond,             # identifiant du  matériel chez le reconditionneur
        d['idMaterielReconditionneur'] = idmaterielreconditionneur
        # 2: Admin.ECID,                 # identifiant EmmausEC
        d['idEsn'] = vals[2]
        # 3: infos["Type"],              # type de matériel ( Portable , UC )
        d['typeMateriel'] = bolc_to_tectech_types[vals[3]]
        # 4: Admin.categorie,            # categorie  A B C D Premium INVENDABLE
        d['categorie'] = vals[4].upper()
        # 5: Admin.bolcstatut,           # Prêt à vendre, En reconditionnement ...
        d['statut'] = bolc_to_tectech_statuts.get(vals[5], "EN_COURS_DE_TRAITEMENT")
        if d['categorie'] == "INVENDABLE":
            d['categorie'] = "D"
            d['statut'] = "NON_REEMPLOYABLE"
        # 7: infos["Marque"],            # Marque: HP , Lenovo ...
        d['marque'] = vals[7].upper() if vals[7].upper() in tectech_data.allowed_values['marque'] else ""
        # 10: infos["Modele"],            # Modele ...
        d['model'] = vals[10]
        # 14: infos["NumeroSerie"],       # Numero de serie
        d['numeroSerie'] = vals[14]
        # 15: infos["Processeur"],        # Type de Processeur
        d['processeur'] = vals[15]
        # 16: infos["DisqueType"],        # Type de disque HDD/SSD
        d['typeDisqueDur1'] = vals[16]
        # 17: infos["DisqueTaille"],      # Capacite disque
        d['tailleDisqueDur1'] = __nullableint(vals[17])
        # 20: infos["RAM"],               # RAM
        d['RAM'] = __nullableint(vals[20])
        # 22: infos["Webcam"],            # Webcam présente ?
        if vals[22]:  # ignore if this field is empty in BOLC of contains something else than "oui" or "non"
            if vals[22].lower() == "oui":
                d['webcam'] = True
            elif vals[22].lower() == "non":
                d['webcam'] = False
        # 30: infosystem,                 # Commentaire sur le reconditionnement : on y met l'OS cible
        opsys = vals[30].lower()
        if "android" in opsys:
            d['systemeExploitation'] = "Android"
        elif "ios" in opsys:
            d['systemeExploitation'] = "iOS"
        elif "linux" in opsys:
            d['systemeExploitation'] = "Linux"
        elif "macos" in opsys:
            d['systemeExploitation'] = "MacOS"
        elif "windows" in opsys:
            d['systemeExploitation'] = "Windows"
        else:
            d['systemeExploitation'] = ""

        ## the following have nowhere to go in tec.tech
        # 11: infos["Batterie"],          # % de batterie residuel ...
        # 13: Admin.observations,         # Observations
        # 23: infos["Ecran"],             # Info taille ecran
        # 24: infos["NoteTechnique"],     # Pondération technique
        # 25: infos["NoteEsthetique"],    # Pondération esthetique
        # 26: infos["CPUMARK"],           # Indice processeur
        # 28: Admin.benevole,             # Nom du benevole
        # 29: bolcdate,                   # date de l'audit
        # 34: Admin.origine               # Origine du reconditionnement: utilisation diverse selon les sites

        # at this stage, we have 'idStock' and 'commentaire' to fill up
        d['idStock'] = esn_to_idstock.get(vals[2][0:2])
        if not d['idStock']:
            raise

        # 'commentaire' will hold some of the BOLC fields that fit nowhere in tec.tech structure
        d['commentaire'] = f"cpumark: {vals[26]} / Batterie: {vals[11]} / Écran: {vals[23]}"
        d['commentaire'] += f" / Observations: {vals[13]} / PondTech: {vals[24]} / PondEsth: {vals[25]}"
        d['commentaire'] += f" / Bénévole: {vals[28]} / Origine: {vals[34]}"

    except (TecTapiBolcFileConversionError, Exception) as exc:
        raise TecTapiBolcFileConversionError(exc.__repr__()) from exc

    return d


if __name__ == "__main__":

    parser_ = argparse.ArgumentParser()

    parser_.add_argument("-v", "--verbose", default=False, action='store_true',
                         help="Rendre l'exécution verbeuse")

    parser_.add_argument("-d", "--debug", default=False, action='store_true',
                         help="Afficher les traces d'exécution (aide à la mise au point)")

    parser_.add_argument("-b", "--bolc-file", type=str, required=True,
                         help="Fichier CSV au format d'import BOLC")

    args_ = parser_.parse_args()

    with open(args_.bolc_file, 'r') as bf:
        line = bf.readline().strip('\n')  # we carelessly read a single line and assume it is what we want

    vals_ = line.split(';')

    try:
        d_ = from_bolc_to_tectech(vals_, "L-0048", "EM_2510_0049")
    except(TecTapiBolcFileConversionError, Exception) as exc_:
        print(exc_)
        d_ = {}

    ds_ = json.dumps([d_]).encode('utf-8')

    sys.exit(0)
