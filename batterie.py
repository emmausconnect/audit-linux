
import os
import sys
import time
import signal
import sys
import datetime

from  outils import *   # outils.py

inxifile="/tmp/tmp.txt"


outfile="/tmp/batterie.txt"

guide="""
=============== Mesure autonomie batterie ====================

Il y a 2 moyens pour faire cette mesure :

Méthode1 (rapide):
- Inhiber l'économiseur d'écran ( Préférences => Paramètre Système => Economiseur d'Ecran )
- Inhiber la mise en veille     ( Préférences => Paramètre Système => Gestion d'Alimentation )

- Lancer une vidéo sur Firefox : https://www.youtube.com/watch?v=bQoOev5GNYM
- Enlever le cable du chargeur de batterie
- Laisser tourner cet outil pendant 10 ou 20mn, et retenir l'estimation d'automonie qu'il donne

Méthode2 (lente):
- Inhiber l'économiseur d'écran ( Préférences => Paramètre Système => Economiseur d'Ecran )
- Inhiber la mise en veille     ( Préférences => Paramètre Système => Gestion d'Alimentation )
- Charger la batterie à 100%

- Lancer une vidéo sur Firefox : https://www.youtube.com/watch?v=bQoOev5GNYM
- Enlever le cable du chargeur de batterie
- Lancer l'outil, et laisser le PC jusqu'à ce qu'il s'arrête pour cause de batterie vide

- Regarder dans le fichier /tmp/batterie.txt  le nbre de minutes pendant lesquelles l'outil a tourné

============== Début des mesures ==========================
"""


def abort():
        print( "Infos de batterie non disponibles" )
        exit()

#----------------------------------------------------------------------
# Appel de inxi pour trouver la charge de la batterie
#
# Estime l'autonomie, et écrit une ligne sur le fichier resultat
#
# INPUT
#
#  i = N° de l'iteration
#  minutes= temps en minutes depuis le debut
#  membat = charge de la batterie à la 1e exècution
#
# RETURN
#  renvoie la charge de batterie
#
#
#----------------------------------------------------------------------
def ShowBattery(i,minutes,initbat) :

    # commande inxi pour avoir les infos de batterie
    cmd=f"inxi -B -y1 > {inxifile} "
    os.system(cmd)

    # Decodage des infos dans Inxi            
    DecodeInxi(inxifile)

    # "Battery/ID-x/charge"
    batinfo=""
    for key,data in InxiItems("Battery").items() :
        # decodage de la charge batterie
        v=InxiValue(f"Battery/{key}/charge" )
        if v != "" : batinfo =v

    if batinfo == "" : abort()

    tmp=batinfo.split("(" )
    batinfo=tmp[-1]
    tmp=batinfo.split("%" )
    batinfo=tmp[0]

    batinfo=float(batinfo)

    # calcul de l'autonomie
    if minutes == 0:
        delta=0
    else:
        delta=membat - batinfo
    
    if delta != 0 : 
        autonomie=90*minutes / delta          # on considere que ça tient jusqu'à 10%
        autonomie=f"{autonomie:.0f} mn"
    else:
        autonomie="****"

    date= datetime.datetime.now().strftime("%H:%M:%S")

    txt=f"{date}  {outfile}   Temps(mn)={minutes:<4}  Batterie={batinfo:<4}%    DeltaBatterie={delta:<4.2f}%   Autonomie={autonomie}"

    print(txt)

    # rajouter une ligne sur le fichier resultat
    with open( outfile,'a') as f:
        f.write(txt + "\r\n" )

    return batinfo

#================================= Main ===============================

# Catcher le CTRL/C
def signal_handler(sig, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print(guide)

with open( outfile,'w') as f:
    f.write("")

i=0
membat=0
starttime=time.time()



while True:

    t=time.time()
    minutes= round ( ( t - starttime ) / 60 )

    b=ShowBattery(i,minutes,membat)
    if i==0 : membat=b

    i=i+1

    # inxi a pu prendre du temps, donc on n'attend pas exactement 60s
    # calcul du temps à attendre, pour executer la prochaine itération à i*60 secondes
    newtime=time.time()

    waittime= int (  starttime + i*60 - newtime )
    waittime=max( 10, waittime )  # eviter de boucler si on est très en retard, suite à une hibernation

    t1=time.time()
    time.sleep(waittime)
    t2=time.time()
    
    # si le sleep a duré 10s de trop, c'est qu'une hibernation a eu lieu
    sleeptime = t2 - t1
    # print ( "sleeptime",sleeptime,"waitime",waittime) 
    if sleeptime > 60 + 10:
        break








    
    



