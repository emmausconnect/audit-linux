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
from outils import *

TMPDISK="/tmp/"                                 # répertoire où sont générés les fichiers temporaires.  DOIT être terminé par /
TMPSCANFILE=TMPDISK+ "scan-linux.txt"           # fichier d'export de la commande inxi
FILESCAN="scan-linux.txt"                        # fichier contenant le scan système qu'on copie sur drop.tf
OSTARGET="Linux"                                # Utilisé pour trouver kes règles dans regles.csv , et comme suffixe pour DecouverteMonPC
     
# directory separateur
DIRSEP="/"

# Curl prefix/suffix
P="$"
S=""
CURL="curl"
       
# Variables globales
inxidata={}  
infos={}  # donnees technique issues du scan systeme

#------------------------------------------
# Lance les outils système de scan
#------------------------------------------
def SystemScan(inxifile):

    cmd=f"(sudo    inxi -F -xx -y1) > {inxifile}"
    os.system(cmd)


#------------------------------------------
# Execute l'audit technique : lancement du scan, decodage 
#  renvoie infos : dictionnaire de valeurs
#------------------------------------------
def AuditMe():
    if "noscan" not in sys.argv or not os.path.isfile(TMPSCANFILE) :
        print( f"===================== Lancement du scan système (inxi) .  Creation de {TMPSCANFILE} ===============" )
        SystemScan(TMPSCANFILE)

    print( f"===================== Décodage des infos système depuis {TMPSCANFILE} ===============" )
    DecodeInxi( TMPSCANFILE )
    AnalyzeInxi()
    return infos




#------------------------------------------
# renvoie le nb d'espaces au début d'un texte
#------------------------------------------
def Nbspace(txt):
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
indentvalue=0
def InxiLine(txt) :
    global indentvalue
    indent=Nbspace(txt)
    if indent != 0 and indentvalue==0 : indentvalue = indent # memoriser la largeur de la 1e indentation
    if indentvalue != 0: indent = indent / indentvalue # avoir des valeurs de 1  en 1

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
def DecodeInxi( inxifile ):
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
                items.append( InxiLine(line) )

    for item  in items:
        (level,key,value) = item
        stack[level][key]={ "#" : value }
        stack[level+1] = stack[level][key]



#-------------------------------------------------------
# Renvoie la structure correspondant à un chemin comme
#  "Machine/System/product"
# USAGE INTERNE
#-------------------------------------------------------
def InxiData( txt ):
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
def InxiDataValue( data ) :
    if "#" in data:
        return data["#"]
    else:
        return ""

#-------------------------------------------------------
# Renvoie la valeur  associée à un chemin comme
#  "Machine/System"
# pour cela, on lit la clé "#"
#-------------------------------------------------------
def InxiValue( txt ) :
    data= InxiData( txt )
    if "#" in data:
        return data["#"]
    else:
        return ""

#-------------------------------------------------------
# Renvoie les sous bloc associés à un chemin comme
#  "Machine/System"
# pour cela, on renvoie toutes les cles sauf "#"
#-------------------------------------------------------
def InxiItems( txt ) :
    data= InxiData( txt )
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
def AnalyzeInxi():
    global infos

    infos={}

    # Conversion de type : le BOLC ignore ce qui n'est pas UC / Portable'
    # Soit l'os installé est Windows ou Linux et dans ce cas il est considéré comme UC / Portable
    # Soit l'os installé est android ou IOS  et dans ce cas il est considéré comme une tablette,
    type=InxiValue("Machine/Type")  
    if type.lower() in ( "desktop" , "mini-pc" )  : type = "UC"
    else:                                           type = "Portable"
    infos["Type"]= type
   
    infos["Marque"]=InxiValue("Machine/System")
    infos["Modele"]=InxiValue("Machine/System/product")
    infos["NumeroSerie"]=InxiValue("Machine/System/product/serial")

    infos["Processeur"]=InxiValue("CPU/Info/model")

    infos["Systeme"]=InxiValue("System/Distro")

    infos["LINUX"]="oui"                                        # valeur forcee


    # Memoire : suivant la version,  se trouve dans Memory ou Memory/total
    ram=InxiValue("Info/Memory")
    if ram == "" : ram=InxiValue("Info/Memory/total")
    infos["RAM"]= round( DecodeNumber( ram ) )

    # Batterie:    "condition": "73.3/80.0 Wh (91.6%) 
    # on  récupère le pourcentage residuel  
    battery =""

    # il se peut, que Inxi renvoie rien sur battery
    for key,data in InxiItems("Battery").items():
        tmp=InxiValue(f"Battery/{key}/condition" )
        if tmp != "":
    	    tmp=tmp.split(" ")
    	    tmp=tmp[-1]   # dernier element
    	    battery=tmp.replace( "(" , "" ). replace( ")","")  # supprimer parentheses

    infos["Batterie"]=battery

    # Taille ecran  Graphics/Display/Screen-x/Monitor-x/diag
    ecran=""
    for key,data in InxiItems("Graphics/Display").items():
        for k, monitor in InxiItems(f"Graphics/Display/{key}").items():
            if k.startswith("Monitor-") and "diag" in monitor:
                v=InxiDataValue( monitor["diag" ] )
                items=v.split(" ")
                ecran=items[-1]
                ecran=ecran.replace("(","").replace(")","").replace('"',"")

    # Webcam( pas forcément fiable )  
    webcam=""
    for key,data in InxiItems("Graphics").items():
        if key.startswith("Device-" ):
            txt=InxiDataValue( data ).lower()
            if txt.find("camera") > -1 or txt.find("webcam") > -1 :
                webcam="oui"

    infos["Ecran"]=ecran
    infos["Webcam"]=webcam

    # Disques
    # Il ne faut creer infos["NVME"] que si nvme est détecté !  Car son existence sert à exécuter une règle de calcul de points
    sizedisk=0
    typedisk=[]

    diskid=""
    for key, elem in InxiItems( "Drives" ).items():
        if key.startswith("ID-" )and "size" in elem:

            # oublier les cle USB, qui apparaissent avec type=USB
            if "type" in elem:
                if InxiDataValue( elem["type"] ).upper() == "USB": continue

            # Le 1e drive donne le diskID du system
            if diskid=="":
                diskid=InxiDataValue( elem )

            # ajouter la taille disque
            s=InxiDataValue( elem["size"] )
            sizedisk=sizedisk + DecodeNumber( s )

            # si le disque est nvme , on a une pattern comme id=/dev/nvme0n1
            if diskid.find("nvme") > -1 :
                infos["NVME"]="oui"

            # modele de disque
            if "model" in elem:
                typedisk.append( InxiDataValue(elem["model"]) )

    infos["DisqueTaille"]=round(sizedisk)
    infos["DisqueRef"]= ",".join(typedisk)
    infos["DisqueID"]=diskid

    infos["DisqueType"] = DetectDiskType( diskid )


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
def DetectDiskType(diskid):
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

    BUREAU=""
    for b in [ "Bureau" ,"Desktop"]:
        bname=os.path.join(  os.environ["HOME"] , b )
        if os.path.isdir(bname):  BUREAU=bname

    if BUREAU != "" :
        for name in files:
            if os.path.isfile(name) : 
                CopyFile( name , BUREAU )
            if os.path.isdir(name):
                CopyDir( name , BUREAU )
    else:
        return False

    return True



def CopyFile2File( src, dst):
    os.system( f"cp {src} {dst}" )

def CopyFile( src, dstdir):
    os.system( f"rsync {src} {dstdir}/" )

def CopyDir( src, dstdir):
    os.system( f"rsync -r {src} {dstdir}/" )

def ConvertFile(name):
    return name

