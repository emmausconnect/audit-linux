#####################################################################################
# Calcul des notes et de la categorie finale
#
# txtnote=[]
# initialnote=  ComputeNote( infos , csvregles ,section ,txtnotes):
# finalnote=    ComputeNoteModif( infos , csvregles ,section ,txtnotes,initialnote)
# categorie=    ComputeCategorie( csvregles , finalnote)
#
#####################################################################################
from common import *

#--------------------------------------------------
# Calcule la categorie 
#
#
# INPUT
#  csvregles: nom du fichier csv des règles
#  note:    note à convertir en catégorie
# RETURN
#  categorie
#---------------------------------------------------
def ComputeCategorie( csvregles , note):
    if note < 0: note=0

    section="#CATEGORIE"
    table=ReadCSV( csvregles,section  )

    cat=""
    for item in table:
        cat=item[section]
        if str(note) == item["NOTE"]:
            return cat

    # pas trouve ! on prend le dernier de la liste
    return cat

#--------------------------------------------------
# Calcule la note de base ( CPU, RAM, DISK ) , en fonction des infos de regles.csv
#
# renvoie cette note
# rajoute les details dans txtnotes
#
# INPUT
#  infos: liste des infos utiles
#  csvregles: nom du fichier csv des règles
#  section: nom de la section du csv à utiliser
#  txtnotes: tableau dans lequel ajouter des lignes d'explication ( UNIQUEMENT avec append() )
# RETURN
#  note de base 
#  txtnotes modifié
#---------------------------------------------------
def ComputeNote(infdic, csvregles, section, txtnotes):


    rules=ReadCSV( csvregles,section)
    finalnote=0

    # parcourir toutes les regles
    for rule in rules:

        # sur quel critere la regle s'applique
        key=rule[section]
        if key == "" : continue  # ligne vide ou non applicable

        # si le critere existe dans les infos
        if key in infdic:
            keyvalue=float(infdic[key])
            keyvalue=round(keyvalue)     # arrondi : une mémoire de 3.99 GO sera vue comme 4 . Il y a des petits risque d'écart suite à la conversion GiB / GB
            # keynote=0

            # parcourir les valeurs de la regle, si la valeur reelle est inferieure à la valeur de la règle, on retourne la note associée
            for note,limit in rule.items():
                if limit == "": limit="999999999"   # Cas de la note maximale. Pour elle, on met une valeur limite infinie
                if not limit.isnumeric(): continue  # Eliminer ce qui n'est pas une valeur numerique

                # marge:  
                # marge= 0.94  # 6% de marge  ... permet à un disque de 250GO d'être traité comme un disque 256GO
                marge=1.0    # abandon de la marge : pour éviter des écarts avec les moulinettes Excel qui peuvent exister dans les sites
                vlimit=float(limit)* marge  
                if keyvalue < vlimit:
                    txt=f"{key}={keyvalue} Note={note}" 
                    txtnotes.append(txt)
                    finalnote=finalnote+ float(note)
                    break

    return int(finalnote)            

#--------------------------------------------------
# Modifie la note de base , en fonction de regles
#
# renvoie la note finale
# - application de NoteTechnique NoteEsthetique
# - application de règles
#
# rajoute le detail des claculs dans txtnotes
#
# INPUT
#  infos: liste des infos utiles
#  csvregles: nom du fichier csv des règles
#  section: nom de la section du csv à utiliser
#  initialnote: note initiale à modifier
#  txtnotes: tableau dans lequel ajouter des lignes d'explication ( UNIQUEMENT avec append() )
# RETURN
#  note modifiée
#  txtnotes modifié
#---------------------------------------------------
def ComputeNoteModif(infdic, csvregles, section, txtnotes, initialnote):

    maxcrit=5
    rules=ReadCSV( csvregles,section)

    note=initialnote


    txtnotes.append("")
    txtnotes.append(f"Note brute avant ajustements={initialnote} ")
    txtnotes.append(f"Delta NoteTechnique={infdic['NoteTechnique']}")
    txtnotes.append(f"Delta NoteEsthetique={infdic['NoteEsthetique']}")

    note= note + int(infdic["NoteTechnique"]) + int(infdic["NoteEsthetique"])
    txtnotes.append("")

    # parcourir toutes les regles
    for rule in rules:
        if rule[section]=="" : continue    # regle non activée si la 1e colonne est vide
        #print("\n",rule["DESCRIPTION"])
        # allpresent=True
        critlist={}

        # fabriquer la liste des criteres non vides pour cette règle
        for i in range( 0, maxcrit ):
            keycrit=f"CRIT{i}"
            keyval=f"VAL{i}"
            if keycrit in rule : 
                critname= rule[keycrit] 
                critvalue= rule[keyval] 
                if critname != "":
                    critlist[ critname  ] = critvalue

        # vérifer chaque critère
        explain=[]
        ok=True
        for critname,critvalue in critlist.items():
            # tous les criteres doivent être presents dans infos
            if critname not in infdic:
                ok=False
            else:
                infosvalue=infdic[critname]
                # si critvalue est vide, on vérifier seulement que le critname existe dans infos
                # si non, on verifie que la valeur reelle dans infos est inferieure à critvalue
                if critvalue == "" :
                    explain.append(f"{critname}")
                else:
                    if float( infosvalue ) >= float( critvalue) : ok=False
                    explain.append(f"{critname}={infosvalue}")



        # si ok est True, on applique la règle
        if ok:
            memnote=note
            desc=rule["DESCRIPTION"]

            action=rule["DELTA"]
            if  action != "" and action.isnumeric() :
                note=note + int( action )

            action=rule["MAX"]
            if action  != ""  and action.isnumeric() :
                note= min( note ,int( action )  )

            txtnotes.append( f"\nREGLE: {desc}" )
            txt=" ".join(explain)
            txtnotes.append(f"VALEURS: [{txt}]" )
            txtnotes.append(f"Note Initiale={memnote}   Note Modifiee={note}")

    return note


