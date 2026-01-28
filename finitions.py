
import json
import re
import sys
import datetime
import os
import time

from outils import *


#--------------------------------------------------------
# renvoie le nom du Bureau
#   "" si pas trouvé
#--------------------------------------------------------
def GetBureau():
    HOME = os.environ["HOME"]

    for b in [ "Bureau" ,"Desktop"]:
        bname=os.path.join(  HOME , b )
        if os.path.isdir(bname):  return bname

    return ""


#--------------------------------------------------------
# Ajout de liens dans la barre des taches
#--------------------------------------------------------
def MajBarre():
    print("\n➡️ Modification de la barre des tâches")
    if MajBarre2():
        print("      ⚠️ Ne sera effectif qu'après déconnection / reboot ")
    else:
        print("  ❗️Modification impossible")

def MajBarre2():

    links=[ "libreoffice-writer.desktop","libreoffice-calc.desktop" ]

    HOME = os.environ["HOME"]
    dirs=[".config/cinnamon/spices" , ".cinnamon/configs" ]  # difference LMDE6 LMDE7
    fileconf=""
    for zedir in dirs:
        testfile=  os.path.join( HOME, zedir , "grouped-window-list@cinnamon.org/2.json" )
        if  os.path.isfile( testfile): fileconf=testfile

    if fileconf == "":
        print("❗️Fichier de configuration non trouvé !")
        return False

    with open(fileconf,"r") as f:
        data=json.load(f)

    section="pinned-apps"
    if section not in data:
        print(f"  Section {section} non trouvée")
        return False

    items=data[section]["value"]
    for link in links:
        if link not in items:
            items.append( link  )
    data[section]["value"]=items

    txt=json.dumps( data , indent=4)
    outfile=fileconf
    with open( outfile , "w") as f:
        f.write(txt)
    return True

def MajMenu():

    items=[
        "background-menu-create-new-folder", 
        "background-menu-open-as-root", 
        "background-menu-open-in-terminal", 
        "background-menu-paste", 
        "background-menu-properties", 
        "background-menu-scripts", 
        "background-menu-show-hidden-files", 

        "desktop-menu-customize", 

        "iconview-menu-arrange-items", 


        "iconview-menu-organize-by-name",
        "selection-menu-copy-to",
        "selection-menu-copy",
        "selection-menu-cut",
        "selection-menu-duplicate",
        "selection-menu-favorite",
        "selection-menu-make-link",
        "selection-menu-move-to",
        "selection-menu-move-to-trash",
        "selection-menu-open-as-root",
        "selection-menu-open-in-new-tab",
        "selection-menu-open-in-new-window",
        "selection-menu-open-in-terminal",
        "selection-menu-open",
        "selection-menu-paste",
        "selection-menu-pin",
        "selection-menu-properties",
        "selection-menu-pin",
        "selection-menu-rename",
        "selection-menu-scripts"
    ]

    print("\n➡️ Modification du menu contextuel")

    for item in items:
        cmd=f"gsettings set org.nemo.preferences.menu-config {item} true"
        os.system(cmd)


def MajBureau():

    items=[
        "trash-icon-visible", 
        "home-icon-visible"
        ]

    files=["Téléchargements","Documents"]

    print("\n➡️ Ajout des icônes et liens sur le Bureau")

    HOME=os.environ["HOME"]

    # Creation d'icones sur le bureau
    for item in items:
        cmd=f"gsettings set org.nemo.desktop {item} true"
        os.system(cmd)

    # Creation de liens sur le Bureau
    BUREAU=GetBureau()
    if BUREAU == "" : return
    
    for name in files:
        filename=os.path.join(HOME,name)
        target=os.path.join(BUREAU,name)

        #print(name, filename,os.path.isdir(filename) )
        if os.path.exists(filename) and not os.path.exists(target): 
            print( f"Création lien {target} => {filename}" )
            #os.symlink(target,filename)
            os.system(f"ln -s {filename} {BUREAU}")

def MajFirefox():
    MajFirefoxParams()
    MajFirefoxExtensions()

#------------ Paramètres
def MajFirefoxParams():
    print("\n➡️ Firefox: Modification de paramètres ( s'il n'a pas déjà tourné )")

    HOME=os.environ["HOME"]
    print("   👉 Modification des paramètres Firefox ")
    PrepareSudo()
    fileauto=os.path.join("modeles","autoconfig.js")
    dirpref="/opt/firefox/defaults/pref"
    if not os.path.isdir(dirpref):
        os.system(f"sudo mkdir -p {dirpref}")

    # possibilité de prendre firefox.cfg dans un repertoire spécifique à l'esn
    fileconf=os.path.join("esn","firefox.cfg")
    if os.path.isfile(fileconf):
        print(f"       !!! Utilisation du fichier de configuration spécifique au site: {fileconf}")
    else:
        fileconf=os.path.join("modeles","firefox.cfg")
    target=os.path.join("/opt/firefox","firefox.cfg")

    # Detection du profil
    profiledir= os.path.join(HOME,".mozilla","firefox")
    if os.path.isdir(profiledir):
        print(f"   ⛔️ Firefox a déjà été lancé. Pour que les modifications s'appliquent,il faut le réinitialiser")
        print(f"      ( fermer Firefox , détruire {profiledir} , relancer Firefox\n" )

    os.system(f"sudo cp {fileauto} {dirpref}" )
    os.system(f"sudo cp {fileconf} {target}" )

def MajFirefoxExtensions():
   
    # Extensions
    print("\n➡️ Firefox: installation Ublock-origin")
    PrepareSudo()  
    target="/opt/firefox/distribution/policies.json"
    source="modeles/autoconfig.json"
    tmpjson="/tmp/policies.json"

    if not os.path.isfile(target): return
        
    with open( target) as f:
        data = json.load(f)

    with open( source) as f:
        datasource = json.load(f)

    for key,value in datasource["policies"].items() :
        data["policies"][key]=value
    txt=json.dumps( data , indent=4)
    with open( tmpjson , "w") as f:
        f.write(txt)
    os.system( f"sudo cp {tmpjson} {target}")

#------------------------------------------------------------
# teste si un executable existe
#------------------------------------------------------------
def TestAppli(name):
    code=os.system(f"command -v {name} > /dev/null" )
    if code == 0: return True
    else: return False

def MajApplis():
    print("\n➡️ Installation d'applications complémentaires ( esn/applis.json )")

    filejson=os.path.join("esn","applis.json")
    if not os.path.isfile(filejson): return

    with open(filejson,"r") as f:
        data=json.load(f)

    for appli,package in data.items():
        if TestAppli(appli):
            print(f"  👉 Déja installé: {appli}")
        else:
            print(f"  👉 Installation de {appli} depuis le package {package}")
            PrepareSudo()
            cmd=f"(sudo apt install -y {package}) > /tmp/auditlog.txt 2>&1"
            print("    ",cmd)
            code=os.system(cmd)
            if code == 0:
                print("    Installation réussie")
            else:
                print("    🚫️  Echec !")
            print()


def MajPwd():
    print("\n➡️ Creation du fichier MotDePasse sur le Bureau")
    txt=os.environ.get("ZZZEMMAUS","") 
    bureau=GetBureau()
    filename=os.path.join( bureau,"MotDePasse.txt" )     
    with open(filename,"w") as f:
        f.write(txt)      


    

def MajAll():
    print("\n\n➡️-------------- Début des  Finitions ! ---------------")

    MajBureau()

    MajApplis()

    MajFirefox()

    MajMenu()

    MajBarre()

    print("\n➡️-------------- FINI ! -------------\n")

def MajAllPwd():
    MajAll()
    MajPwd()

if __name__ == '__main__':
    MajAllPwd()

    
