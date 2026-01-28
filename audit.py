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
import html

# fichiers include
from  outils import *  
WIN=ISWIN()
if WIN:
    from win.windows import *
else:
    from ux.linux import *



from  rtf import *   
from ihm  import *



VERSION=GetLocalVersion()

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
FILEFICHE="FicheSmartphone.rtf"     # mini fiche à coller sur le PC  QRcode normal pour appli smartphone
FILEDOUCHETTE="FicheDouchette.rtf" # mini fiche à coller sur le PC  QRcode douchette
FILEACHAT="FicheAchat.rtf"         # fiche d'achat
FILECARACT="caract.html"           # caracteristiques techniques
FILEPARENTAL="LeControleParental.pdf"


DECOUVERTE=f"DecouverteMonPC-{OSTARGET}"      # Répertoire des docs à recopier sur le Bureau

CSVREGLES="regles.csv"                        # fichier .csv décrivant les règles de calcul des notes
CSVCPU="cpus.csv"                             # fichier .csv contenant l'indice cpu ( CPUMARK ) tiré de cpubenchmark.net
CPUBENCHMARK="https://www.cpubenchmark.net/CPU_mega_page.html"   

#==================================================================
# infos administratives
#   utilisation: Admin.xxx
#==================================================================
class Admin():
    # Notation
    notebrut=0          # note initiale, basée sur mémoire/disque/cpu
    notenet=0           # note finale, après règles spécifiques, et notes technique/esthetique
    categorie=""        # categorie du PC
    txtnotes=[]         # Texte pour les calculs de notes, qui sera rajouté au rapport

    benevole=""         # nom du benevole
    observations=""        # observations saisies

    # autres infos 
    ECID=""             # identifiant GRPCxx-nnnn
    iddon=""            # Numero du don dans le Bolc, auquel le PC est associé
    idrecond=""         # Si reconditionneur PRO, ID du PC chez ce reconditionneur
    origine=""          # Origine du PC ( ASF, Ecodair, Trira, ESN ... )  utilisation variable selon les sites
    bolcstatut=""       # statut dans le bolc
    auditdate=""        # date de l'audit



#--------------------------------------------------------
# Sauvegarde/Relit des infos  stockées en local
#--------------------------------------------------------
def DataSave( dir, file,data ):
    filename=os.path.join(dir,file)
    with open( filename,"w") as f:
        f.write(data)

def DataGet( dir, file ):
    filename=os.path.join(dir,file)
    if not os.path.isfile(filename): return ""
    with open( filename,"r") as f:
        data=f.read()
    return data

#--------------------------------------------------------
# Nettoie le nom d'une CPU, avant de la rechercher dans la liste
#
#  INPUT
#     cpuname: nom du cpu
#  RETURN
#     nom du cpu nettoyé
#
#   valeur Inxi                                         Valeur cpubenchhmark.net
#   Intel (R) Core(TM) i5-6200U CPU @ 2.30GHZ           Intel Core i5-6200U @ 2.30GHZ
#   Intel Core i7-5600U                                 Intel Core i7-5600U @ 2.60GHz
#   13th Gen Intel Core i7-1360P                        Intel Core i7-1360P 
#   Intel Core i7 M 620                                 Intel Core i7-620M
#
#   AMD PRO A10-8730B R5, 10 COMPUTE CORES 4C+6G        AMD PRO A10-8730B   (nettoyer à partir de la virgule est utile mais pas suffisant à cause du R5 )
#--------------------------------------------------------   
def CleanCpuname(cpuname):

    # à faire avant les autres
    #cpuname=re.sub( r'[@][{]Name=[^}]*[}]' , "" , cpuname)  # truc tiré de l'auditJJ    supprimer @{Name=.......}
    cpuname=re.sub( r'[@].*' , "" , cpuname)  # on retire à partir du @
    cpuname=re.sub( r'[,].*' , "" , cpuname)  # on retire à partir de la virgule   AMD PRO A10-8730B R5, 10 COMPUTE CORES 4C+6G

    # Cas des cpu Intel
    if cpuname.find("Intel") > -1 :
        cpuname=re.sub( r'\(R\)' , "" , cpuname)   # supprimer (R)
        cpuname=re.sub( r'\(TM\)' , "" , cpuname)  # supprimer (TM)
        cpuname=re.sub( r'CPU ' , "" , cpuname)  # supprimer "CPU "
        cpuname=re.sub( r'[0-9]+th Gen ' , "" , cpuname , 0 , re.IGNORECASE  )  # supprimer "13th Gen , 13TH GEN"


    # Cas des cpu AMD
    if cpuname.find("AMD") > -1 :
        cpuname=re.sub( r' with .*$' , "" , cpuname)  # supprimer " with xxxxxxx" 
        cpuname=re.sub( r' R5$' , "" , cpuname)       # supprimer le R5 final dans AMD PRO A10-8730B R5

    # Pour tout le monde
    cpuname=re.sub( r'\s+' , " " , cpuname)    # 1 seul espace consecutif

    # Note: cA va faire rater la detection des 2 cas particuliers: Intel Core i5 E 520    Intel Core i5 750S 
    # une fois qu'on a un seul espace consecutif, transformer Intel(R) Core(TM) i3 CPU       M 330  en  Intel Core i3-330M
    cpuname=re.sub( r'Intel Core i([0-9]) ([A-Z]) ([0-9]+)' , r"Intel Core i\1-\3\2" , cpuname)  
    # et aussi Intel Core i3 550  en Intel Core i3-550
    cpuname=re.sub( r'Intel Core i([0-9]) ([0-9]+)' , r"Intel Core i\1-\2" , cpuname)  

    cpuname=cpuname.strip()
    return cpuname


            
#--------------------------------------------------------
# Lit le fichier csv des cpus, et cherche un nom de cpu
#
# Les comparaisons se font en minuscules
# Pour éviter des confusions, on compare sur l'égalité
# le nom dans Inxi peut être plus grand que le nom dans cpubenchmark.net, mais pas toujours
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

    #cpuname="Intel Core i3-6100U"


    cpuold=cpuname
    cpuname=CleanCpuname(cpuname)

    cpuname=CpuChange().Adapt(cpuname)
    print(f"Cherche: {cpuold}       Transformé en: {cpuname}")


    newcpuname=cpuname.lower()





    for cpudata in cpulist:
        key=cpudata["NAME"]
        newkey=key.lower()
        # ANCIEN TEST  qui provoque des confusions    Intel Core i3-6100U est confondu avec Intel Core i3-6100   
        #   if ( len(newkey) > 10 and newcpuname.find(newkey) > -1) or ( newkey.find(newcpuname) > -1 ):
        # ce nouveau test limite le risque de confusion, mais ne permet plus de trouver AMD PRO A10-8730B R5, 10 COMPUTE CORES 4C+6G
        if newcpuname == newkey:

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
        area=dialog.area
        hbox=Zhbox(area,0,0)
        vbox=Zvbox(hbox,2,2)
        vboxother=Zvbox(hbox,2,2)

        # Obtention du disque, et stockage de la taille dans les valeurs SSD ou HDD
        boxdisk=Zvbox(vbox,2,2,"Disque")



        if disktype == "":
            Ztext(boxdisk,"Type de disque non détecté !")
            msgdisk= f"Pour savoir si le disque est un HDD ou un SSD, vous pouvez chercher sa référence sur Internet: {infos['DisqueRef']}"
            Ztext(boxdisk,msgdisk)
            Zlistbox(dialog, boxdisk, "DISK", "Type de disque", [ "HDD", "SSD" ] , "HDD" )
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
        Zlistbox(dialog,  boxdelta, "NoteTechnique", "Note Technique", [ "-2","-1","0","1"] , "0") 
        Zlistbox(dialog,  boxdelta,  "NoteEsthetique", "Note Esthétique", [ "-1","0","1"] , "0")

        # autres infos
        pctypes=[ "Portable" , "Tablette", "UC" ]
        index=0
        for i,value in enumerate(pctypes):
            if value==infos["Type"] : index=i
        Zlistbox(dialog,  vboxother,  "Type", "Type de PC", pctypes , "Portable")
        Zentry(dialog, vboxother, "Ecran", "Taille Ecran (pouces): ","r",infos["Ecran"] )
        
        # boutons
        boxactions= Zhbox(area,0,0)
        Zbutton(dialog, boxactions ,"OK", "OK","Yellow")

        # affiche le dialog, attend la sortie, et renvoie le résultat
        out= dialog.Run()
        exitcode=dialog.exitcode
        if exitcode == "#QUIT" : sys.exit()   # trop difficile à gérer si les infos spnt pas saisies !
        

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
    infos["Type"]= out["Type"]
    infos["Ecran"]= out["Ecran"]






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

    hbox=Zhbox(vbox)
    Zentry(dialog, hbox, "benevole", "Nom Bénévole:","r")
    Zentry(dialog, hbox, "nomcomm", "Modèle Commercial","r",infos["Modele"] )

    Zentry(dialog, vbox, "observations", "Observations:","up")

    Zlistbox(dialog, vbox, "bolcstatut", "Statut Reconditionnement", [ "", "En reconditionnement" , "Prêt à vendre" , "En attente" ,  "HS" ,"A entrer dans Salesforce" ] ,"")

    boxadmin=Zvbox(vbox,5,2,"Informations administratives:")
    Ztext(boxadmin,"La manière dont ces infos sont gérées dépend du site ...\nSur certains sites, elles sont facultatives ou préchargées manuellement dans le Bolc avant reconditionnement")
    hbox = Zhbox( boxadmin,2 ,0)
    Zentry(dialog, hbox, "idrecond" , "(PC venant d'un Reconditionneur PRO)\nID du PC chez le reconditionneur:","r")        
    Zentry(dialog, hbox, "origine", "Origine du PC ( ASF, Trira, Ecodair...):","r")   

    boxbolc=Zvbox(vbox,2,2,"Transfert BOLC")
    Ztext(boxbolc,"Si le PC n'a pas déjà été créé dans le Bolc, il faut fournir le N°du don auquel il est associé. Sinon l'import échouera")
    Zentry(dialog,boxbolc , "iddon", "N° du don:","r")  

    boxactions= Zhbox(vbox,0,0)
    Zbutton(dialog, boxactions ,"QUIT", "ABANDON","Orange")
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
#  txtnotes: tableau dans lequel ajouter des lignes d'explication ( UNIQUEMENT avec append() )
# RETURN
#  note de base 
#  txtnotes modifié
#---------------------------------------------------
def ComputeNote( infos , csvfile ,section ,txtnotes):


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
#  txtnotes: tableau dans lequel ajouter des lignes d'explication ( UNIQUEMENT avec append() )
# RETURN
#  note modifiée
#  txtnotes modifié
#---------------------------------------------------
def ComputeNoteModif( infos , csvfile ,section ,txtnotes,initialnote):

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
# Ils sont generés dans le répertoire ../ECID
#---------------------------------------------------     
def MakeSendFiles(xfer=True):
    dir=os.path.join( "..", Admin.ECID)
    if not os.path.isdir(dir):
        os.mkdir(dir)

    # suppression des fichiers  pour éviter une prolifération de fichiers bolc
    with os.scandir(dir) as it:
        for entry in it:
            if entry.is_file() :
                filename=os.path.join( dir, entry.name)
                #print( "**Suppresion: ", filename)
                os.remove( filename)


    filebolc=       os.path.join( dir,f"{Admin.ECID}.{FILEBOLC}" )
    filerapport=    os.path.join( dir,f"{Admin.ECID}.{FILERAPPORT}")
    filefiche=      os.path.join( dir,f"{Admin.ECID}.{FILEFICHE}" )
    filedouchette=  os.path.join( dir,f"{Admin.ECID}.{FILEDOUCHETTE}")
    filescan=       os.path.join( dir,f"{Admin.ECID}.{FILESCAN}")
    fileachat=      os.path.join( dir,f"{Admin.ECID}.{FILEACHAT}")
    filecaract=     os.path.join( dir,f"{Admin.ECID}.{FILECARACT}")
    fileparental=     os.path.join( DECOUVERTE, FILEPARENTAL)

    # fabrication du nom de fichier bolc pour import sftp
    # on le sauvegarde en local, pour pouvoir relancer un import bolc ultérieur
    date= datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    site=Admin.ECID[0:2]
    filebolcimportbase = f"{site}-PORTABLE-{date}.csv"
    filebolcimport     = os.path.join( dir, filebolcimportbase )
    DataSave( TMPDISK , "-bolc.txt",filebolcimport)

    MakeBolc( filebolc )
    MakeRapport( filerapport )
    MakeFiches( filefiche , filedouchette )
    MakeFicheAchat(fileachat)
    ####################################Caract().Html(filecaract)

    # copy fichier scan systeme
    CopyFile2File( TMPSCANFILE , filescan )


    # Copie du rapport sur le Bureau et de DecouverteMonPC .  Le Bureau peut s'appeler Bureau ou Desktop
    print(f"\nCopie du rapport d'audit sur le Bureau")
    code=Copy2Desktop( [ filerapport , filefiche, filedouchette, DECOUVERTE , fileparental] )
    if not code:
        print( f"  !!! Je n'ai pas trouvé le Bureau : il faudra copier manuellement le rapport d'audit et {DECOUVERTE} ")

    # Rajout du détail des notes sur le rapport, avant de l'envoyer 
    with open( filerapport, "a" ) as f:
        f.write("\n\n-------------- Explications de la notation ----------------\n\n" )
        f.write( "\n".join(Admin.txtnotes) )
 


    # fabrication du fichier bolc adapté pour envoi sftp: rajout d'une colonne Numéro de don
    with open( filebolc ) as f:
        bolcdata=f.read()
    with open( filebolcimport , "w" ) as f:
        f.write( Admin.iddon + ";" + bolcdata)


    # On rajoute le nom de fichier bolc dans le rapport pour audits.emmaus-connect.org
    # Car ça facilite la recherche en cas d'erreur d'import bolc
    with open( filerapport, "a" ) as f:
        f.write("\n\n-------------- Import sftp  Bolc ----------------\n" )
        f.write( f"Fichier CSV: {filebolcimportbase}\n"  )
        f.write( f"Statut BOLC: {Admin.bolcstatut}\n"  )



    # Génération d'un .zip pour  envoi 
    print(f"\nCreation du fichier: {ZIPFILE} pour envoi vers audits.emmaus-connect.org" )
    if os.path.isfile(ZIPFILE) :  os.remove(ZIPFILE)
    files= [ filebolc, filebolcimport, filerapport, filescan, filefiche, filedouchette , fileachat ]
    MakeZip( ZIPFILE , files )

    # IHM de transfer
    # Si xfer , on ne pose pas la question
    if not xfer:
        dlgsend=Zdialog("Envoyer les fichiers vers le serveur audits et le Bolc ?",80,40)
        hbox=Zhbox(dlgsend.area,30,30)
        Zbutton(dlgsend , hbox, "QUIT", "QUITTER" ,"Red")
        Zbutton(dlgsend , hbox, "EMMAUS", "Serveur Audit uniquement" ,"LightBlue")
        Zbutton(dlgsend , hbox, "BOTH", "Serveur Audit + BOLC " ,"Yellow")
        rep=dlgsend.Run()
        exitcode=dlgsend.exitcode
    else:
        exitcode="BOTH"

    

    if exitcode in [ "EMMAUS", "BOTH" ] :
        print(f"\n-------------- envoi des fichiers vers audits.emmaus-connect.org  --------------")
        #cmd=f"curl -X POST https://update.drop.tf/upload_zip.php -F \"ecid={Admin.ECID}\" -F \"actual_file=@{ZIPFILE}\"  "
        cmd=f'{CURL} -X POST https://audits.emmaus-connect.org/api/upload/zip {P}quiet{S} -F "ecid={Admin.ECID}" -F "actual_file=@{ZIPFILE}"  '
        os.system(cmd)
        print()

    if exitcode in [ "BOTH" ] :
        # envoi du fichier bolc
        # Pour déposer sur le bolc par sftp, il faut rajouter une 1e colonne contenant le N° du don
        # - si le PC existe déjà dans le bolc, on peut laisser une valeur vide
        # - sinon l'import échouera si le N° de don est vide
        # Le nom de fichier doit être comme   GR-PORTABLE-date.csv , sinon l'import bolc l'ignore 
        print(f"\n-------- envoi du fichier bolc vers le serveur BOLC ({filebolcimportbase}) ------------------")
        code=TransfertBolc(filebolcimport)
        print()

#--------------------------------------------------
# Envoie le fichier vers le Bolc
#
# INPUT
#  filebolcimport:  nom  du fichier . S'il est vide, on le retrouve avec DataGet()
# RETURN
#  code  ( 0 si OK)
#--------------------------------------------------
def TransfertBolc(filebolcimport=""):
    if filebolcimport == "":
        filebolcimport=DataGet(TMPDISK,"-bolc.txt")
    if filebolcimport == "" or not os.path.isfile(filebolcimport):
        print(f"******** Fichier BOLC non trouvé : {filebolcimport} **************")
        return
        
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

    print("**Creation: " , filename)

    items=[
    f"======================= Rapport d'Audit  (Version={VERSION}) ================",   
    f" IDENTIFIANT     : {Admin.ECID}  ",
    f" DATE            : {Admin.auditdate}    ",
    f" REALISE PAR     : {Admin.benevole}  ",
    f"=================================================================================",
    f"",
    f"--------------------------- Informations (les tailles Ram/Disque sont en GB) ------------------"
    ]

    txt1=CRLF.join(items) + CRLF

    txt2=""
    for key,value in infos.items():
        # astuce pour remplacer la valeur numerique des cles SSD et HDD
        if key in [ "SSD","HDD" ] : value="oui"

        txt2=txt2 + f"{key:<20}: {value}" + CRLF


    items=[
    f"",
    f"--------------------------- Notes -----------------------------",
    f" Note Brute : {Admin.notebrut} " ,
    f" Note Nette : {Admin.notenet} ",
    f"",
    f" Categorie  : {Admin.categorie}",
    f"",
    f"--------------------------- Observations -----------------------------",
    Admin.observations
    ]

    txt3=CRLF.join(items) + CRLF

    with open( filename,"w") as f:
        f.write(txt1)
        f.write(txt2)
        f.write(txt3)

#--------------------------------------------------
# Genere la ficher achat
# Utilisation d'un squelette rtf , dans lequel on fait des substitutions
#
# INPUT
#  filename:  nom complet du fichier resultat
#--------------------------------------------------
def MakeFicheAchat(filename):

    template=os.path.join("modeles","ficheachat.rtf")
    with open(template,"r") as f:
        txt=f.read()

    modele=Admin.nomcomm
    txt=txt.replace("LEMAT", f'{infos["Marque"]} {modele}' )
    txt=txt.replace("LIDEC",Admin.ECID)
    txt=txt.replace("LESN",infos["NumeroSerie"])
    txt=txt.replace("LAMARK",infos["Marque"])
    txt=txt.replace("LACAT",Admin.categorie)

    with open(filename,"w") as f:
        f.write(txt)



#--------------------------------------------------
# Genere les mini fiches
# - format qrcode standard ( separateur # )
# - format douchette ( separateur TAB  + multiples transcriptions)
#
# INPUT
#  noms complet des fichier
#--------------------------------------------------
def MakeFiches(filesmartphone , filedouchette ):

    print("**Creation: " ,filesmartphone ,  filedouchette)

    # taille de police
    small=9
    big=12

    date= datetime.datetime.now().strftime("%Y/%m/%d")
    # liste des items à mettre dans la fiche
    items=[
            (big,   "ID:",   Admin.ECID),
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
            (big,   "CAT:",            Admin.categorie ),
            (small, ""            ,  ""),
            (small, "OBSERVATIONS:",  ""),
            (small, "",                 Admin.observations)
            ]

    #------------------------  avec qrcode format smarphone
    # le contenu sera interpétré par un script coté Salesforce . Donc format simple
    # texte du qrcode
    qrcodeitems= [Admin.ECID , infos["NumeroSerie"] , Admin.categorie , infos["Marque"], infos["Modele"] ] 
    txtqrcode = "#".join( qrcodeitems )  #  IDENTIFIANT#NumeroSerie#Marque#Modele

    MakeRTF( items, txtqrcode ,filesmartphone ,TMPDISK )

    #------------------------  avec qrcode format douchette
    # le contenu correspond exactement aux champs coté database Salesforce . Donc formatage hyper complexe
    if Admin.categorie == "Premium" : tmpcat = f"Ordinateur - PREMIUM"
    else:                           tmpcat = f"Ordinateur - Catégorie {Admin.categorie}"

    patterns={ "Dell" : "Dell",  "Hewlett" : "HP"  , "ASUSTeK" : "Asus" , "Packard" : "Packard Bell" , "Essentiel" : "Essentiel B" , "Terra" : "Terra Mobile" , "Apple" : "Apple Mac"  }
    tmpmarque=infos["Marque"]
    for key,value in patterns.items():
        tmp=tmpmarque.upper()
        if tmp.find( key.upper() ) > -1:
            tmpmarque=value
            break

    #catégorie + tabulation + tabulation + tabulation + tabulation + tabulation + tabulation + tabulation + marque + tabulation + tabulation + modèle + tabulation + tabulation + Identiant Emmaus-Connect + tabulation + numéro de série
    txtqrcode=f"{tmpcat}\t\t\t\t\t\t\t{tmpmarque}\t\t{infos['Modele']}\t\t{Admin.ECID}\t{infos['NumeroSerie']}"
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
    Admin.idrecond,             # identifiant du  matériel chez le reconditionneur
    Admin.ECID,                # identifiant EmmausEC
    infos["Type"],              # type de matériel ( Portable , UC )
    Admin.categorie,            # categorie  A B C D Premium INVENDABLE    
    Admin.bolcstatut,           # Prêt à vendre, En reconditionnement ...
    "",                         # commentaire statut . 
    infos["Marque"],            # Marque: HP , Lenovo ...
    "",                         # Constructeur
    "",                         # Nom commercial
    infos["Modele"],            # Modele ...
    infos["Batterie"],          # % de batterie residuel ...
    "",                         # Date de vente
    Admin.observations,         # Observations
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
    Admin.benevole,             # Nom du benevole
    bolcdate,                   # date de l'audit
    infosystem,                 # Commentaire sur le reconditionnement : on y met l'OS cible
    "",                         # nature des dépenses
    "",                         # cout total
    "",                         # lien url
    Admin.origine               # Origine du reconditionnement: utilisation diverse selon les sites
    ]

    # Eviter certains caractères incompatibles avec csv
    for i,value in enumerate(items):
        value=str(value)
        items[i]=value.replace(";" , ",").replace("\r","").replace("\n","")

    txt=";".join(items)

    print("**Creation: " , filename)
    # newline="" est indispensable sous windows pour eviter que \n devienne CRLF
    with open(filename,"w",newline="") as f:
        f.write(txt + "\r\n")
                         
#===========================================================================================
# Collecte des Tests Materiel
#
#  les infos sont mémorisées dans un fichier -caract.txt au format json
#===========================================================================================
class Caract():

    def __init__(self):
        self.file=os.path.join(TMPDISK,"-caract.txt")
        if os.path.isfile( self.file):
            with open(self.file,"r") as f:
                self.data = json.load(f)
        else:
            self.data={ }


    def Save(self,data):
        global infos
        # sauvegarde dans le fichier
        txt=json.dumps( data , indent=4)
        with open(self.file,"w") as f:
            f.write(txt)
        # sauvegarde dans infos
        #infos["Ecran"] = self.data["ECRAN"]

    def Html(self,file):
        txt="<HTML><HEAD><meta charset='UTF-8'></HEAD><BODY>\n<H1>Caracteristiques Techniques</H1><TABLE BORDER=2>\n"
        for key,value in self.data.items():
            value=html.escape(value)
            txt=txt+ f"<TR><TD>{key}</TD><TD>{value}</TD></TR>\n"
        txt=txt+"</TABLE></BODY></HTML>\n"
        
        with open(file,"w") as f:
            f.write(txt)
            
        

    def Dialog(self):
        radioitems=["CLAVIER","PAVE TACTILE","SOURIS","WEBCAM", "DVD/GRAVEUR","LECTEUR SD","PORT SIM", "SORTIE VGA","SORTIE HDMI","SORTIE DISPLAY PORT","SORTIE SON","MICRO","BLUETOOTH","PORT ETHERNET","CARTE WIFI","STATION D'ACCUEIL","ALIMENTATION - CHARGEUR",
                    "SANTE Disque1","SANTE Disque2"]


        radiostatus=[ "TESTE OK",  "HS",  "PRESENT" ,  "ABSENT" ]
        radiostatusdisk=["NEUF","CORRECT","PRUDENCE","MAUVAIS", "ABSENT" ]

        entryitems= { "USB" : "Nbre Ports USB" , "USBHS" : "Dont USB HS" , "BATTERIE" : "Autonomie Batterie (mn)" }

        dialog=Zdialog("COLLECTE RESULTATS TESTS MATERIELS",5,5)
        vbox=dialog.area
        hboxradio=Zhbox(vbox)
        bradio1=Zvbox(hboxradio,2,2)
        bradio2=Zvbox(hboxradio,2,2)

        hboxentry=Zhbox(vbox,5,5)

        # Liste de RadioButtons
        grid1=Zgrid(bradio1)
        grid2=Zgrid(bradio2)
        col=0
        row=0
        maxrows=len(radioitems) // 2 +1
        grid=grid1
        for group in radioitems:

            if row >= maxrows:
                row=0
                grid=grid2

            hbox0=Zhcell(grid,0,row,2,2)
            hbox1=Zhcell(grid,1,row,2,2)
            row=row+1

            if group.find("SANTE") < 0:
                radiolist=radiostatus
            else:
                radiolist=radiostatusdisk

            Ztext(  hbox0 , group)
            for txt in radiolist:

                # Initialisation: si la valeur est dans self.data, on initialise selon cette valeur
                checked=self.data.get( group , "ABSENT" )
                Zradio(dialog, hbox1 , txt, txt,checked,group)

        # Liste de chanps de saisie
        index=0
        for key, txt in entryitems.items():
            #hbox=Zhcell(grid,2,index,5,10)
            initvalue=self.data.get(txt,"")
            Zentry(dialog,hboxentry,txt,txt,"r",initvalue)
            index=index+1

        # Boutons quitter/sauvegarde
        bbox=Zhbox(vbox)
        Zbutton(dialog, bbox ,"QUIT", "QUITTER","orange") 
        Zbutton(dialog, bbox ,"SAVE", "ENREGISTRER","yellow")       

        out=dialog.Run()
        if dialog.exitcode == "SAVE":
            self.Save(out)

#===========================================================
# Gestion / saisie de l'identifiant ECID
# Il est mémorisé dans un fichier local
# 
# Ecid().Get()  renvoie la valeur mémorisée
#  - saisie si le fichier local n'existe pas  ( et dans ce cas crée le fichier local)
#  - abort si on saisie une valeur vide#
# Ecid().Init(value)  permet de mémoriser l'ECID s'il est a été passé en paramètres
# Ecid().Reset()  détruit le fichier local
#==========================================================
class Ecid():

    def __init__(self):
        self.idfile=os.path.join(TMPDISK,"-ecid.txt")
        self.regexp=r"^[A-Z]{2}(PC|TA)[0-9]{2}-[0-9]{4}$"

    def Save(self,value):
        with open(self.idfile,"w") as f:
            f.write(value)

    def Get(self):
        if os.path.isfile(self.idfile):
            with open(self.idfile,"r") as f:
                value=f.read()
        else:
            value=self.Input("")

        # Pour les tests unitaires...
        TestsUnitaires(value)
        TestsUnitaires("ZZTEST")

        return value

    def Init(self,value):
        self.Input(value)

    def Reset(self):
        if os.path.isfile(self.idfile) :  os.remove(self.idfile)        

    def Input(self,value):
        while not re.match( self.regexp , value):
            if value != "":
                msg=f"IDENTIFIANT emmaus incorrect: {value}"
            else:
                msg=""
            value=Zinputbox( "SAISIE IDENTIFIANT" , msg, "Entrer l'identifiant (exemple: GRPC25-9999) "  , value )
            if value == "" : break

        if value == "" : sys.exit()  
        self.Save(value)
        return value

#------------------------------------------------------------------
# Download  un .zip si la version dans version.txt est inferieure à celle sur le serveur
#
#------------------------------------------------------------------
def ShowChange(owner,id):
    Browser("https://audits.emmaus-connect.org/api/apps/linux/changelog/web")

def UpdateMe( remotedir =""):
    localv=GetLocalVersion( )
    remotev=GetRemoteVersion( )

    print(f"Vérification Versions: Local={localv} Serveur={remotev} \n")
    if localv == "" or remotev == "": return

    localvnew=FormatVersion(localv)
    remotevnew=FormatVersion(remotev)



    if localvnew < remotevnew :

        dlg=Zdialog( "Nouvelle Version !")
        Ztext( dlg.area, f"Une version plus récente est disponible !\nVersion actuelle: {localv}  \nVersion disponible: {remotev}" )
        bbox=Zhbox(dlg.area)
        Zbutton(dlg,bbox,"QUIT","IGNORER","orange")
        Zbutton(dlg,bbox,"SHOW","Voir les Evolutions","lightgreen", ShowChange)
        Zbutton(dlg,bbox,"GET","Downloader","yellow")
        out=dlg.Run()
        exitcode=dlg.exitcode

        if exitcode in [ "QUIT" , "#QUIT" ] : return

        zipfile=f"audit-linux.{remotev}.zip"
        print(f"\nDOWNLOAD en cours: {zipfile}\n")

        ret=Download( "audits.emmaus-connect.org", "/api/apps/linux/download/latest" , zipfile )

        if ret  != "" :
            print (f"**** {zipfile} téléchargé ! ****\n")
            exit()        
        else:
            print("*** ECHEC du download ***")

    




#==============================================================================
# Procedure d'Audit
#
#==============================================================================
def ProcessAudit(mini=False,xfer=False):

    global infos # TRES important !

    Admin.ECID = Ecid().Get()





    # Audit du système et extraction des données
    infos=AuditMe()



    # Si le materiel est declaré comme tablette, on force le type
    if len(Admin.ECID) > 4 and Admin.ECID[2:4] == "TA":
        infos["Type"]= "Tablette"

    #print(infos)

    # Recherche du CPUmark dans le fichier csv
    #infos["Processeur"]= "13th Gen Intel (RR) Core i5-3439Y @ 1.50GHz"  #### TEST
    #infos["Processeur"]= "13th Gen Intel (R) Core i5-3439Y @ 1.50GHz"  #### TEST
    #infos["Processeur"]="Intel Core i5 M 520"  ##### test
    print(f"\n----------------- Recherche du processeur dans {CSVCPU} ----------------------")
    cpumark=FindCPUMARK(CSVCPU,infos["Processeur"] )

    # Saisie d'infos complémentaires, y compris le cpumark si pas trouvé
    print("\n------------ Saisie manuelle d'informations --------------------")
    ManualTechInfos(infos,cpumark)

    print("\n----------------- Infos (tailles en GB) ----------------------\n")
    for key,value in infos.items():
        print(f"{key:<20}: {value}")
    #print(json.dumps( infos, sort_keys=False, indent=4))






    print("\n----------------- Calcul des notes  ----------------------")

    # On fait 2 fois le calcul de notes, pour detecter la compatibilite WIN et LINUX
    # la dernière fois est celle de l'OS cible
    # INACTIVE !!!
    if False:
        for os in [ "WIN", "LINUX" ]:
            tmptxtnotes=[]
            sectionnote="#NOTE-" + os  
            note = ComputeNote( infos, CSVREGLES, sectionnote, tmptxtnotes )
            target="Compatible-" + os
            if note < 0 : value ="non"
            else:         value="oui"
            infos[target]=value
            print(f"==> {target}: {value}\n" )

    tmptxtnotes=[]
    sectionnote="#NOTE-" + OSTARGET.upper()  
    note = ComputeNote( infos, CSVREGLES, sectionnote, tmptxtnotes )

    Admin.notebrut= note
    Admin.txtnotes = tmptxtnotes

    Admin.notenet=ComputeNoteModif( infos, CSVREGLES, "#MODIF" , Admin.txtnotes, Admin.notebrut )

    print( "\n".join(Admin.txtnotes)  )

    print(f"\nNote finale={Admin.notenet}")

    Admin.categorie=ComputeCategorie( CSVREGLES,Admin.notenet)
    print(f"Categorie={Admin.categorie}")

    # si Mini Audit , pas d'envoi ....
    if mini : return

    # Sasie des infos manuelles
    result=ManualAdminInfosIHM("Saisie Informations")
    # si on n'a pas cliqué OK, les infos saisies sont invalides, et peuvent provoquer bugs
    if result.get("OK","") == "" : return 

    #print(result)
    Admin.nomcomm=result["nomcomm"]
    Admin.benevole=result["benevole"]
    Admin.observations=result["observations"]
    Admin.bolcstatut=result["bolcstatut"]
    Admin.idrecond=result["idrecond"]
    Admin.origine=result["origine"]
    Admin.iddon=result["iddon"]


    print("\n----------------- Création et envoi des fichiers vers audits.emmaus-connect.org  et Bolc ----------------------")
    Admin.auditdate= datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    MakeSendFiles(xfer)

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

# Se positionne sur le drive/directory du script principal
ChdirScript()

# charger la maj
UpdateMe()

# Test interne désactivé
cpulist=[ "Intel (R) Core(TM)      i5-6200U CPU @ 2.30GHZ  @{Name=bidule}" ,   " AMD 3456 @  2.30GHZ      with double option" ]
cpulist=[]  # desactive le test
if len(cpulist) > 0:
    for cpuname in cpulist :
        print("Cpuname=",cpuname)
        print( "Cleanname=",CleanCpuname(cpuname) )
        print()
    sys.exit()



if __name__ == '__main__':
    
    # Vérifier l'identifiant Emmaus passé en paramètre
    if len(sys.argv) > 1:
        Ecid().Init(sys.argv[1])
        nopc=False
    else:
        nopc=True

    ProcessAudit(mini=False)
    
    # Si exécution directe, attendre RETURN  ( pour ne pas perdre l'affichage )
    if nopc:
        Zinputbox("**FIN**" , "Fin de l'audit !                              ")




  
    



