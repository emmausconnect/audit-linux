import os
import re

if "HOME" in os.environ :
    from ihmlinux import *
else:
    from ihmwin import *

#===========================================================================
# IHM de saisie des infos
#
#
# Si on ferme la fenêtre avec la croix,on aura result["OK"]=""
#===========================================================================
def Zinputbox(title,msg,entrylabel,initvalue):
    # créer l'objet Zdialog
    dialog=Zdialog(title)
    vbox=dialog.area
    Ztext(vbox,msg)
    Zentry(dialog,vbox,"VALUE",entrylabel,"up",initvalue)
    Zbutton(dialog,vbox,"OK","OK","yellow")

    result=dialog.Run()
    if "OK" in result:
        return result["VALUE"]
    else:
        return ""






