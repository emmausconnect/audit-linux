

import json
import re
import sys
import datetime
import os







# fichiers include
from  outils import *   
from ihm  import *
from audit import *



#--------------------------------------------------------
# Menu principal
#
#--------------------------------------------------------
def MenuWinActions(owner,id):
    

    if id == "CRISTAL":    
        #WinExecWait( r".\outils\crystaldiskinfoportable\DiskInfo64.exe" )
        WinExecWait( r"..\outils\CrystalDiskInfoPortable\DiskInfo64.exe" )

    if id == "SDC":
        WinExecWait( r"..\outils\SDC\Smart Disk Checker.exe" )

    if id == "HDTUNE":
        WinExecWait( r"..\outils\Portable_HDTune\hdtune.exe" )

    if id == "CLAVIER":
        Browser( "https://www.test-clavier.fr/" )


    if id == "WIN11":
        cmd="utils\\WhyNotWin11.exe"
        os.system(cmd)  

    if id == "BITLOCKER":
        cmd='win\\execpower.cmd clebitlocker.ps1'
        os.system(cmd)  

    if id == "RESTART":
        cmd='shutdown.exe -f -r -o -t 0'
        os.system(cmd)  

    if id == "WINSCP":
        cmd= r'..\outils\WinSCPPortable\WinSCPPortable.exe'
        os.system(cmd) 

    if id == "AVIRA":
        Browser( "https://www.avira.com/fr/free-security")


    if id == "TUNING":
        WinExecWait(  "utils\\EmCoTech.exe" )



def PrepareSudo():
    os.system( ' echo "$ZZZEMMAUS" | sudo -S -p "init sudo" echo "..............." ')

#--------------------------------------------------------
# Menu reconditionnement
#
#--------------------------------------------------------
def MenuRecondActions(owner,id):

    if id == "SITESWEB":
        name="sitesweb.htm"
        template=os.path.join("modeles",name)
        filehtm=os.path.join(TMPDISK,name)
        CopyFile2File( template, filehtm )

        if WIN:
            cmd=f"wmic bios get serialnumber >> {filehtm}"
        else:
            #cmd=f"(sudo dmidecode -s system-serial-number) >> {filehtm}"
            cmd=f"(cat /sys/class/dmi/id/product_name) >> {filehtm}"
        os.system(cmd)
        Browser( filehtm )
   

    if id == "DOC":
        filehtm=os.path.join("doc","index.html")
        Browser( filehtm )

    if id == "INITID":
        Ecid().Reset()


    if id == "DISK":
        cmd= "gnome-disks &"  # en background pour pas bloquer le menu
        os.system(cmd) 


    if id == "BATTERIE":
        # cette commande est non-bloquante
        cmd='gnome-terminal --title "TEST BATTERIE" -- bash batterie.sh'
        os.system(cmd)

    if id == "WEB":
        Browser( "https://philippe-ec.github.io/EClille.github.io" )


    if id == "AUDITMINI":
        PrepareSudo()
        ProcessAudit(mini=True)

    if id == "AUDITXFER":
        PrepareSudo()
        ProcessAudit(mini=False,xfer=True )

    if id == "AUDIT":  
        PrepareSudo()      
        ProcessAudit(mini=False,xfer=False)

    if id == "CARACT":
        c = Caract()
        c.Dialog()

    if id == "BOLC":
        TransfertBolc()




    if id == "STATUT":
        BolcStatut()






def MenuRecond( withtest=True ):

    while True:

        if withtest:    title ="Menu Reconditionnement AVEC tests"
        else:           title ="Menu Reconditionnement SANS tests"
        dialog=Zdialog( title ,5,5)
        vbox=dialog.area

        hbox = Zhbox( vbox,2 ,0)
        vbox1=Zvbox(hbox,5,5)
        vbox2=Zvbox(hbox,5,5)

        if ( withtest ):
            btools=Zvbox(vbox1,5,5,"TESTS")

            Zbutton(dialog, btools ,"DISK", "Test Disque","LightGreen",MenuRecondActions)          # process en //
            Zbutton(dialog, btools ,"BATTERIE", "Test Batterie","LightGreen",MenuRecondActions)    # process en //
            Zbutton(dialog, btools ,"WEB", "Webcam, Clavier, Son","LightGreen",MenuRecondActions)  # process en //


        butils=Zvbox(vbox1,5,5,"Utilitaires")
        Zbutton(dialog, butils ,"BOLC", "Transfert BOLC","Yellow")
        Zbutton(dialog, butils ,"STATUT", "Changement Statut BOLC","Yellow")
        Zbutton(dialog, butils ,"INITID", "REINITIALISATION IDENTIFIANT EMMAUS","Yellow")

        bres=Zvbox(vbox1,5,5,"Ressources")
        Zbutton(dialog, bres ,"SITESWEB", "ACCES AUX SITES WEB CONSTRUCTEURS POUR BIOS & DRIVERS","Chocolate",MenuRecondActions)
        Zbutton(dialog, bres ,"DOC", "DOCUMENTATION","Chocolate",MenuRecondActions)


        Zbutton(dialog, vbox2 ,"AUDITMINI", "Mini Audit","lightblue")

        Zbutton(dialog, vbox2 ,"CHECK", "Affichage Checklist\n** à rajouter **","LightGreen")
        Zbutton(dialog, vbox2 ,"CARACT", "Saisie des Caractéristiques Matériel","LightGreen")
        boxaudit=Zvbox( vbox2,5,5)
        Zbutton(dialog, boxaudit ,"AUDITXFER", "AUDIT + transferts","lightblue")
        Zbutton(dialog, boxaudit ,"AUDIT", "AUDIT sans transferts","lightblue")
        #Zcheck(dialog,boxaudit,"XFEREMMAUS","Transfert vers serveur Emmaus","on")
        #Zcheck(dialog,boxaudit,"XFERBOLC","Transfert vers BOLC","on")
        #######################################Zbutton(dialog, vbox2 ,"TUNING", "Installations/Finitions (EmCoTech)","pink")  


        butbox=Zhbox(vbox,5,0)
        Zbutton(dialog, butbox ,"QUIT", "QUITTER","orange")


        out=dialog.Run()
        exitcode=dialog.exitcode

        MenuRecondActions( dialog, exitcode)

        if exitcode in [ "MAIN", "QUIT","#QUIT" ] : return exitcode
    



#===========================================================================================
# Changement du statut Bolc
#
#  On prend le modele
#===========================================================================================
def BolcStatut():    

    ecid=Ecid().Get()
    liststatut=[
            "A reconditionner",
			"En reconditionnement",
			"A entrer dans Salesforce",
			"Prêt à vendre ",
			"Prêt à donner",
			"Réservé",
			"Vendu",
			"Donné ",
			"Usage interne",
			"SAV bénéficiaire",
			"HS",
			"perdu",
			"Transféré",
			"En attente ",
			"Retour reconditionneur pro.",
            "Utilisé"
            ]
    
    dialog=Zdialog("Changement du Status Bolc",5,5)
    vbox=dialog.area
    Ztext( vbox , f"Identifiant: {ecid}")
    Zlistbox(dialog,  vbox, "STATUT", "Nouveau Statut", liststatut , "") 
    Zentry(dialog, vbox, "COMMENT", "Commentaire Statut: ","r","")
        
    boxactions= Zhbox(vbox,0,0)
    Zbutton(dialog, boxactions ,"QUIT", "QUITTER","Orange")
    Zbutton(dialog, boxactions ,"OK", "OK","Yellow")

    out=dialog.Run()

    if out.get("OK","") == "" : return
    if out.get("STATUT","") == "" : return

    print("Nouveau statut: " + out["STATUT"])

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


    TransfertBolc( filebolc )




out=MenuRecond()

