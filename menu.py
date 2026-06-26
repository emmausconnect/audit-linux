# import json
# import re
# import sys
# import datetime
import time
import datetime
# import os

datestamp = time.strftime("%Y%m%d.%H%M%S", datetime.datetime.now().timetuple())

# fichiers include
# from  outils import *
# from ihm  import *
from audit import *
from finitions import *


#--------------------------------------------------------
# Menu principal Windows
#
#--------------------------------------------------------
# def MenuWinActions(owner,id):
#
#
#     if id == "CRISTAL":
#         #WinExecWait( r".\outils\crystaldiskinfoportable\DiskInfo64.exe" )
#         WinExecWait( r"..\outils\CrystalDiskInfoPortable\DiskInfo64.exe" )
#
#     if id == "SDC":
#         WinExecWait( r"..\outils\SDC\Smart Disk Checker.exe" )
#
#     if id == "HDTUNE":
#         WinExecWait( r"..\outils\Portable_HDTune\hdtune.exe" )
#
#     if id == "CLAVIER":
#         Browser( "https://www.test-clavier.fr/" )
#
#
#     if id == "WIN11":
#         cmd="utils\\WhyNotWin11.exe"
#         os.system(cmd)
#
#     if id == "BITLOCKER":
#         cmd='win\\execpower.cmd clebitlocker.ps1'
#         os.system(cmd)
#
#     if id == "RESTART":
#         cmd='shutdown.exe -f -r -o -t 0'
#         os.system(cmd)
#
#     if id == "WINSCP":
#         cmd= r'..\outils\WinSCPPortable\WinSCPPortable.exe'
#         os.system(cmd)
#
#     if id == "AVIRA":
#         Browser( "https://www.avira.com/fr/free-security")
#
#
#     if id == "TUNING":
#         WinExecWait(  "utils\\EmCoTech.exe" )





#--------------------------------------------------------
# Menu reconditionnement
#
#--------------------------------------------------------
def MenuRecondActions(owner,id):

    noactionbuttons = ["STATUT", "AUDITMINI", "AUDITXFER", "AUDIT"]

    if id in noactionbuttons:
        return

    if id == "SITESWEB":
        name="sitesweb.htm"
        template=os.path.join("modeles",name)
        filehtm=os.path.join(TMPDISK,name)
        CopyFile2File( template, filehtm )

        cmd=f"(cat /sys/class/dmi/id/product_name) >> {filehtm}"
        os.system(cmd)
        Browser( filehtm )
   

    if id == "DOC":
        filehtm=os.path.join("doc","index.htm")
        Browser( filehtm )

    if id == "INITID":  # this button serves no purpose after removal of Ecid class...
        EqId().reset()  # Ecid().Reset()


    if id == "DISK":
        cmd= "bash addons/testdisque.sh &"
        os.system(cmd) 


    if id == "BATTERIE":
        GetPasswd()
        # cette commande est non-bloquante
        cmd='gnome-terminal --title "TEST BATTERIE" -- bash batterie.sh'
        os.system(cmd)

    if id == "WEB":
        Browser( "https://philippe-ec.github.io/EClille.github.io" )


    if id == "AUDITMINI":
        GetPasswd()
        PrepareSudo()
        ProcessAudit(mini=True, useprodapi=False, datestamp=datestamp)

    if id == "AUDITXFER":
        GetPasswd()
        PrepareSudo()
        ProcessAudit(mini=False, useprodapi=False, xfer=True, datestamp=datestamp )

    if id == "AUDIT": 
        GetPasswd() 
        PrepareSudo()
        ProcessAudit(mini=False, useprodapi=False, xfer=False, datestamp=datestamp)

    if id == "CARACT":
        c = Caract()
        c.Dialog()

    if id == "MAJ":
        MajAll()

    if id == "PWD":
        GetPasswd()
        MajPwd()

    # id is never "BOLC" ==> this block is useless
    # if id == "BOLC":
    #     filebolc=os.path.join( TMPDISK,"-bolc.txt")
    #     TransfertBolc(filebolc)

    if id == "STATUT":
        BolcStatut()

    if id == "KEYBDFR":
        cmd= "bash setxkbmap-fr"
        os.system(cmd) 

    if id == "KEYBDMAC":
        cmd= "bash setxkbmap-fr-mac"
        os.system(cmd) 



def MenuRecond( withtest=True ):

    while True:

        if withtest:    title ="Menu Reconditionnement AVEC tests"
        else:           title ="Menu Reconditionnement SANS tests"
        dialog=Zdialog( title ,5,5)
        vbox=dialog.area

        hbox = Zhbox( vbox,2 ,0)
        vbox1=Zvbox(hbox,5,5)
        vbox2=Zvbox(hbox,5,5)

        if withtest:
            btools=Zvbox(vbox1,5,5,"TESTS")

            Zbutton(dialog, btools ,"DISK", "Test Disque","LightGreen",MenuRecondActions)          # process en //
            Zbutton(dialog, btools ,"BATTERIE", "Test Batterie","LightGreen",MenuRecondActions)    # process en //
            Zbutton(dialog, btools ,"WEB", "Webcam, Clavier, Son","LightGreen",MenuRecondActions)  # process en //


        butils=Zvbox(vbox1,5,5,"Utilitaires")

        bclavier=Zhbox(butils,0,0)
        Zbutton(dialog, bclavier ,"KEYBDFR", "setxkbmap fr","Yellow")    
        Zbutton(dialog, bclavier ,"KEYBDMAC", "setxkbmap fr mac","Yellow")  
   
        #Zbutton(dialog, butils ,"BOLC", "Transfert BOLC","Yellow")
        # Zbutton(dialog, butils ,"STATUT", "Changement Statut BOLC (sans effet)","Yellow")
        Zbutton(dialog, butils ,"INITID", "REINITIALISATION IDENTIFIANT EMMAUS","Yellow")

        bres=Zvbox(vbox1,5,5,"Ressources")
        Zbutton(dialog, bres ,"SITESWEB", "SITES WEB CONSTRUCTEURS (BIOS & DRIVERS)","Chocolate",MenuRecondActions)
        Zbutton(dialog, bres ,"DOC", "DOCUMENTATION","Chocolate",MenuRecondActions)


        # Zbutton(dialog, vbox2 ,"AUDITMINI", "Mini Audit (sans effet)","lightblue")

        Zbutton(dialog, vbox2 ,"CHECK", "Affichage Checklist\n** à rajouter **","LightGreen")
        Zbutton(dialog, vbox2 ,"CARACT", "Saisie des Caractéristiques Matériel","LightGreen")
        boxaudit=Zvbox( vbox2,5,5)
        # Zbutton(dialog, boxaudit ,"AUDITXFER", "AUDIT + transferts auto (sans effet)","lightblue")
        # Zbutton(dialog, boxaudit ,"AUDIT", "AUDIT sans transferts auto (sans effet)","lightblue")

        Zbutton(dialog, boxaudit ,"MAJ", "Finitions (Bureau,Menu,Barre des Tâches,Firefox,Applis)","salmon")
        Zbutton(dialog, boxaudit ,"PWD", "Création MotDePasse.txt","salmon")
        #Zcheck(dialog,boxaudit,"XFEREMMAUS","Transfert vers serveur Emmaus","on")
        #Zcheck(dialog,boxaudit,"XFERBOLC","Transfert vers BOLC","on")
        #######################################Zbutton(dialog, vbox2 ,"TUNING", "Installations/Finitions (EmCoTech)","pink")  


        butbox=Zhbox(vbox,5,0)
        Zbutton(dialog, butbox ,"QUIT", "QUITTER","orange")


        out=dialog.Run()
        exitcode=dialog.exitcode

        MenuRecondActions( dialog, exitcode)

        if exitcode in [ "MAIN", "QUIT","#QUIT" ] : return exitcode
    







out=MenuRecond()

