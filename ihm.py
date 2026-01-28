import os
import re

if "HOME" in os.environ :
    from ihmlinux import *
else:
    from ihmwin import *

#===========================================================================
# InputBox avec un message et une zone de saisie
#
# Renvoie la saisie si on clique sur OK
# Si on ferme la fenêtre avec la croix,on aura ""
#===========================================================================
def Zinputbox(title,msg,entrylabel,initvalue):
    # créer l'objet Zdialog
    dialog=Zdialog(title)
    vbox=dialog.area

    # message
    Ztext(vbox,msg)
    # zone de saisie
    Zentry(dialog,vbox,"VALUE",entrylabel,"up",initvalue)
    # Bouton de sortie
    Zbutton(dialog,vbox,"OK","OK","yellow")

    result=dialog.Run()
    if "OK" in result:
        return result["VALUE"]
    else:
        return ""

#========================= TEST ZONE =================

def ZTestAction(owner,id):
    zzz=Zdialog("modeless",belongsto=owner)
    vbox=zzz.area
    Zbutton(zzz, vbox ,"ZOK", "OK","yellow")
    zzz.Run()


def ZTestIhm():
    dialog=Zdialog("test")
    vbox=dialog.area

    Zbutton(dialog, vbox ,"action1", "action1","#DD22EE",ZTestAction)
    Zbutton(dialog, vbox ,"action2", "action2","Red",ZTestAction)
    Zbutton(dialog, vbox ,"OK", "OK","grey")
    Zcheck(dialog, vbox ,"A", "allemand","")
    Zcheck(dialog, vbox ,"E", "english","on")


    # affiche le dialog, attend la sortie, et renvoie le résultat
    print( dialog.Run() )

if __name__ == '__main__':
    ZTestIhm()


