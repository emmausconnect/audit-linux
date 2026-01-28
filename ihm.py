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
def Zinputbox(title,msg,entrylabel="",initvalue=""):
    # créer l'objet Zdialog
    dlg=Zdialog(title)
    vbox=dlg.area

    # message
    Ztext(vbox,msg)
    # zone de saisie
    if entrylabel != "":  
        Zentry(dlg,vbox,"ZVALUE",entrylabel,"up",initvalue,focus=True)

    # Bouton de sortie
    b=Zbutton(dlg,vbox,"OK","OK","yellow")


    result=dlg.Run()
    if "OK" in result:
        return result.get( "ZVALUE", "") # au cas ou pas de entrylabel]
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

    for i in range(3):
        Zradio(dialog, vbox ,f"X{i}", f"BoutonX{i}","","groupX")
    for i in range(3):
        Zradio(dialog, vbox ,f"Y{i}", f"BoutonY{i}","on","groupY")

    # affiche le dialog, attend la sortie, et renvoie le résultat
    print( dialog.Run() )

def ZTestHard():
    items=["CLAVIER","PAVE TACTILE","SOURIS","DVD/GRAVEUR","LECTEUR SD","SORTIE VGA","SORTIE HDMI","SORTIE DISPLAY PORT","BLUETOOTH","PORT ETHERNET","CARTE WIFI"]
    status={ "OK" : "TESTE OK", "HS" : "HS", "ABSENT": "ABSENT" , "PRESENT": "PRESENT" }
    dialog=Zdialog("COLLECTE RESULTATS TESTS MATERIELS",5,5)
    vbox=dialog.area
    grid=Zgrid(vbox)

    for index,value in enumerate(items):

        hbox0=Zhcell(grid,0,index,5,10)
        hbox1=Zhcell(grid,1,index,5,10)
        Ztext(  hbox0 , value)
        for key,txt in status.items():
            if key == "ABSENT" : checked="on"
            else:             checked=""
            Zradio(dialog, hbox1 , key, txt,checked,value)

    Zbutton(dialog, vbox ,"OK", "OK","yellow")       

    out=dialog.Run()
    print(out)
        
        
if __name__ == '__main__':
    ZTestHard()
    #ZTestIhm()



