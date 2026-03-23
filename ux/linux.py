###################################################################################
#
# Actions techniques pour l'Audit Linux
#
#
# Utilisation:
#  import linux.py
#  infos=AuditMe()
#
#
##################################################################################

import os
import subprocess
import re
import sys

from common import *

TMPDISK="/tmp"                                  # répertoire où sont générés les fichiers temporaires.  

FILESCAN="scan-linux.txt"                        # fichier contenant le scan système qu'on copie sur drop.tf
OSTARGET="Linux"                                # Utilisé pour trouver kes règles dans regles.csv , et comme suffixe pour DecouverteMonPC
   
TMPSCANFILE=os.path.join( TMPDISK ,  "scan-linux.txt")           # fichier d'export de la commande inxi
# print(f"FILESCAN={FILESCAN}")
# print(f"TMPSCANFILE={TMPSCANFILE}")

# Variables globales
inxidata={}  
infos={}  # donnees technique issues du scan systeme

#------------------------------------------
# Lance les outils système de scan
#------------------------------------------
def SystemScan(inxifile):

    # cmd=f"(sudo    inxi -F -xx -y1) > {inxifile}"
    # os.system(cmd)
    result = subprocess.run(["sudo", "inxi", "-F", "-xx", "-y1", "--color", "0"], capture_output=True, text=True)
    with open(f"{inxifile}", "w") as f:
        f.write(result.stdout)

    pass


#------------------------------------------
# Execute l'audit technique : lancement du scan, decodage 
#  renvoie infos : dictionnaire de valeurs
#------------------------------------------
from ux.characteristics import get_machine_infos
def AuditMe():
    infostmp =  get_machine_infos()
    print(infostmp)
    SystemScan(TMPSCANFILE)  # keep those legacy parts around for now
    unusedDecodeInxi(TMPSCANFILE)
    unusedAnalyzeInxi()  # will update the global variable "infos"
    t = [(_, infos[_], infostmp[_]) for _ in infos if infos[_] != infostmp[_]]
    for _ in t:
        print(_)
    return infostmp



#------------------------------------------
# renvoie le nb d'espaces au début d'un texte
#------------------------------------------
def unusedNbspace(txt):
    # raise RuntimeError
    nb=0
    for c in txt:
        if c == " " : nb=nb+1
        else: return nb

    return nb

#------------------------------------------
# analyse une ligne de inxi, indentée
#
# renvoie [ indent, key , value ]
#
# La 1e indentation observée, permet de définir le nb d'espaces de l'indentation
#-------------------------------------------
unusedIndentvalue=0
def unusedInxiLine(txt) :
    # raise RuntimeError
    global unusedIndentvalue
    indent=unusedNbspace(txt)
    if indent != 0 and unusedIndentvalue==0 : unusedIndentvalue = indent # memoriser la largeur de la 1e indentation
    if unusedIndentvalue != 0: indent = indent / unusedIndentvalue # avoir des valeurs de 1  en 1

    txt = txt.strip()
    ( key, value ) = txt.split(":" , 1)
    value=value.strip()
    return [ indent,key,value]

#------------------------------------------------------
# Analyse un fichier inxi -y1
# L'indentation définit la structure de données
#
# Systeme:
#    Distro: LMDE 6 Faye
#      base: Debian 12.1 bookworm
#
# devient:
#     { "System":
#        "#" : "",
#        "Distro": {
#            "#": "LMDE 6 Faye",
#            "base": {
#                    "#": "Debian 12.1 bookworm"
#                    }
#    }   
#
# "#" sert à stocker le nom d'un niveau
#
# INPUT
#   inxifile : nom du fichier inxi
# RETURN
#   structure de données
#----------------------------------------------------               
def unusedDecodeInxi(inxifile):
    # raise RuntimeError
    global inxidata
    data={}
    stack={}
    for i in range(0,10): stack[i]=""
    level=0

    # durant l'analyse , 
    # - level contient le niveau d'indentation
    # - stack[level] conitient l'endroit où on stocke la donnée lue  
    stack[0]= inxidata

    items=[]
    # errors=ignore permet de survivre au cas où le fichier inxi n'est pas utf-8 ( presence de \x00 dans les infos batterie
    with open(inxifile,'r',errors='ignore') as f:
        for line in f:
            if line.strip("\n ") != "" :
                items.append(unusedInxiLine(line))

    for item  in items:
        (level,key,value) = item
        stack[level][key]={ "#" : value }
        stack[level+1] = stack[level][key]



#-------------------------------------------------------
# Renvoie la structure correspondant à un chemin comme
#  "Machine/System/product"
# USAGE INTERNE
#-------------------------------------------------------
def unusedInxiData(txt):
    # raise RuntimeError
    global inxidata

    items=txt.split("/")
    data=inxidata
    for item in items:
        if item in data :
            data=data[item]

        else:
            return {}

    return data

#-------------------------------------------------------
# Renvoie la valeur  associée à un bloc data 
#
# pour cela, on lit la clé "#"
#-------------------------------------------------------
def unusedInxiDataValue(data) :
    # raise RuntimeError
    if "#" in data:
        return data["#"]
    else:
        return ""

#-------------------------------------------------------
# Renvoie la valeur  associée à un chemin comme
#  "Machine/System"
# pour cela, on lit la clé "#"
#-------------------------------------------------------
def unusedInxiValue(txt) :
    data= unusedInxiData(txt)
    if "#" in data:
        return data["#"]
    else:
        return ""

#-------------------------------------------------------
# Renvoie les sous bloc associés à un chemin comme
#  "Machine/System"
# pour cela, on renvoie toutes les cles sauf "#"
#-------------------------------------------------------
def unusedInxiItems(txt) :
    # raise RuntimeError
    data= unusedInxiData(txt)
    newdata={}
    for key,value in data.items():
        if key != "#" :
            newdata[key] = value
    return newdata

#-----------------------------------------------------------
# Extrait les infos utiles de inxi
#
# retourne un dictionnaire des rubriques utiles
#
# !!! Entre inxi 3.3.26 de LMDE6  et inxi 3.3.34 de MINT22.1 le nom et le format des rubriques change !
#
# INPUT
# RETURN
#  liste { clé , valeur } 
#-----------------------------------------------------------
def unusedAnalyzeInxi():
    # raise RuntimeError
    global infos

    infos={}

    # Conversion de type : le BOLC ignore ce qui n'est pas UC / Portable'
    # Soit l'os installé est Windows ou Linux et dans ce cas il est considéré comme UC / Portable
    # Soit l'os installé est android ou IOS  et dans ce cas il est considéré comme une tablette,
    type=unusedInxiValue("Machine/Type")
    if type.lower() in ( "desktop" , "mini-pc" )  : type = "UC"
    else:                                           type = "Portable"
    infos["Type"]= type
   
    infos["Marque"]=unusedInxiValue("Machine/System")
    infos["Modele"]=unusedInxiValue("Machine/System/product")
    infos["NumeroSerie"]=unusedInxiValue("Machine/System/product/serial")

    infos["Processeur"]=unusedInxiValue("CPU/Info/model")

    infos["Systeme"]=unusedInxiValue("System/Distro")

    infos["LINUX"]="oui"                                        # valeur forcee


    # Memoire : suivant la version,  se trouve dans Memory ou Memory/total
    ram=unusedInxiValue("Info/Memory")
    if ram == "" : ram=unusedInxiValue("Info/Memory/total")
    # print(f"ram = {ram}")
    if m := re.match(r'^(?P<siz>(\d+))\s+(?P<unt>(GiB|Gio))', ram, re.IGNORECASE):
        infos['RAM'] = int(m['siz'])
    else:
        # fallback: legacy code
        infos["RAM"]= round(unusedDecodeNumber(ram))
    # print(f"infos['RAM'] = {infos['RAM']}")

    # Batterie:    "condition": "73.3/80.0 Wh (91.6%) 
    # on  récupère le pourcentage residuel  
    battery =""

    # il se peut, que Inxi renvoie rien sur battery
    for key,data in unusedInxiItems("Battery").items():
        tmp=unusedInxiValue(f"Battery/{key}/condition")
        if tmp != "":
    	    tmp=tmp.split(" ")
    	    tmp=tmp[-1]   # dernier element
    	    battery=tmp.replace( "(" , "" ). replace( ")","")  # supprimer parentheses

    infos["Batterie"]=battery

    # Taille ecran  Graphics/Display/Screen-x/Monitor-x/diag
    ecran=""
    for key,data in unusedInxiItems("Graphics/Display").items():
        for k, monitor in unusedInxiItems(f"Graphics/Display/{key}").items():
            if k.startswith("Monitor-") and "diag" in monitor:
                v=unusedInxiDataValue(monitor["diag"])
                items=v.split(" ")
                ecran=items[-1]
                ecran=ecran.replace("(","").replace(")","").replace('"',"")

    # Webcam( pas forcément fiable )  
    webcam=""
    for key,data in unusedInxiItems("Graphics").items():
        if key.startswith("Device-" ):
            txt=unusedInxiDataValue(data).lower()
            if txt.find("camera") > -1 or txt.find("webcam") > -1 :
                webcam="oui"

    infos["Ecran"]=ecran
    infos["Webcam"]=webcam

    # Disques
    # Il ne faut creer infos["NVME"] que si nvme est détecté !  Car son existence sert à exécuter une règle de calcul de points
    sizedisk=0
    typedisk=[]

    diskid=""
    for key, elem in unusedInxiItems("Drives").items():
        if key.startswith("ID-" )and "size" in elem:

            # oublier les cle USB, qui apparaissent avec type=USB
            if "type" in elem:
                if unusedInxiDataValue(elem["type"]).upper() == "USB": continue

            # Le 1e drive donne le diskID du system
            if diskid=="":
                diskid=unusedInxiDataValue(elem)

            # ajouter la taille disque
            s=unusedInxiDataValue(elem["size"])
            print(f"partial sizedisk = {unusedDecodeNumber(s)} GB/Go")
            # we want to keep disk sizes in GB (not GiB) because that's how they are advertised
            sizedisk = sizedisk + round(unusedDecodeNumber(s))

            # si le disque est nvme , on a une pattern comme id=/dev/nvme0n1
            if diskid.find("nvme") > -1 :
                infos["NVME"]="oui"

            # modele de disque
            if "model" in elem:
                typedisk.append(unusedInxiDataValue(elem["model"]))

    print(f"sizedisk = {sizedisk} GB/Go")
    infos["DisqueTaille"] = sizedisk  # round(sizedisk)
    infos["DisqueRef"]= ",".join(typedisk)
    infos["DisqueID"]=diskid

    infos["DisqueType"] = unusedDetectDiskType(diskid)


#----------------------------------------------------------------------
# Detecte si un disque est HDD ou SSD
# 
# INPUT:
#  diskid:  nom du drive  (/dev/nvmen0  /dev/sda ....)
#
# RETURN:  "HDD" ou "SSD"  ou "" s'il n'arrive pas à déterminer
#
# ATTENTION: ça dit n'importe quoi pour les clé usb !
#----------------------------------------------------------------------
def unusedDetectDiskType(diskid):
    # raise RuntimeError
    tmp=diskid.split("/")
    device=tmp[-1]
    fileinfo=f"/sys/block/{device}/queue/rotational"
    if not os.path.isfile(fileinfo) : return ""

    with open( fileinfo , "r" ) as f:
        txt=f.read()

    if len(txt) == 0 : return ""

    code = txt[0]
    if code == "1" : return "HDD"
    if code == "0" : return "SSD"
    return ""

#-----------------------------------------------------------
# Copie une liste de fichiers/répertoires sur le Bureau
#   renvoie False si bureau pas trouvé
#
#-----------------------------------------------------------
def Copy2Desktop(files):

    print(f"Copy2Desktop({files = })")
    BUREAU=""
    insudo = False
    if suu := os.environ.get("SUDO_USER"):
        insudo = True
        enduserrootdir = f"/home/{suu}"
        enduseruid = int(os.environ.get("SUDO_UID"))
        endusergid = int(os.environ.get("SUDO_GID"))
    else:
        enduserrootdir = os.environ.get("HOME")
        enduseruid = -1
        endusergid = -1

    for b in [ "Bureau" ,"Desktop"]:
        bname = os.path.join(enduserrootdir, b)
        if os.path.isdir(bname):
            BUREAU = bname

    print(f"{BUREAU=}, {insudo=}, {enduserrootdir=}, {enduseruid=}, {endusergid=}")
    if BUREAU != "":
        for name in files:
            dst = os.path.join(BUREAU, name)
            if os.path.isfile(name):
                CopyFile(name, BUREAU)
                if insudo:
                    cmd = f"chown {enduseruid}:{endusergid} {BUREAU}{os.sep}{os.path.basename(dst)}"
                    print(cmd)
                    os.system(cmd)
            if os.path.isdir(name):
                CopyDir(name, BUREAU)
                if insudo:
                    cmd = f"chown -R {enduseruid}:{endusergid} {dst}"
                    print(cmd)
                    os.system(cmd)
    else:
        return False

    return True



def CopyFile2File( src, dst):
    os.system( f"cp {src} {dst}" )

def CopyFile( src, dstdir):
    os.system( f"rsync {src} {dstdir}/" )

def CopyDir( src, dstdir):
    os.system( f"rsync -r {src} {dstdir}/" )

def unusedConvertFile(name):
    return name


if  __name__ == "__main__":
    infos_ = AuditMe()

    # myscan_ = "/home/ghalebp/tmp/linux-bernard-maison-to-tec.tech/MAPC26-0019/MAPC26-0019.scan-linux.txt"
    # DecodeInxi( myscan_)
    # AnalyzeInxi()
    # infos_ = infos
    # infos_ = get_machine_infos()

    sys.exit(0)
