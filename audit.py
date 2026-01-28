#=====================================================================================
# Audit Linux 
#
# Il est appelé par audit.sh qui utilise la commande 'inxi' pour générer un fichier TMPSCANFILE
#
# Appel:
#  python3 audit.py GRPCxx-xxxx
# 
#
#=====================================================================================
#
# Réalisation:  Bernard Maison (EmmausConnect Grenoble)
# Version originelle ( basée sur Excel+VBA) : Philippe Ruppli / Bernard Maison
#
#====================================================================================


import json
import re
import sys
import datetime
import os


# fichiers include
from  outils import *   
from  rtf import *   
from ihm  import *



VERSION=GetVersion("version.txt")

USEIHM=True


# detection de l'OS et chargement des scripts d'audit
# va générer TMPDISK , FILESCAN  , OSTARGET , AuditMe()
if "HOME" in os.environ :
    from ux.linux import *
else :
    from win.windows import *


DEBUG=False
if "debug" in sys.argv : DEBUG=True

# Noms de fichiers
ZIPFILE=TMPDISK+ "audit-zip.zip"              # zip des fichiers à envoyer vers audits.emmaus-connect.org

FILEBOLC="bolc.csv"                 # fichier .csv pour import manuel dans le Bolc
FILERAPPORT="audit.txt"             # fichier d'audit déposé sur le Bureau
FILEFICHE="fiche.rtf"               # mini fiche à coller sur le PC  QRcode normal
FILEDOUCHETTE="fiche-douchette.rtf" # mini fiche à coller sur le PC  QRcode douchette


DECOUVERTE=f"DecouverteMonPC-{OSTARGET}"      # Répertoire des docs à recopier sur le Bureau

CSVREGLES="regles.csv"                        # fichier .csv décrivant les règles de calcul des notes
CSVCPU="cpus.csv"                             # fichier .csv contenant l'indice cpu ( CPUMARK ) tiré de cpubenchmark.net
CPUBENCHMARK="https://www.cpubenchmark.net/CPU_mega_page.html"   


# variables globales: ces valeurs pourraient être stockées dans infos
# mais comme infos est affiché automatiquement dans le rapport, certaines rubriques ne seraient pas à la place souhaitée ...
reconditionneur=""  # nom du reconditionneur
remarques=""        # remarques saisies
notebrut=0          # note initiale, basée sur mémoire/disque/cpu
notenet=0           # note finale, après règles spécifiques, et notes technique/esthetique
categorie=""        # categorie du PC

# autres variables globales
don=""              # Numero du don dans le Bolc, auquel le PC est associé
idrecond=""         # Si reconditionneur PRO, ID du PC chez ce reconditionneur
origine=""          # Origine du PC ( ASF, Ecodair, Trira, ESN ... )  utilisation variable selon les sites
bolcstatut=""       # statut dans le bolc
auditdate=""        # date de l'audit
txtnotes=[]         # Texte pour les calculs de notes, qui sera rajouté au rapport



#--------------------------------------------------------
# Nettoie le nom d'une CPU, avant de la rechercher dans la liste
#
#  INPUT
#     cpuname: nom du cpu
#  RETURN
#     nom du cpu nettoyé
#
#   valeur Inxi                                         Valeur cpubenchmark.net
#   Intel (R) Core(TM) i5-6200U CPU @ 2.30GHZ           Intel (R) Core(TM) i5-6200U CPU @ 2.30GHZ
#   Intel Core i7-5600U                                 Intel Core i7-5600U @ 2.60GHz
#   13th Gen Intel Core i7-1360P                        Intel Core i7-1360P 
#--------------------------------------------------------   
def CleanCpuname(cpuname):

    # Cas des cpu Intel
    if cpuname.find("Intel") > -1 :
        cpuname=re.sub( r'\(R\)' , "" , cpuname)   # supprimer (R)
        cpuname=re.sub( r'\(TM\)' , "" , cpuname)  # supprimer (TM)
        cpuname=re.sub( r'CPU ' , "" , cpuname)  # supprimer "CPU "
        cpuname=re.sub( r'[0-9]+th Gen ' , "" , cpuname)  # supprimer "13th Gen "

    # Cas des cpu AMD
    if cpuname.find("AMD") > -1 :
        cpuname=re.sub( r' with .*$' , "" , cpuname)  # supprimer " with xxxxxxx" 

    # Pour tout le monde
    cpuname=re.sub( r'[@][{]Name=[^}]*[}]' , "" , cpuname)  # supprimer @{Name=.......}

    cpuname=re.sub( r'\s+' , " " , cpuname)    # 1 seul espace consecutif
    cpuname=cpuname.strip()
    return cpuname


            
#--------------------------------------------------------
# Lit le fichier csv des cpus, et cherche un nom de cpu
#
# Les comparaisons se font en minuscules
# le nom dans Inxi peut être plus grand que le nom dans cpubenchmark.net, mais pas toujours
#  donc on regarde de 2 manieres:
#   - si la valeur inxi CONTIENT la valeur web ( mais on exclut les valeurs web trop petites, pour éviter les erreurs )
#   - si la valeur web contient la valeur inxi
#  
#   valeur Inxi                           Valeur cpubenchmark.net
#   13th Gen Intel Core i7-1360P          Intel Core i7-1360P 
#   Intel Core i7-5600U                   Intel Core i7-5600U @ 2.60GHz
#
# INPUT
#   cpufile: nom du fichier csv contenant la liste des cpus
#   cpuname: nom de cpu à rechercher
# RETURN
#   l'indice CPU ( CPUMARK) si on trouve la cpu
#   ""  si pas trouvée
#--------------------------------------------------------   
def FindCPUMARK(cpufile,cpuname ):
    # lire le fichier des cpu
    cpulist=ReadCSV(cpufile,"")

    cpuname=CleanCpuname(cpuname)
    newcpuname=cpuname.lower()

    print(f"Cherche: {cpuname}")

    for cpudata in cpulist:
        key=cpudata["CPUNAME"]
        newkey=key.lower()
        if ( len(newkey) > 10 and newcpuname.find(newkey) > -1) or ( newkey.find(newcpuname) > -1 ):

            print(f"Trouve: {key}")
            value=cpudata["CPUMARK"].replace(",","")  # les valeurs peuvent contenir un separateur de milliers
            return value

    print(f"Echec de la recherche...")
    return ""



#--------------------------------------------------------------
# Saisie des infos techniques complémentaires
#
# Si cpumark est vide, demande de le saisir
# Notes Technique/Esthetique
# Type de deisque
#
# INPUT
#  infos: liste des infos utiles
#  cpumark: s'il est vide, on le demandera
# OUTPUT
#  mise à jour de infos 
#-----------------------------------------------------------------
def ManualTechInfos(infos,cpumark):

    disktype=infos["DisqueType"] 
    #disktype=""
    #cpumark=""

    while True:



        dialog=Zdialog("Informations Techniques",10,10)
        vbox=dialog.area

        # Obtention du disque, et stockage de la taille dans les valeurs SSD ou HDD
        boxdisk=Zvbox(vbox,2,2,"Disque")



        if disktype == "":
            Ztext(boxdisk,"Type de disque non détecté !")
            msgdisk= f"Pour savoir si le disque est un HDD ou un SSD, vous pouvez chercher sa référence sur Internet: {infos['DisqueRef']}"
            Ztext(boxdisk,msgdisk)
            Zlistbox(dialog, boxdisk, "DISK", "Type de disque", [ "HDD", "SSD" ] ,0 )
        else:
            msgdisk= f"Type de disque detecté: {disktype}"
            Ztext(boxdisk,msgdisk)


        # saisie du cpumark, si pas trouvé
        boxcpu=Zvbox(vbox,5,5,"CPU")
        Ztext(boxcpu,f'Type de CPU: {infos["Processeur"]}' )

        msgcpu=""
        if cpumark == "" :
            msgcpu=f"Le nom de processeur n'a pas été trouvé dans le fichier local {CSVCPU}:"
            msgcpu=msgcpu + "\nIl faut chercher son 'CPU mark' dans https://www.cpubenchmark.net/CPU_mega_page.html"
            msgcpu=msgcpu+ "\nVous pouvez soit saisir manuellement le CPUmark, soit modifier le fichier csv et relancer l'audit"

        Zentry(dialog, boxcpu, "CPUMARK", "Cpumark: ","r",cpumark)

        # ajustement note
        boxdelta = Zhbox( vbox,5 ,5,"Ajustement Note" )
        Zlistbox(dialog,  boxdelta, "NoteTechnique", "Note Technique", [ "-2","-1","0","1"] ,2) 
        Zlistbox(dialog,  boxdelta,  "NoteEsthetique", "Note Esthétique", [ "-1","0","1"] , 1)

        # boutons
        boxactions= Zhbox(vbox,0,0)
        Zbutton(dialog, boxactions ,"OK", "OK","Yellow")

        # affiche le dialog, attend la sortie, et renvoie le résultat
        out= dialog.Run()

        # Traitement
        ok=True

        cpumark=out["CPUMARK"]
        if not cpumark.isnumeric():
            ok=False
           
        if ok : break

    if "DISK" in out: 
        disktype=out["DISK"]
        infos["DisqueType"]=disktype
    #!!!! il est important que les clés SSD ou HDD contiennent la taille disque, car c'est ce qui est utilisé dans le calcul des regles
    infos[disktype]=infos["DisqueTaille"]

    infos["NoteTechnique"]=int(out["NoteTechnique"])
    infos["NoteEsthetique"]=int(out["NoteEsthetique"])
    infos["CPUMARK"]= cpumark






#===========================================================================
# IHM de saisie des infos administratives
#
#
# Si on ferme la fenêtre avec la croix,on aura result["OK"]=""
#===========================================================================
def ManualAdminInfosIHM(title,margin=2,spacing=2):
    # créer l'objet Zdialog
    dialog=Zdialog(title,margin,spacing)
    vbox=dialog.area

    Zentry(dialog, vbox, "reconditionneur", "Nom Bénévole:","up")
    Zentry(dialog, vbox, "remarques", "Remarques:","up")

    Zlistbox(dialog, vbox, "bolcstatut", "Statut Reconditionnement", [ "", "En reconditionnement" , "Prêt à vendre" , "En attente" ,  "HS" ,"A entrer dans Salesforce" ] ,0)

    boxadmin=Zvbox(vbox,5,2,"Informations administratives:")
    Ztext(boxadmin,"La manière dont ces infos sont gérées dépend du site ...\nSur certains sites, elles sont facultatives ou préchargées manuellement dans le Bolc avant reconditionnement")
    hbox = Zhbox( boxadmin,2 ,0)
    Zentry(dialog, hbox, "idrecond" , "(PC venant d'un Reconditionneur PRO)\nID du PC chez le reconditionneur:","r")        
    Zentry(dialog, hbox, "origine", "Origine du PC ( ASF, Trira, Ecodair...):","r")   

    boxbolc=Zvbox(vbox,2,2,"Transfert BOLC")
    Ztext(boxbolc,"Si le PC n'a pas déjà été créé dans le Bolc, il faut fournir le N°du don auquel il est associé. Sinon l'import échouera")
    Zentry(dialog,boxbolc , "don", "N° du don:","r")  

    boxactions= Zhbox(vbox,0,0)
    Zbutton(dialog, boxactions ,"OK", "OK","Yellow")

    # affiche le dialog, attend la sortie, et renvoie le résultat
    return dialog.Run()





#--------------------------------------------------
# Calcule la note de base ( CPU, RAM, DISK ) , en fonction des infos de regles.csv
#
# renvoie cette note
# rajoute les details dans txtnotes
#
# INPUT
#  infos: liste des infos utiles
#  csvfile: nom du fichier csv des règles
#  section: nom de la section du csv à utiliser
# RETURN
#  note de base
#---------------------------------------------------
def ComputeNote( infos , csvfile ,section ):
    global txtnotes

    rules=ReadCSV( csvfile,section)
    finalnote=0

    # parcourir toutes les regles
    for rule in rules:

        # sur quel critere la regle s'applique
        key=rule[section]
        if key == "" : continue  # ligne vide ou non applicable

        # si le critere existe dans les infos
        if key in infos:
            keyvalue=int( infos[key] )
            keynote=0

            # parcourir les valeurs de la regle, si la valeur reelle est inferieure à la valeur de la règle, on retourne la note associée
            for note,limit in rule.items():
                if limit == "": limit="999999999"   # Cas de la note maximale. Pour elle, on met une valeur limite infinie
                if not limit.isnumeric(): continue  # Eliminer ce qui n'est pas une valeur numerique

                vlimit=float(limit)*0.94  # 6% de marge: une memoire de 16GB apparait comme 15.30GB
                if keyvalue < vlimit:
                    txt=f"{key}={keyvalue} Note={note}" 
                    txtnotes.append(txt)
                    finalnote=finalnote+ float(note)
                    break;

    return int(finalnote)            

#--------------------------------------------------
# Modifie la note de base , en fonction de regles
#
# renvoie la note finale
# rajoute le detail des claculs dans txtnotes
#
# INPUT
#  infos: liste des infos utiles
#  csvfile: nom du fichier csv des règles
#  section: nom de la section du csv à utiliser
#  initialnote: note initiale à modifier
# RETURN
#  note modifiée
#---------------------------------------------------
def ComputeNoteModif( infos , csvfile ,section ,initialnote):
    global txtnotes
    maxcrit=5
    rules=ReadCSV( csvfile,section)

    note=initialnote


    txtnotes.append("")
    txtnotes.append(f"Note brute avant ajustements={initialnote} ")
    txtnotes.append(f"Delta NoteTechnique={infos['NoteTechnique']}")
    txtnotes.append(f"Delta NoteEsthetique={infos['NoteEsthetique']}")

    note=note + int(infos["NoteTechnique"]) + int(infos["NoteEsthetique"])
    txtnotes.append("")

    # parcourir toutes les regles
    for rule in rules:
        if rule[section]=="" : continue    # regle non activée si la 1e colonne est vide
        #print("\n",rule["DESCRIPTION"])
        allpresent=True
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
            if critname not in infos: 
                ok=False
            else:
                infosvalue=infos[critname] 
                # si critvalue est vide, on vérifier seulement que le critname existe dans infos
                # si non, on verifie que la valeur reelle dans infos est inferieure à critvalue
                if critvalue != "" :
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
            txtnotes.append(f"Note Initiale={memnote} Note Modifiée={note}")

    return note

#--------------------------------------------------
# Calcule la categorie 
#
#
# INPUT
#  csvfile: nom du fichier csv des règles
#  note:    note à convertir en catégorie
# RETURN
#  categorie
#---------------------------------------------------
def ComputeCategorie( csvfile , note):
    if note < 0: note=0

    section="#CATEGORIE"
    table=ReadCSV( csvfile,section  )

    cat=""
    for item in table:
        cat=item[section]
        if str(note) == item["NOTE"]:
            return cat

    # pas trouve ! on prend le dernier de la liste
    return cat
         
#--------------------------------------------------
# Genere les fichiers ( bolc.csv , audit.txt )
#
# Les envoie....
#
# Ils sont generés dans le répertoire ../IDENTIFIANT
#---------------------------------------------------     
def MakeSendFiles():
    dir="../" + IDENTIFIANT
    if not os.path.isdir(dir):
        os.mkdir(dir)


    filebolc= ConvertFile( f"{dir}/{IDENTIFIANT}.{FILEBOLC}" )
    filerapport=ConvertFile(f"{dir}/{IDENTIFIANT}.{FILERAPPORT}")
    filefiche= ConvertFile( f"{dir}/{IDENTIFIANT}.{FILEFICHE}" )
    filedouchette=ConvertFile(f"{dir}/{IDENTIFIANT}.{FILEDOUCHETTE}")
    filescan=ConvertFile(f"{dir}/{IDENTIFIANT}.{FILESCAN}")

    # fabrication du nom de fichier bolc pour import sftp
    date= datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    site=IDENTIFIANT[0:2]
    filebolcimportbase = f"{site}-PORTABLE-{date}.csv"
    filebolcimport     = ConvertFile( f"{dir}/{filebolcimportbase}" )

    MakeBolc( filebolc )
    MakeRapport( filerapport )
    MakeFiches( filefiche , filedouchette )

    # copy fichier scan systeme
    CopyFile2File( TMPSCANFILE , filescan )


    # Copie du rapport sur le Bureau et de DecouverteMonPC .  Le Bureau peut s'appeler Bureau ou Desktop
    print(f"\nCopie du rapport d'audit sur le Bureau")
    code=Copy2Desktop( [ filerapport , filefiche, filedouchette, DECOUVERTE ] )
    if not code:
        print( f"  !!! Je n'ai pas trouvé le Bureau : il faudra copier manuellement le rapport d'audit et {DECOUVERTE} ")

    # Rajout du détail des notes sur le rapport, avant de l'envoyer 
    with open( filerapport, "a" ) as f:
        f.write("\n\n-------------- Explications de la notation ----------------\n\n" )
        f.write( "\n".join(txtnotes) )
 


    # fabrication du fichier bolc adapté pour envoi sftp: rajout d'une colonne Numéro de don
    with open( filebolc ) as f:
        bolcdata=f.read()
    with open( filebolcimport , "w" ) as f:
        f.write( don + ";" + bolcdata)


    # On rajoute le nom de fichier bolc dans le rapport pour audits.emmaus-connect.org
    # Car ça facilite la recherche en cas d'erreur d'import bolc
    with open( filerapport, "a" ) as f:
        f.write("\n\n-------------- Import sftp  Bolc ----------------\n" )
        f.write( f"Fichier CSV: {filebolcimportbase}\n"  )
        f.write( f"Statut BOLC: {bolcstatut}\n"  )



    # Génération d'un .zip pour  envoi 
    print(f"\nCreation du fichier: {ZIPFILE} pour envoi vers audits.emmaus-connect.org" )
    if os.path.isfile(ZIPFILE) :  os.remove(ZIPFILE)
    files= [ filebolc, filebolcimport, filerapport, filescan, filefiche, filedouchette ]
    MakeZip( ZIPFILE , files )

    rep = InputValue("\nEnvoyer les fichiers vers audits.emmaus-connect.org [ o / n ] ? ", ["o","n",""])
    if rep != "o" : return


    print(f"\n-------------- envoi des fichiers vers audits.emmaus-connect.org  --------------")
    #cmd=f"curl -X POST https://update.drop.tf/upload_zip.php -F \"ecid={IDENTIFIANT}\" -F \"actual_file=@{ZIPFILE}\"  "
    cmd=f'{CURL} -X POST https://audits.emmaus-connect.org/api/upload/zip {P}quiet{S} -F "ecid={IDENTIFIANT}" -F "actual_file=@{ZIPFILE}"  '
    os.system(cmd)
    
    print()

    # envoi du fichier bolc
    # Pour déposer sur le bolc par sftp, il faut rajouter une 1e colonne contenant le N° du don
    # - si le PC existe déjà dans le bolc, on peut laisser une valeur vide
    # - sinon l'import échouera si le N° de don est vide
    # Le nom de fichier doit être comme   GR-PORTABLE-date.csv , sinon l'import bolc l'ignore 
    rep = InputValue("\nEnvoyer les fichiers vers le BOLC  [ o / n ] ? ", ["o","n",""])
    if rep != "o" : return
    print(f"\n-------- envoi du fichier bolc vers le serveur BOLC ({filebolcimportbase}) ------------------")


    print()


    # envoi par sftp , en utilisant la commande curl
    fileconf="sftp.conf"
    cmd= f"{CURL} -k {P}fast{S} -T {filebolcimport} sftp://sftpemmaus.newmips.cloud:22222"
    if DEBUG :
        print(cmd)
        print()
    code=os.system(cmd)
    if ( code == 0 ) : print("******** Transfert BOLC OK **************")

    

#--------------------------------------------------
# Genere le fichier rapport
#
# INPUT
#  filename:  nom complet du fichier
#--------------------------------------------------
def MakeRapport(filename):

    CRLF="\r\n"

    print("Creation du fichier: " , filename)

    items=[
    f"======================= Rapport d'Audit  (Version={VERSION}) ================",   
    f" IDENTIFIANT     : {IDENTIFIANT}  ",
    f" DATE            : {auditdate}    ",
    f" REALISE PAR     : {reconditionneur}  ",
    f"=================================================================================",
    f"",
    f"--------------------------- Informations (les tailles Ram/Disque sont en GB) ------------------"
    ]

    txt1=CRLF.join(items) + CRLF

    txt2=""
    for key,value in infos.items():
        txt2=txt2 + f"{key:<20}: {value}" + CRLF


    items=[
    f"",
    f"--------------------------- Notes -----------------------------",
    f" Note Brute : {notebrut} " ,
    f" Note Nette : {notenet} ",
    f"",
    f" Categorie  : {categorie}",
    f"",
    f"--------------------------- Remarques -----------------------------",
    remarques
    ]

    txt3=CRLF.join(items) + CRLF

    with open( filename,"w") as f:
        f.write(txt1)
        f.write(txt2)
        f.write(txt3)

#--------------------------------------------------
# Genere les mini fiches
# - format qrcode standard ( separateur # )
# - format douchette ( separateur TAB  + multiples transcriptions)
#
# INPUT
#  noms complet des fichier
#--------------------------------------------------
def MakeFiches(filesmartphone , filedouchette ):

    print("Creation des fichiers: " ,filesmartphone ,  filedouchette)

    # taille de police
    small=9
    big=12

    date= datetime.datetime.now().strftime("%Y/%m/%d")
    # liste des items à mettre dans la fiche
    items=[
            (big,   "ID:",   IDENTIFIANT),
            (small, "DATE:",        date  ),
            (small, "MARQUE:",        infos["Marque"]  ),
            (small, "MODELE:",         infos["Modele"]  ),
            (small, "S/N:",            infos["NumeroSerie"]  ),
            (small, "SYSTEME:",      "Linux: " + infos["Systeme"]  ),
            (small, "DISQUE:",       f'{infos["DisqueType"]} {infos["DisqueTaille"]} GB '  ),
            (small ,"MEMOIRE:",      f'{infos["RAM"]}  GB '  ),
            (small, "CPU:",           f'{infos["Processeur"]}'  ),
            (small ,"CPUMARK:",       f'{infos["CPUMARK"]}'  ),
            (small, "BATTERIE:",      f'{infos["Batterie"]}'  ),
            (big,   "CAT:",     categorie ),
            (small, ""            ,  ""),
            (small, "OBSERVATIONS:",  ""),
            (small, "",remarques)
            ]

    #------------------------  avec qrcode format smarphone
    # le contenu sera interpétré par un script coté Salesforce . Donc format simple
    # texte du qrcode
    qrcodeitems= [IDENTIFIANT , infos["NumeroSerie"] , categorie , infos["Marque"], infos["Modele"] ] 
    txtqrcode = "#".join( qrcodeitems )  #  IDENTIFIANT#NumeroSerie#Marque#Modele

    MakeRTF( items, txtqrcode ,filesmartphone ,TMPDISK )

    #------------------------  avec qrcode format douchette
    # le contenu correspond exactement aux champs coté database Salesforce . Donc formatage hyper complexe
    tmpcat=categorie
    if categorie == "Premium" : tmpcat = f"Ordinateur - PREMIUM"
    else:                       tmpcat = f"Ordinateur - Catégorie {categorie}"

    patterns={ "Dell" : "Dell",  "Hewlett" : "HP"  , "ASUSTeK" : "Asus" , "Packard" : "Packard Bell" , "Essentiel" : "Essentiel B" , "Terra" : "Terra Mobile" , "Apple" : "Apple Mac"  }
    tmpmarque=infos["Marque"]
    for key,value in patterns.items():
        tmp=tmpmarque.upper()
        if tmp.find( key.upper() ) > -1:
            tmpmarque=value
            break

    #catégorie + tabulation + tabulation + tabulation + tabulation + tabulation + tabulation + tabulation + marque + tabulation + tabulation + modèle + tabulation + tabulation + Identiant Emmaus-Connect + tabulation + numéro de série
    txtqrcode=f"{tmpcat}\t\t\t\t\t\t\t{tmpmarque}\t\t{infos['Modele']}\t\t{IDENTIFIANT}\t{infos['NumeroSerie']}"
    MakeRTF( items, txtqrcode ,filedouchette, TMPDISK )


        
#--------------------------------------------------
# Genere le fichier bolc
#
# C'est le format utilisé pour entrer un fichier csv, depuis le site web du Bolc
# Il ne contient pas la 1e colonne avec le numéro du don
# 
# INPUT
#  filename:  nom complet du fichier
#--------------------------------------------------
def MakeBolc(filename):

    bolcdate=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")  #impérativement format francais

    infosystem="Linux: " + infos["Systeme"]

    items=    [
    idrecond,                   # identifiant du  matériel chez le reconditionneur
    IDENTIFIANT,                # identifiant EmmausEC
    infos["Type"],              # type de matériel ( Portable , UC )
    categorie,                  # categorie  A B C D Premium INVENDABLE    
    bolcstatut,                 # Prêt à vendre, En reconditionnement ...
    "",                         # commentaire statut . 
    infos["Marque"],            # Marque: HP , Lenovo ...
    "",                         # Constructeur
    "",                         # Nom commercial
    infos["Modele"],            # Modele ...
    infos["Batterie"],          # % de batterie residuel ...
    "",                         # Date de vente
    remarques,                  # Remarques
    infos["NumeroSerie"],       # Numero de serie
    infos["Processeur"],        # Type de Processeur
    infos["DisqueType"],        # Type de disque HDD/SSD
    infos["DisqueTaille"],      # Capacite disque
    "",                         # disk2 type
    "",                         # disk2 capacite
    infos["RAM"],               # RAM
    "",                         # Info DVD
    infos["Webcam"],            # Webcam présente ?
    infos["Ecran"],             # Info taille ecran
    infos["NoteTechnique"],     # Pondération technique
    infos["NoteEsthetique"],    # Pondération esthetique
    infos["CPUMARK"],           # Indice processeur
    "",                         # Autonomie batterie (mn)
    reconditionneur,            # Nom du reconditionneur
    bolcdate,                   # date de l'audit
    infosystem,                 # Commentaire sur le reconditionnement : on y met l'OS cible
    "",                         # nature des dépenses
    "",                         # cout total
    "",                         # lien url
    origine                     # Origine du reconditionnement: utilisation diverse selon les sites
    ]

    # Eviter certains caractères incompatibles avec csv
    for i,value in enumerate(items):
        value=str(value)
        items[i]=value.replace(";" , ",").replace("\r","").replace("\n","")

    txt=";".join(items)

    print("Creation du fichier: " , filename)
    # newline="" est indispensable sous windows pour eviter que \n devienne CRLF
    with open(filename,"w",newline="") as f:
        f.write(txt + "\r\n")
                         

#=============================== Main ==============================

# Catcher le CTRL/C
try:
    import signal

    def signal_handler(sig, frame):
        print()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

except:
    print()

# Test interne désactivé
cpulist=[ "Intel (R) Core(TM)      i5-6200U CPU @ 2.30GHZ  @{Name=bidule}" ,   " AMD 3456 @  2.30GHZ      with double option" ]
cpulist=[]  # desactive le test
if len(cpulist) > 0:
    for cpuname in cpulist :
        print("Cpuname=",cpuname)
        print( "Cleanname=",CleanCpuname(cpuname) )
        print()
    sys.exit()

# Vérifier l'identifiant Emmaus passé en paramètre
if len(sys.argv) > 1:
    IDENTIFIANT=sys.argv[1]
    nopc=False
else:
    IDENTIFIANT =""
    nopc=True


# Contrôle de l'identifiant, et resaisie éventuelle
#regexp=r"^[A-Z]{2}(PC|TA)[0-9]{2}-[0-9]{4}$"
#if not re.match( regexp , IDENTIFIANT):
#    print( "IDENTIFIANT emmaus incorrect",IDENTIFIANT)
#    IDENTIFIANT=InputValue( "Entrer l'identifiant (exemple: GRPC25-9999) ? " , [] , regexp )

# Contrôle de l'identifiant, et resaisie éventuelle
regexp=r"^[A-Z]{2}(PC|TA)[0-9]{2}-[0-9]{4}$"
while not re.match( regexp , IDENTIFIANT):
    msg=f"IDENTIFIANT emmaus incorrect: {IDENTIFIANT}"
    IDENTIFIANT=Zinputbox( "SAISIE IDENTIFIANT" , msg, "Entrer l'identifiant (exemple: GRPC25-9999) "  , IDENTIFIANT )
    if IDENTIFIANT == "" : break

if IDENTIFIANT == "" : sys.exit()  

# Pour les tests unitaires...
TestsUnitaires(IDENTIFIANT)
TestsUnitaires("ZZPCTEST")


# Audit du système et extraction des données
infos=AuditMe()


# Si le materiel est declaré comme tablette, on force le type
if len(IDENTIFIANT) > 4 and IDENTIFIANT[2:4] == "TA":
    infos["Type"]= "Tablette"

#print(infos)

# Recherche du CPUmark dans le fichier csv
#infos["Processeur"]= "13th Gen Intel (RR) Core i5-3439Y @ 1.50GHz"  #### TEST
#infos["Processeur"]= "13th Gen Intel (R) Core i5-3439Y @ 1.50GHz"  #### TEST
print(f"\n----------------- Recherche du processeur dans {CSVCPU} ----------------------")
cpumark=FindCPUMARK(CSVCPU,infos["Processeur"] )

# Saisie d'infos complémentaires, y compris le cpumark si pas trouvé
print("\n------------ Saisie manuelle d'informations --------------------")
ManualTechInfos(infos,cpumark)

print("\n----------------- Infos (tailles en GB) ----------------------\n")
for key,value in infos.items():
    print(f"{key:<20}: {value}")
#print(json.dumps( infos, sort_keys=False, indent=4))



result=ManualAdminInfosIHM("Saisie Informations")
# si on n'a pas cliqué OK, les infos saisies sont invalides, et peuvent provoquer bugs
if "OK" not in result or result["OK"] == "" : sys.exit() 

#print(result)

reconditionneur=result["reconditionneur"]
remarques=result["remarques"]
bolcstatut=result["bolcstatut"]
idrecond=result["idrecond"]
origine=result["origine"]
don=result["don"]



print("\n----------------- Calcul des notes ----------------------")
sectionnote="#NOTE-" + OSTARGET.upper() 
notebrut=ComputeNote( infos, CSVREGLES, sectionnote )
notenet=ComputeNoteModif( infos, CSVREGLES, "#MODIF" , notebrut )

print( "\n".join(txtnotes)  )

print(f"\nNote finale={notenet}")

categorie=ComputeCategorie( CSVREGLES,notenet)
print(f"Categorie={categorie}")







print("\n----------------- Création et envoi des fichiers vers audits.emmaus-connect.org  et Bolc ----------------------")
auditdate= datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

MakeSendFiles()

# Si exécution directe, attendre RETURN  ( pour ne pas perdre l'affichage )
if nopc:
    code=InputValue("\n\n*** Fini ! ***  Tapez RETURN pour sortir ? ")




  
    



