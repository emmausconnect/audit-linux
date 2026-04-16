#=====================================================================================
# Audit Linux 
#
# Il est appelé par audit.sh
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

import time
import datetime
import html
import os.path
import signal
import json
import zipfile
import sys
import re
import argparse

from trace import Tracer
_DSFMT = "%Y%m%d.%H%M%S"
DATESTAMP = time.strftime(_DSFMT, datetime.datetime.now().timetuple())

_tracer = Tracer(name="audit-linux", ts=DATESTAMP, debugmode=False)
_logger = _tracer.get_logger()
_logger.info(f"Nom du fichier de trace: {_tracer.get_tracefilename()}")

import __about__
import tectech_data
from outils import Browser, MakeZip, Editor, ChdirScript
from outils import TransfertTectech, TransfertEmmaus, GetRemoteVersionInfo, DownloadFile
from cpumark import FindCpuMark
from categorie import ComputeCategorie, ComputeNote, ComputeNoteModif
from  rtf import MakeRTF
# from ihm  import *
from ihm import Zdialog, Zhbox, Zvbox, Zlistbox, Zentry, Zbutton, Ztext, Zradio, Zgrid, Zhcell, Zinputbox
from ux.linux import AuditMe, get_user_dirs, chown_to_user, Copy2Desktop, CopyFile2File

from __about__ import __version__
from ux.linux import TMPDISK, FILESCAN, TMPSCANFILE

ZIPFILE=os.path.join(TMPDISK, "audit-zip.zip"   )   # zip des fichiers à envoyer vers audits.emmaus-connect.org

FILEBOLC="bolc.csv"                 # fichier .csv pour import manuel dans le Bolc
FILERAPPORT="audit.txt"             # fichier d'audit déposé sur le Bureau
FILEFICHE="FicheSmartphone.rtf"     # mini fiche à coller sur le PC  QRcode normal pour appli smartphone
FILEDOUCHETTE="FicheDouchette.rtf" # mini fiche à coller sur le PC  QRcode douchette
FILEACHAT="FicheAchat.rtf"         # fiche d'achat
FILECARACT="caract.html"           # caracteristiques techniques
FILEPARENTAL="LeControleParental.pdf"

OSTARGET="Linux"  # Utilisé pour trouver kes règles dans regles.csv , et comme suffixe pour DecouverteMonPC
DECOUVERTE=f"DecouverteMonPC-{OSTARGET}"      # Répertoire des docs à recopier sur le Bureau

CSVREGLES="regles.csv"                        # fichier .csv décrivant les règles de calcul des notes
# CPUBENCHMARK="https://www.cpubenchmark.net/CPU_mega_page.html"

#==================================================================
# infos administratives
#   utilisation: Admin.xxx
#==================================================================
class Admin:
    # Notation
    notebrut=0          # note initiale, basée sur mémoire/disque/cpu
    notenet=0           # note finale, après règles spécifiques, et notes technique/esthetique
    categorie=""        # categorie du PC
    txtnotes=[]         # Texte pour les calculs de notes, qui sera rajouté au rapport

    benevole=""         # nom du benevole
    observations=""        # observations saisies

    # autres infos 
    ECID=""             # identifiant GRPCxx-nnnn
    iddonlot=""            # Numero du don (resp. lot) dans le Bolc (resp. tec.tech), auquel le PC est associé
    idrecond=""         # Si reconditionneur PRO, ID du PC chez ce reconditionneur
    origine=""          # Origine du PC ( ASF, Ecodair, Trira, ESN ... )  utilisation variable selon les sites
    bolcstatut=""       # statut dans le bolc
    auditdate=""        # date de l'audit
    nomcomm = ""        # modèle?


def DataSave(somedir, file, data):
    filename = os.path.join(somedir, file)
    with open(filename, "w") as f:
        f.write(data)


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
def ManualTechInfos(infdic, cpumark):
    _logger.debug(f"Avant saisie manuelle: {infdic=}")

    disktype=infdic["DisqueType"]
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
        if False and disktype == "":
            Ztext(boxdisk,"Type de disque non détecté !")
            msgdisk= f"Pour savoir si le disque est un HDD ou un SSD, vous pouvez chercher sa référence sur Internet: {infdic['DisqueRef']}"
            Ztext(boxdisk,msgdisk)
            Zlistbox(dialog, boxdisk, "DISK", "Type de disque", [ "HDD", "SSD" ] , "HDD" )
        else:
            _ = disktype + ("/nvme" if infdic.get("NVME") else "/ata") if disktype == "SSD" else ""
            msgdisk = f"Disque principal: {_} - {infdic.get('DisqueTaille')} Go"
            msgdisk += f"\nAutres disques: {infdic.get('AutresDisques')}"
            Ztext(boxdisk,msgdisk)

        boxram=Zvbox(vbox,2,2,"RAM")
        Ztext(boxram, f"{infdic.get('RAM')} Gio")

        # saisie du cpumark, si pas trouvé
        boxcpu=Zvbox(vbox,5,5,"CPU")
        Ztext(boxcpu,f'Type de CPU: {infdic["Processeur"]}')

        Zentry(dialog, boxcpu, "CPUMARK", "cpumark: ", "r", cpumark)

        # ajustement note
        boxdelta = Zhbox( vbox,5 ,5,"Ajustement de la note" )
        Zlistbox(dialog,  boxdelta, "NoteTechnique", "Note technique", [ "-2","-1","0","1"] , "0")
        Zlistbox(dialog,  boxdelta,  "NoteEsthetique", "Note esthétique", [ "-1","0","1"] , "0")

        # autres infos
        pctypes=["Portable", "Fixe", "Tablette"]
        # index=0
        # for i,value in enumerate(pctypes):
        #     if value==infosdict["Type"] : index=i
        Zlistbox(dialog,  vboxother,  "Type", "Type de PC", pctypes , infdic.get('Type', "Portable"))
        Zentry(dialog, vboxother, "Ecran", "Taille Ecran (pouces): ","r", infdic["Ecran"])
        
        # boutons
        boxactions= Zhbox(area,0,0)
        Zbutton(dialog, boxactions ,"OK", "OK","Yellow")

        # affiche le dialog, attend la sortie, et renvoie le résultat
        out= dialog.Run()
        exitcode=dialog.exitcode
        if exitcode == "#QUIT" : sys.exit()   # trop difficile à gérer si les infos sont pas saisies !
        

        # Traitement
        ok=True

        cpumark=out["CPUMARK"]
        if not cpumark.isnumeric():
            ok=False
           
        if ok : break

    # if "DISK" in out:
    #     disktype=out["DISK"]
    #     infdic["DisqueType"]=disktype
    #!!!! il est important que les clés SSD ou HDD contiennent la taille disque, car c'est ce qui est utilisé dans le calcul des regles
    infdic[disktype]=infdic["DisqueTaille"]

    infdic["CPUMARK"]= cpumark

    infdic["NoteTechnique"]=int(out["NoteTechnique"])
    infdic["NoteEsthetique"]=int(out["NoteEsthetique"])

    infdic["Type"]= out["Type"]
    infdic["Ecran"]= out["Ecran"]

    _logger.debug(f"Après saisie manuelle: {infdic=}")


#===========================================================================
# IHM de saisie des infos administratives
#
#
# Si on ferme la fenêtre avec la croix,on aura result["OK"]=""
#===========================================================================
def ManualAdminInfosIHM(infdic, title, margin=2, spacing=2):
    # créer l'objet Zdialog
    dialog=Zdialog(title,margin,spacing)
    vbox=dialog.area

    hbox=Zhbox(vbox)
    Zentry(dialog, hbox, "benevole", "Nom Bénévole:","r")
    Zentry(dialog, hbox, "nomcomm", "Modèle Commercial","r", infdic["Modele"])

    Zentry(dialog, vbox, "observations", "Observations:","up")

    # Zlistbox(dialog, vbox, "bolcstatut", "Statut Reconditionnement", [ "", "En reconditionnement" , "Prêt à vendre" , "En attente" ,  "HS" ,"A entrer dans Salesforce" ] ,"")

    items =list(tectech_data.external_to_internal_snames.keys())
    Zlistbox(dialog, vbox, "bolcstatut", "Statut Reconditionnement", items ,"")

    boxadmin=Zvbox(vbox,5,2,"Informations administratives:")
    Ztext(boxadmin,"Pour un PC reconditionné par un pro, préciser son ID."
          " Si le PC a été reconditionné en ESN, laisser ce champ vide.\n"
          "Le champ 'origine' est ajouté au 'commentaire' dans tec.tech")
    hbox = Zhbox( boxadmin,2 ,0)
    Zentry(dialog, hbox, "idrecond" , "ID du PC chez le reconditionneur:","r")
    Zentry(dialog, hbox, "origine", "Origine du PC:","r")

    dest = "tec.tech"
    nrequis = "lot"
    boxbolc=Zvbox(vbox,2,2,f"Transfert {dest}")
    Ztext(boxbolc, f"Si le PC n'a pas déjà été créé dans {dest}, fournir le n° du {nrequis}"
                   " auquel il est associé, sinon l'import échouera")
    Zentry(dialog,boxbolc , "iddonlot", f"N° du {nrequis}:","r")

    boxactions= Zhbox(vbox,0,0)
    Zbutton(dialog, boxactions ,"QUIT", "ABANDON","Orange")
    Zbutton(dialog, boxactions ,"OK", "OK","Yellow")

    # affiche le dialog, attend la sortie, et renvoie le résultat
    return dialog.Run()







         
#--------------------------------------------------
# Genere les fichiers ( bolc.csv , audit.txt )
#
# Les envoie....
#
# Ils sont generés dans le répertoire ../ECID
#---------------------------------------------------     
def MakeSendFiles(infdic, useprodapi: bool = False, xfer=True):
    eciddir = os.path.join("..", Admin.ECID)
    if not os.path.isdir(eciddir):
        os.mkdir(eciddir)

    # suppression des fichiers  pour éviter une prolifération de fichiers bolc
    with os.scandir(eciddir) as it:
        for entry in it:
            if entry.is_file() :
                filename = os.path.join(eciddir, entry.name)
                #_logger.info( "**Suppresion: ", filename)
                os.remove( filename)

    filebolc = os.path.join(eciddir, f"{Admin.ECID}.{FILEBOLC}")
    filerapport = os.path.join(eciddir, f"{Admin.ECID}.{FILERAPPORT}")
    filefiche = os.path.join(eciddir, f"{Admin.ECID}.{FILEFICHE}")
    filedouchette = os.path.join(eciddir, f"{Admin.ECID}.{FILEDOUCHETTE}")
    filescan = os.path.join(eciddir, f"{Admin.ECID}.{FILESCAN}")
    fileachat = os.path.join(eciddir, f"{Admin.ECID}.{FILEACHAT}")
    filecaract = os.path.join(eciddir, f"{Admin.ECID}.{FILECARACT}")
    fileparental = os.path.join(DECOUVERTE, FILEPARENTAL)

    # fabrication du nom de fichier bolc pour import sftp
    # on le sauvegarde en local, pour pouvoir relancer un import bolc ultérieur
    date= datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    site=Admin.ECID[0:2]
    filebolcimportbase = f"{site}-PORTABLE-{date}.csv"
    filebolcimport = os.path.join(eciddir, filebolcimportbase)
    DataSave( TMPDISK , "-bolc.txt",filebolcimport)

    MakeBolc(infdic, filebolc)
    MakeRapport(infdic, filerapport, header=True, details=False)
    MakeFiches(infdic, filefiche, filedouchette)
    MakeFicheAchat(infdic, fileachat)
    Caract().Html(filecaract)

    # copy fichier scan systeme
    CopyFile2File( TMPSCANFILE , filescan )


    # Copie du rapport sur le Bureau et de DecouverteMonPC .  Le Bureau peut s'appeler Bureau ou Desktop
    # tobecopied = [ filerapport , filefiche, filedouchette, DECOUVERTE , fileparental]
    tobecopied = [DECOUVERTE , fileparental]
    _logger.info(f"Copie de {tobecopied} sur le bureau")
    code=Copy2Desktop(tobecopied)
    if not code:
        _logger.warning( f"  !!! Je n'ai pas trouvé le Bureau : il faudra copier manuellement le rapport d'audit et {DECOUVERTE} ")

    # Rajout du détail des notes sur le rapport, avant de l'envoyer 
    MakeRapport(infdic, filerapport, header=True, details=True)

 


    # fabrication du fichier bolc adapté pour envoi sftp: rajout d'une colonne Numéro de don
    with open( filebolc ) as f:
        bolcdata=f.read()
    with open( filebolcimport , "w" ) as f:
        f.write( Admin.iddonlot + ";" + bolcdata)


    # On rajoute le nom de fichier bolc dans le rapport pour audits.emmaus-connect.org
    # Car ça facilite la recherche en cas d'erreur d'import bolc
    with open( filerapport, "a" ) as f:
        f.write("\n\n-------------- Import sftp  Bolc ----------------\n" )
        f.write( f"Fichier CSV: {filebolcimportbase}\n"  )
        f.write( f"Statut BOLC: {Admin.bolcstatut}\n"  )

    # this should be the right place to adjust ownership of the various files/dirs we just created
    chown_to_user(eciddir)

    # Génération d'un .zip pour  envoi 
    _logger.info(f"Création du fichier: {ZIPFILE} pour envoi vers audits.emmaus-connect.org" )
    if os.path.isfile(ZIPFILE) :  os.remove(ZIPFILE)
    files= [ filebolc, filebolcimport, filerapport, filescan, filefiche, filedouchette , fileachat ]
    MakeZip( ZIPFILE , files )

    # IHM de transfer
    # Si xfer , on ne pose pas la question
    if not xfer:
        dlgsend=Zdialog("Envoyer les fichiers vers le serveur audits et tec.tech?",80,40)
        hbox=Zhbox(dlgsend.area,30,30)
        Zbutton(dlgsend , hbox, "QUIT", "QUITTER" ,"Red")
        Zbutton(dlgsend , hbox, "EMMAUS", "Serveur Audit uniquement" ,"LightBlue")
        btntitle = f'tec.tech({"PROD" if useprodapi else "TEST"})'
        Zbutton(dlgsend , hbox, "BOTH", f"Serveur Audit + {btntitle} " ,"Yellow")
        dlgsend.Run()
        exitcode=dlgsend.exitcode
    else:
        exitcode="BOTH"

    _logger.info(">" * 64)
    _logger.info(f"{infdic=}")
    _logger.info("<" * 64)

    if exitcode in [ "BOTH" ] :
        _logger.info(f"===== Les infos du fichier (BOLC) {filebolcimportbase} iront dans"
              f' tec.tech ({"PROD" if useprodapi else "TEST"}) =====')
        _logger.info(f"Admin.iddonlot: {Admin.iddonlot}, Admin.idrecond: {Admin.idrecond}")
        TransfertTectech(filebolcimport, useprodapi, Admin.iddonlot, Admin.idrecond, Admin.ECID)

    if exitcode == "BOTH":
        # add the tectech CSV file to the ZIP archive
        dest = os.path.join("..", Admin.ECID, f"{Admin.ECID}.tect.csv")
        with zipfile.ZipFile(ZIPFILE, mode='a') as z:
            z.write(dest, os.path.basename(dest))

    if exitcode in ["EMMAUS", "BOTH"]:
        _logger.info("=== Envoi des fichiers vers audits.emmaus-connect.org ===")
        TransfertEmmaus(ZIPFILE, Admin.ECID)
        _logger.info("=== ...terminé ===")


    

#--------------------------------------------------
# Genere le fichier rapport
#
# INPUT
#  filename:  nom complet du fichier
#  header:      si True, on affiche le header
#  details:   si True, on affiche le details du calcul des notes
#--------------------------------------------------
def MakeRapport(infdic, filename, header, details):

    if header: icon=""
    else   : icon="➡️ "

    CRLF="\n"

    if header:
        _logger.info(f"Création de: {filename}")

    items=[
    f"======================= Rapport d'Audit  (Version={__version__}) ================",
    f" IDENTIFIANT     : {Admin.ECID}  ",
    f" DATE            : {Admin.auditdate}    ",
    f" REALISE PAR     : {Admin.benevole}  ",
    "=================================================================================",
    "",
    ]

    txt1=CRLF.join(items) + CRLF

    txt2=    "✅--------------------------- Informations (Gio pour la mémoire, Go pour les disques) ------------------" +CRLF + CRLF
    for key,value in infdic.items():
        # astuce pour remplacer la valeur numerique des cles SSD et HDD
        # if key in [ "SSD","HDD" ] : value="oui"

        txt2=txt2 + f"{icon}{key:<20}: {value}" + CRLF

    if infdic["DisqueType"] == "SSD":
        ouinon = "NVME" if infdic.get("NVME") == "oui" else "ATA"
    else:
        ouinon = "N/A"
    txt2 += f"{icon}{'NVME/ATA':<20}: {ouinon}" + CRLF


    items=[
    "",
    "✅--------------------------- Notes -----------------------------",
    f" Note Brute : {Admin.notebrut} " ,
    f" Note Nette : {Admin.notenet} ",
    "",
    f" Categorie  : {Admin.categorie}",
    "",
    "✅--------------------------- Observations -----------------------------",
    Admin.observations
    ]

    txt3=CRLF.join(items) + CRLF

    txt4= "\n\n✅-------------- Explications de la notation ----------------\n\n"
    txt4 = txt4 + "\n".join(Admin.txtnotes) 


    with open( filename,"w",encoding="utf-8") as f:
        if header: f.write(txt1)
        f.write(txt2)
        f.write(txt3)
        if details: f.write(txt4)

#--------------------------------------------------
# Genere la ficher achat
# Utilisation d'un squelette rtf , dans lequel on fait des substitutions
#
# INPUT
#  filename:  nom complet du fichier resultat
#--------------------------------------------------
def MakeFicheAchat(infdic, filename):

    template=os.path.join("modeles","ficheachat.rtf")
    with open(template,"r") as f:
        txt=f.read()

    modele=Admin.nomcomm
    txt=txt.replace("LEMAT", f'{infdic["Marque"]} {modele}')
    txt=txt.replace("LIDEC",Admin.ECID)
    txt=txt.replace("LESN", infdic["NumeroSerie"])
    txt=txt.replace("LAMARK", infdic["Marque"])
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
def MakeFiches(infdic, filesmartphone, filedouchette):

    _logger.info(f"Création de: {filesmartphone}, {filedouchette}")

    # taille de police
    small=9
    big=12

    date= datetime.datetime.now().strftime("%Y/%m/%d")
    # liste des items à mettre dans la fiche
    items=[
            (big,   "ID:",   Admin.ECID),
            (small, "DATE:",        date  ),
            (small, "MARQUE:", infdic["Marque"]),
            (small, "MODELE:", infdic["Modele"]),
            (small, "S/N:", infdic["NumeroSerie"]),
            (small, "SYSTEME:",      "Linux: " + infdic["Systeme"]),
            (small, "DISQUE:",       f'{infdic["DisqueType"]} {infdic["DisqueTaille"]} GB '),
            (small ,"MEMOIRE:",      f'{infdic["RAM"]}  GB '),
            (small, "CPU:",           f'{infdic["Processeur"]}'),
            (small ,"CPUMARK:",       f'{infdic["CPUMARK"]}'),
            (small, "BATTERIE:",      f'{infdic["Batterie"]}'),
            (big,   "CAT:",            Admin.categorie ),
            (small, ""            ,  ""),
            (small, "OBSERVATIONS:",  ""),
            (small, "",                 Admin.observations)
            ]

    #------------------------  avec qrcode format smarphone
    # le contenu sera interpétré par un script coté Salesforce . Donc format simple
    # texte du qrcode
    qrcodeitems= [Admin.ECID , infdic["NumeroSerie"] , Admin.categorie , infdic["Marque"], infdic["Modele"]]
    txtqrcode = "#".join( qrcodeitems )  #  IDENTIFIANT#NumeroSerie#Marque#Modele

    MakeRTF( items, txtqrcode ,filesmartphone ,TMPDISK )

    #------------------------  avec qrcode format douchette
    # le contenu correspond exactement aux champs coté database Salesforce . Donc formatage hyper complexe
    if Admin.categorie == "Premium":
        tmpcat = "Ordinateur - PREMIUM"
    else:
        tmpcat = f"Ordinateur - Catégorie {Admin.categorie}"

    patterns={ "Dell" : "Dell",  "Hewlett" : "HP"  , "ASUSTeK" : "Asus" , "Packard" : "Packard Bell" , "Essentiel" : "Essentiel B" , "Terra" : "Terra Mobile" , "Apple" : "Apple Mac"  }
    tmpmarque=infdic["Marque"]
    for key,value in patterns.items():
        tmp=tmpmarque.upper()
        if tmp.find( key.upper() ) > -1:
            tmpmarque=value
            break

    #catégorie + tabulation + tabulation + tabulation + tabulation + tabulation + tabulation + tabulation + marque + tabulation + tabulation + modèle + tabulation + tabulation + Identiant Emmaus-Connect + tabulation + numéro de série
    txtqrcode=f"{tmpcat}\t\t\t\t\t\t\t{tmpmarque}\t\t{infdic['Modele']}\t\t{Admin.ECID}\t{infdic['NumeroSerie']}"
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
def MakeBolc(infdic, filename):

    bolcdate=datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")  #impérativement format francais

    infosystem="Linux: " + infdic["Systeme"]

    items=    [
    Admin.idrecond,             # identifiant du  matériel chez le reconditionneur
    Admin.ECID,                # identifiant EmmausEC
    infdic["Type"],              # type de matériel (Portable, Fixe, Tablette)
    Admin.categorie,            # categorie  A B C D Premium INVENDABLE    
    Admin.bolcstatut,           # Prêt à vendre, En reconditionnement ...
    "",                         # commentaire statut . 
    infdic["Marque"],            # Marque: HP , Lenovo ...
    "",                         # Constructeur
    "",                         # Nom commercial
    infdic["Modele"],            # Modele ...
    infdic["Batterie"],          # % de batterie residuel ...
    "",                         # Date de vente
    Admin.observations,         # Observations
    infdic["NumeroSerie"],       # Numero de serie
    infdic["Processeur"],        # Type de Processeur
    infdic["DisqueType"],        # Type de disque HDD/SSD
    infdic["DisqueTaille"],      # Capacite disque
    "",                         # disk2 type
    "",                         # disk2 capacite
    infdic["RAM"],               # RAM
    "",                         # Info DVD
    infdic["Webcam"],            # Webcam présente ?
    infdic["Ecran"],             # Info taille ecran
    infdic["NoteTechnique"],     # Pondération technique
    infdic["NoteEsthetique"],    # Pondération esthetique
    infdic["CPUMARK"],           # Indice processeur
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

    _logger.info(f"Création de: {filename}")
    # newline="" est indispensable sous windows pour eviter que \n devienne CRLF
    with open(filename,"w",newline="") as f:
        f.write(txt + "\r\n")

#===========================================================================================
# Changement du statut Bolc
#
#  On prend le modele
#===========================================================================================
def BolcStatut():

    ecid=Ecid().Get()
    liststatut = list(tectech_data.allowed_values["statut"])
    dialog=Zdialog("Changement du Status Bolc",5,5)
    vbox=dialog.area
    Ztext( vbox , f"Identifiant: {ecid}")
    # Important de mettre une valeur initiale
    Zlistbox(dialog,  vbox, "STATUT", "Nouveau Statut", liststatut , "") 
    Zentry(dialog, vbox, "COMMENT", "Commentaire Statut: ","r","")
        
    boxactions= Zhbox(vbox,0,0)
    Zbutton(dialog, boxactions ,"QUIT", "QUITTER","Orange")
    Zbutton(dialog, boxactions ,"OK", "OK","Yellow")

    out=dialog.Run()
    #_logger.info(out)
    if out.get("OK","") == "" : return
    if out.get("STATUT","") == "" : return

    _logger.info("Nouveau statut: " + out["STATUT"])

    date= datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    site=ecid[0:2]
    filebolc  = os.path.join( TMPDISK , f"{site}-PORTABLE-{date}.csv" )

    with open( os.path.join( "modeles", "bolc.csv")  , "r" ) as f:
        data=f.read()
    keys=data.split(";")


    gooditems={ "id_pc" : ecid , "id_statutp" : out["STATUT"], "id_statutc" : out["COMMENT"] }
    bolcdata=[]
    for key in keys:
        value=gooditems.get( key , "" )
        value=value.replace(";",",")
        bolcdata.append(value)

    bolcdata=";".join( bolcdata)
    
    with open(  filebolc , "w" ) as f:
        f.write( bolcdata )

    TransfertTectech(filebolc)


#===========================================================================================
# Collecte des Tests Materiel
#
#  les informations sont mémorisées dans un fichier -caract.txt au format json
#===========================================================================================
class Caract:

    def __init__(self):
        self.file=os.path.join(TMPDISK,"-caract.txt")
        if os.path.isfile( self.file):
            with open(self.file,"r") as f:
                self.data = json.load(f)
        else:
            self.data={ }


    def Save(self,data):
        # global infos
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
        # col=0
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
class Ecid:

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
        return value

    def Init(self,value):
        self.Input(value)

    def Reset(self):
        if os.path.isfile(self.idfile) :  os.remove(self.idfile)        

    def Input(self, value: str):
        while not re.match( self.regexp , value.upper()):
            if value != "":
                msg=f"IDENTIFIANT emmaus incorrect: {value}"
            else:
                msg=""
            value=Zinputbox( "SAISIE IDENTIFIANT" , msg, "Entrer l'identifiant (exemple: GRPC25-9999) "  , value )
            if value == "" : break

        # if value == "" : sys.exit()
        self.Save(value.upper())
        return value.upper()


#------------------------------------------------------------------
# Download  un .zip si la version dans version.txt est inferieure à celle sur le serveur
#
#------------------------------------------------------------------
def ShowChange(*args):
    Browser("https://audits.emmaus-connect.org/api/apps/linux/changelog/web")

def UpdateMe():
    remotev, remotef, remoteu, remotes = GetRemoteVersionInfo()

    _logger.info(f"Vérification Versions: Local={__version__} Serveur={remotev}")
    if __version__ == "" or remotev == "":
        return

    # convert to (x, y, z) tuples that can be compared
    localvnew = tuple([int(_) for _ in __version__.split('.')])
    remotevnew = tuple([int(_) for _ in remotev.split('.')])

    if localvnew < remotevnew :

        dlg=Zdialog("Nouvelle version!")
        Ztext( dlg.area,f"Une version plus récente est disponible\n\tvotre version\t\t: {__version__}  \n  \tversion disponible\t: {remotev}")
        bbox=Zhbox(dlg.area)
        Zbutton(dlg,bbox,"QUIT","Ignorer","orange")
        Zbutton(dlg,bbox,"SHOW","Voir les évolutions","lightgreen", ShowChange)
        Zbutton(dlg,bbox,"GET","Télécharger","yellow")
        dlg.Run()
        exitcode=dlg.exitcode

        if exitcode in [ "QUIT" , "#QUIT" ] : return

        DWLDIR = get_user_dirs()["download"]

        dwnlfile = os.path.join(DWLDIR, remotef)
        _logger.info(f"\nTéléchargement de {remotef} vers {dwnlfile} en cours...\n")

        ret = DownloadFile(remoteu, dwnlfile, remotes)

        if ret != "SUCCESS":
            _logger.info(ret)
            if os.path.isfile(dwnlfile):
                os.remove(dwnlfile)
            sys.exit(1)

        chown_to_user(dwnlfile)
        _logger.info (f"Téléchargement de {dwnlfile} réussi!\n")
        sys.exit(0)


#==============================================================================
# Procedure d'Audit
#
#==============================================================================
def ProcessAudit(mini=False, useprodapi: bool = False, xfer=False, datestamp: str=""):
    _logger.debug(f"ProcessAudit({mini=}, {useprodapi=}, {xfer=}, {datestamp=})")
    _logger.debug(f"ProcessAudit: Ecid=>{Ecid().Get()}<")
    # exitiftest()

    Admin.ECID = Ecid().Get()

    # Audit du système et extraction des données
    _logger.info(f"Recherche des caractéristiques de l'équipement")
    infos=AuditMe(datestamp=datestamp)

    # Si le materiel est declaré comme tablette, on force le type
    if len(Admin.ECID) > 4 and Admin.ECID[2:4] == "TA":
        infos["Type"]= "Tablette"

    #_logger.info(infos)

    # Recherche de la note CPU
    proc = infos["Processeur"]
    # _logger.info(f"----------------- Recherche de la note du processeur {proc} ----------------------")
    cpumark = FindCpuMark(proc)
    _logger.info(f"La note >{cpumark}< a été trouvée pour >{proc}<")

    # Saisie d'infos complémentaires, y compris le cpumark si pas trouvé
    _logger.info("------------ Saisie manuelle d'informations --------------------")
    ManualTechInfos(infos,cpumark)

    _logger.info("------- Informations trouvées (mémoire en Gio, disques en Go) -------")
    for key,value in infos.items():
        _logger.info(f"{key:<20}: {value}")

    if infos["DisqueType"] == "SSD":
        ouinon = "NVME" if infos.get("NVME") == "oui" else "ATA"
    else:
        ouinon = "N/A"
    _logger.info(f"{'NVME/ATA':<20}: {ouinon}")

    #_logger.info(json.dumps( infos, sort_keys=False, indent=4))






    _logger.info("----------------- Calcul des notes  ----------------------")

    tmptxtnotes=[]
    sectionnote="#NOTE-" + OSTARGET.upper()  
    note = ComputeNote( infos, CSVREGLES, sectionnote, tmptxtnotes )

    Admin.notebrut= note
    Admin.txtnotes = tmptxtnotes

    Admin.notenet=ComputeNoteModif( infos, CSVREGLES, "#MODIF" , Admin.txtnotes, Admin.notebrut )

    _logger.info( ", ".join(Admin.txtnotes)  )

    _logger.info(f"Note finale={Admin.notenet}")

    Admin.categorie=ComputeCategorie( CSVREGLES,Admin.notenet)
    _logger.info(f"Categorie={Admin.categorie}")

    #------------------- affichage rapide ------------------------
    filename=os.path.join( TMPDISK , "infos.txt")
    MakeRapport(infos, filename, header=False, details=True )
    Editor( filename )  # this editor window is a pain in the neck

    # si Mini Audit , pas d'envoi ....
    if mini : return

    # Sasie des manuelle des informations
    time.sleep(1)  # Evite que l'affichage rapide arrive après la boite de dialogue
    result=ManualAdminInfosIHM(infos, "Saisie des informations administratives")
    # si on n'a pas cliqué OK, les informations saisies sont invalides, et peuvent provoquer bugs
    if result.get("OK","") == "" : return 

    #_logger.info(result)
    Admin.nomcomm=result["nomcomm"]
    Admin.benevole=result["benevole"]
    Admin.observations=result["observations"]
    Admin.bolcstatut = tectech_data.external_to_internal_snames[result["bolcstatut"]]
    Admin.idrecond=result["idrecond"]
    Admin.origine=result["origine"]
    Admin.iddonlot=result["iddonlot"]


    _logger.info("----------------- Création et envoi des fichiers vers audits.emmaus-connect.org et tec.tech ----------------------")
    if datestamp:
        # we are making a (reasonable) assumption about how 'datestamp' is formated
        Admin.auditdate = time.strftime("%d/%m/%Y %H:%M:%S", datetime.datetime.strptime(datestamp, _DSFMT).timetuple())
    else:
        datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    MakeSendFiles(infos, useprodapi, xfer)

#--------------------------------------------------------------------
# Demande de passwd sur Linux
#--------------------------------------------------------------------
def GetPasswd():
    if "ZZZEMMAUS" in os.environ: return

    pwd=Zinputbox( "Saisie Mot de Passe","","           Entrer le mot de passe              ","")
    if pwd != "":
        os.environ[ "ZZZEMMAUS" ] = pwd


#=============================== Main ==============================
def signal_handler(sig, frame):
    _logger.info(f"Caught signal {sig} ({signal.strsignal(sig)}). Exiting...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Se positionne sur le drive/directory du script principal
ChdirScript()

# vérifier l'existence d'une version plus récente, signaler, etc.
UpdateMe()


def old_parsing() -> (bool, bool, bool):
    # The existing parameter handling is not compatible with an argparse-based parsing, so we continue playing with
    # sys.argv without striving for elegance or efficiency...

    # The accepted parameter list styles are:
    #   python3 -B audit.py                         # [1] id will we requested, PROD is implied
    #   python3 -B audit.py GRPC26-0043             # [2] PROD is implied
    #   python3 -B audit.py [PROD|TEST]             # [3] id will we requested
    #   python3 -B audit.py GRPC26-0043 [PROD|TEST] # [4] works with tec.tech (case-insensitive)
    # _logger.level = logging.DEBUG
    _logger.info(sys.argv)
    prod_or_test_ = ["PROD", "TEST"]
    n_ = len(sys.argv) - 1
    nopc = None
    useprodapi = True
    mini = False
    if n_ == 0:  # [1]
        _logger.debug("Aucun paramètre ==> Audit sans transferts")
        nopc = True
        mini = True
    elif n_ == 1:
        _logger.debug("Un seul paramètre: soit un idEsn, soit PROD|TEST")
        if sys.argv[1].upper() not in prod_or_test_:  # [2]
            Ecid().Init(sys.argv[1].upper())
            nopc = False
        else:  # [3]
            _logger.debug("Uniquement choix PROD|TEST")
            useprodapi = sys.argv[1].upper() == "PROD"
    elif n_ == 2:  # [4]
        _logger.debug("Deux paramètres ==> idEsn + PROD|TEST")
        Ecid().Init(sys.argv[1].upper())
        nopc = False
        useprodapi = sys.argv[2].upper() == "PROD"
    else:
        _logger.error("Paramètres incorrects. Abandon...")
        sys.exit(1)

    _logger.info(f"{nopc = }")

    return nopc, mini, useprodapi

def print_version_info() -> None:
    print(f"{__about__.__title__}")
    print(f"Version: {__about__.__version__}")
    print("Développé par:")
    for a in __about__.__authors__:
        print(f"  {a['versions']}: {a['name']} ({a['email']})")
    print(f"Copyright: {__about__.__copyright__}")

def check_idesn(val):
    __esnspat = "|".join(sorted(list(tectech_data.esn_to_idstock.keys())))
    __crexp = re.compile(fr'^(?P<esn>({__esnspat}))(?P<typ>(PC|TA))' + r'(?P<ann>(\d{2}))-(?P<num>(\d{4}))$', re.ASCII)
    m = re.match(__crexp, val.upper())
    if not m:
        raise argparse.ArgumentTypeError(f"{val} n'est pas un idEsn valide")
    return val

def exitiftest():
    # sys.exit(0)
    return


if __name__ == '__main__':

    if not [_ for _ in sys.argv if _.startswith('-')]:
        _logger.debug("Old-style parameter parsing")
        _logger.debug(f"{len(sys.argv)}, {sys.argv=}")
        nopc_, mini_, useprodapi_ = old_parsing()
        # exitiftest()
        ProcessAudit(mini=mini_, useprodapi=useprodapi_, datestamp=DATESTAMP)

    else:
        _logger.debug("Modern-style parameter parsing")

        class myHelpFormatter(argparse.RawDescriptionHelpFormatter):  # argparse.ArgumentDefaultsHelpFormatter):
            pass

        class MyFormatter(argparse.RawDescriptionHelpFormatter, argparse.MetavarTypeHelpFormatter):
            pass


        description_ = "\n====================================="
        description_ += f"\nProgramme d'audit de PC Linux - {__about__.__version__}"
        description_ += "\n====================================="

        epilog_ =  "\n=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*"
        epilog_ += "\nL'ancien style de passage de paramètres est encore admis, mais en voie d'obsolescence."
        epilog_ += "\nPour mémoire, voici quelques exemples de commandes valides:"
        epilog_ += "\n  sudo bash audit.sh              # mini-audit: sans transferts"
        epilog_ += "\n  sudo bash audit.sh GRPC26-0043  # audit normal: avec envoi vers les serveurs"

        epilog_ += "\n======================================================================================"

        parser_ = argparse.ArgumentParser(description=description_, epilog=epilog_,
                                          add_help=False, usage=argparse.SUPPRESS,
                                          formatter_class=MyFormatter)

        ghelp_ = parser_.add_argument_group("Obtenir de l'aide")  # , "Audit puis transferts vers base d'audtis et tec.tech")

        ghelp_.add_argument("-h", "--help", default=False, action='store_true',
                             help="Afficher le message d'aide")

        gfull_ = parser_.add_argument_group("Usage standard", "Audit puis transferts vers base d'audits et tec.tech")

        gfull_.add_argument("-i", "--idesn", type=check_idesn, required=False, metavar='eePCaa-nnnn',
                             help="Identifiant ESN du PC à traiter" 
                                  f"(ee dans {{{', '.join(sorted(list(tectech_data.esn_to_idstock.keys())))}}})")

        gfull_.add_argument("-t", "--test", default=False, action='store_true',
                             help="Utiliser la base tec.tech de test (optionnel - base prod par défaut)")

        gmini_ = parser_.add_argument_group("Mini-audit")  # , "Mini-audit seul")

        gmini_.add_argument("-m", "--mini", default=False, action='store_true',
                             help="Réaliser un audit sans identifier le PC et quitter")

        gvers_ = parser_.add_argument_group("Information")  # , "Information de version")

        gvers_.add_argument("--version", default=False, action='store_true',
                             help="Afficher les informations détaillées de version et quitter")

        args_ = parser_.parse_args()
        nopc_ = False  # not very sure about this one...
        _logger.debug(f"{args_=}")

        if args_.version:
            print_version_info()
            sys.exit(0)

        if args_.help:
            parser_.print_help()
            sys.exit(0)

        if args_.mini:
            _logger.debug("Running mini-audit")
            # exitiftest()
            ProcessAudit(mini=True, useprodapi=not args_.test, datestamp=DATESTAMP, xfer=False)
        else:
            _logger.debug("Running normal audit")
            Ecid().Init(args_.idesn.upper())
            # exitiftest
            ProcessAudit(mini=False, useprodapi=not args_.test, datestamp=DATESTAMP)

    sys.exit(0)

    # Si exécution directe, attendre RETURN  ( pour ne pas perdre l'affichage )
    # if nopc_:
    #     Zinputbox("**FIN**" , "                           Fin de l'audit!                          ")

    # global infos
    # _logger.info(infosdict)
    # _logger.info(f"infos = {infosdict}")

    # _logger.info(f"Liste des symboles globaux")
    # globals_as_str_ = {k: str(globals()[k]) for k in globals()}
    # o_ = "List of globals:"
    # for k_ in globals_as_str_:
    #     o_ += f"\n{k_:<32}: {globals_as_str_[k_]}"
    # _logger.info(o_)
    # _logger.info(globals())

