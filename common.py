#################################################################
#  fonctions diverses
#
################################################################

import json

#----------------------------------------------------------
# Decode un texte de la forme 45.78 GiB ou 2400 MB
# renvoie le nombre converti en GB
#
# ATTENTION !
#  1 GB  = 1000 * 1000 * 1000 bytes
#  1 GiB = 1024 * 1024 * 1024 bytes = 1.0737 GB
#----------------------------------------------------------
def unusedDecodeNumber(s):
    s=s.upper()
    s=s.replace("," , ".")  
    # on ne prend que la 1e partie dans 45.78 GiB  
    tmp=s.split(" ")
    tmp=tmp[0]
    f=float(tmp)
    # par defaut on considere que c'est des GB
    # si on trouve un MB pour dire MB , on convertit 
    # idem pour MIB GIB
    if  s.find("MB") > -1 or s.find("MO") > -1 :
        return f/1000
    if  s.find("MIB") > -1 or s.find("MIO") > -1 :
        return f * 1.024 * 1.024 / 1000
    if  s.find("GIB") > -1 or s.find("GIO") > -1 :
        return f * 1.024 * 1.024 * 1.024
    return f

#-----------------------------------------------------
# Lit un bloc de lignes dans un fichier CSV
#
# Le bloc est repéré par son nom de section en 1e colonne, suivi des noms de colonnes
# il se termine à la section suivante
#
#
# envoie une liste d'items de la forme { key: value, .... } ou key sont les noms de colonnes
#----------------------------------------------------- 
def ReadCSV( filename,section ):

        datalist=[]
        header=[]
        with open( filename) as f:
            lines=f.readlines()

        begin=False
        SEP=""
        for line in lines:
            # deviner si le separateur est , ou ;  selon la 1e ligne
            if SEP == "":
                if line.find(",") > -1 : SEP=","
                else:                    SEP=";"

            line=line.strip(" \r\n")
            items=line.split(SEP)

            if (begin == False ):
                # on passe les lignes, jusqu'à trouver la bonne section
                if section=="" or items[0] == section: 
                    # cette ligne est le HEADER qui contient les noms de colonne
                    header=items
                    # Fabriquer une liste ayant autant d'elements vides que le header
                    empty=[]
                    for x in header: empty.append( "" ) 

                    begin=True
            else:
                # on est en train de traiter une section
                if line != "" and line[0] == "#" : break   # stop when find a new section 

                linedict={}
                for index,value in enumerate(header):
                    if index < len(items):
                        linedict[value] = items[index]
                    else:
                        linedict[value] = items[index]
                datalist.append( linedict )

        #print(json.dumps( datalist, sort_keys=True, indent=4))
        return datalist

