# -----------------------------------------------------
# Lit un bloc de lignes dans un fichier CSV
#
# Le bloc est repéré par son nom de section en 1e colonne, suivi des noms de colonnes
# il se termine à la section suivante
#
#
# envoie une liste d'items de la forme { key: value, .... } ou key sont les noms de colonnes
# -----------------------------------------------------
def ReadCSV(filename, section):
    datalist = []
    header = []
    with open(filename) as f:
        lines = f.readlines()

    begin = False
    SEP = ""
    for line in lines:
        # deviner si le separateur est , ou ;  selon la 1e ligne
        if SEP == "":
            if line.find(",") > -1:
                SEP = ","
            else:
                SEP = ";"

        line = line.strip(" \r\n")
        items = line.split(SEP)

        if (begin == False):
            # on passe les lignes, jusqu'à trouver la bonne section
            if section == "" or items[0] == section:
                # cette ligne est le HEADER qui contient les noms de colonne
                header = items
                # Fabriquer une liste ayant autant d'elements vides que le header
                # empty = []
                # for x in header: empty.append("")

                begin = True
        else:
            # on est en train de traiter une section
            if line != "" and line[0] == "#": break  # stop when find a new section

            linedict = {}
            for index, value in enumerate(header):
                if index < len(items):
                    linedict[value] = items[index]
                else:
                    linedict[value] = items[index]
            datalist.append(linedict)

    # print(json.dumps( datalist, sort_keys=True, indent=4))
    return datalist
