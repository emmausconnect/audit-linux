#####################################################################################
# Calcul du cpumark
#
# cpumark = FindCPUMARK(cpufile,cpuname)
#####################################################################################

import re
from common import *


#--------------------------------------------------------
# Retire la partie finale d'un cpuname
#
# Cela concerne des trucs qu'on retire à la fois
# - dans le cpuname qu'on recherche
# - dans les cpu de cpus.csv
#
#  INPUT
#     cpuname: nom du cpu
#  RETURN
#     nom du cpu nettoyé
# 
#--------------------------------------------------------   

def CleanCpuSuffix(cpuname):
    # ce qui est après @ est parfois différent entre inxi et cpubenchmark.net
    cpuname=re.sub( r'[@].*$' , "" , cpuname)  # on retire à partir du @
    cpuname=re.sub( r'\s+' , " " , cpuname)    # 1 seul espace consecutif
    cpuname=cpuname.strip()
    return cpuname




#--------------------------------------------------------
# Nettoie le nom d'une CPU, avant de la rechercher dans la liste
#
#  INPUT
#     cpuname: nom du cpu
#  RETURN
#     nom du cpu nettoyé
#
#   valeur Inxi                                         Valeur cpubenchhmark.net
#   Intel (R) Core(TM) i5-6200U CPU @ 2.30GHZ           Intel Core i5-6200U @ 2.30GHZ
#   Intel Core i7-5600U                                 Intel Core i7-5600U @ 2.60GHz
#   13th Gen Intel Core i7-1360P                        Intel Core i7-1360P 
#   Intel Core i7 M 620                                 Intel Core i7-620M   // reorganisation du M et du 620
#   Intel Core i7 Q 720                                 Intel Core i7-720QM  // ajout du M en plus
#   Intel Core i7-5600U                                 Intel Core i7-5600U @ 2.60GHz
#   AMD PRO A10-8730B R5, 10 COMPUTE CORES 4C+6G        AMD PRO A10-8730B   
#   AMD A9-9420 RADEON R5, 5 COMPUTE CORES 2C+3G        AMD A9-9420
#   AMD A8-7100 Radeon R5, 8 Compute Cores 4C+4G        AMD A8-7100 APU  ( le APU sera à traiter ensuite )
#   AMD PRO A10-8700B R6, 10 Compute Cores 4C+6G        AMD PRO A10-8700B
#   AMD PRO A10-8730B R5 10 COMPUTE CORES 4C+6G         AMD PRO A10-8730B
#--------------------------------------------------------   
def CleanCpuname(cpuname):

    # à faire avant les autres
    #cpuname=re.sub( r'[@][{]Name=[^}]*[}]' , "" , cpuname)  # truc tiré de l'auditJJ    supprimer @{Name=.......}
    cpuname=re.sub( r'\(R\)' , "" , cpuname)   # supprimer (R)
    cpuname=re.sub( r'\(TM\)' , "" , cpuname)  # supprimer (TM)
    cpuname=re.sub( r'CPU *' , "" , cpuname)  # supprimer "CPU "

    # Cas des cpu Intel
    if cpuname.find("Intel") > -1 :

        cpuname=re.sub( r'[0-9]+th Gen ' , "" , cpuname , 0 , re.IGNORECASE  )  # supprimer "13th Gen" "13TH GEN"
        
        # "Intel Pentium Dual T3200"  => "Intel Pentium T3200" 
        # regle abandonnée car il existe à la fois "Intel Pentium Dual T2390"  et  "Intel Pentium T2390"
        #cpuname=cpuname.replace("Pentium Dual","Pentium")

    # Cas des cpu Pentium
    # tous les Pentium commencent par Intel Pentium  , sauf ceux avec "Dual-Core"
    if cpuname.startswith("Pentium") :
        if cpuname.find("Dual-Core") <0:    cpuname="Intel " + cpuname

    # Cas des cpu AMD
    # beaucoup d'ennuis avec Radeon . 
    if cpuname.find("AMD") == 0  and cpuname.find("AMD Embedded") < 0 :
        cpuname=re.sub( r' with .*$' , "" , cpuname)  # supprimer " with xxxxxxx" 
        cpuname=re.sub( r' w/ .*$' , "" , cpuname)  # supprimer " w/ xxxxxxx"   "AMD Ryzen 5 PRO 2500U w/ Radeon Vega Mobile Gfx"
        cpuname=re.sub( r' RADEON .*$' , "" , cpuname,flags=re.I)  # supprimer  à partir de RADEON ou Radeon   "AMD A8-7100 Radeon R5, 8 Compute Cores 4C+4G"  
        cpuname=re.sub( r' R[56],? .*$' , "" , cpuname)       # supprimer  à partir de R5 R5, R6 R6, 
        #POSE PROBLEME  cpuname=re.sub( r' APU *$' , "" , cpuname)  # on retire le APU final, une fois que "with" "w/" "radeon" ont été purgés
        pass

    # Pour tout le monde
    cpuname=re.sub( r'\s+' , " " , cpuname)    # 1 seul espace consecutif

    # une fois qu'on a un seul espace consecutif, et purgé le "CPU" , transformer "Intel(R) Core(TM) i3 CPU       M 330"  en  "Intel Core i3-330M"
    # Ne pas le faire avec d'autres lettres que M ou Q , à cause de "Intel Core i5 E 520"
    cpuname=re.sub( r'Intel Core i([0-9]) (M) ([0-9]+)' , r"Intel Core i\1-\3\2" , cpuname)  
    cpuname=re.sub( r'Intel Core i([0-9]) (Q) ([0-9]+)' , r"Intel Core i\1-\3\2M" , cpuname)   # rajout du M
    # Et aussi Intel Core i3 550  en Intel Core i3-550
    # ne pas le faire sur Core i5 à cause de "Intel Core i5 750S"
    cpuname=re.sub( r'Intel Core i([3]) ([0-9]+)' , r"Intel Core i\1-\2" , cpuname)  

    cpuname=cpuname.strip()
    return cpuname


            
#--------------------------------------------------------
# Lit le fichier csv des cpus, et cherche un nom de cpu
#
# Les comparaisons se font en minuscules
# Pour éviter des confusions, on compare sur l'égalité
# le nom dans Inxi peut être plus grand que le nom dans cpubenchmark.net, mais pas toujours
#
#   valeur Inxi                           Valeur cpubenchmark.net
#   13th Gen Intel Core i7-1360P          Intel Core i7-1360P 
#   Intel Core i7-5600U                   Intel Core i7-5600U @ 2.60GHz
#
# INPUT
#   cpufile: nom du fichier csv contenant la liste des cpus
#   cpuname: nom de cpu à rechercher
# RETURN
#   ( cpumark , cpufound , trace )
#      - cpumark : cpumark si le cpu est trouvé dans le fichier ) sinon ""
#      - cpufound: nom du cpu trouvé dans le fichier , sinon ""
#      - trace :   traces de la recherche
#--------------------------------------------------------   
def FindCPUMARK(cpufile,cpuname):

    # lire le fichier des cpu
    cpulist=ReadCSV(cpufile,"")

    #print( json.dumps(newcpulist,indent=4) )
    #cpuname="Intel Core i3-6100U"

    trace=""

    cpuold=cpuname

    tmpname=cpuname
    #tmpname=CleanCpuSuffix(cpuname)
    cpuname=CpuChange().Adapt(tmpname)

    # Si on a forcé le résultat, ne pas essayer d'appliquer d'autres transformations
    if cpuname == tmpname:
        cpuname=CleanCpuname(cpuname)


    trace=f"Cherche: {cpuold}       Transformé en: {cpuname}\n"


    newcpuname=cpuname.lower()

    #print("***recherche",newcpuname)
    # key est le nom qu'on montre dans le resultat
    # newkey est le nom sur lequel on fait les comparaisons
    for cpudata in cpulist:
        key=cpudata["NAME"]


        # (observation du fichier des cpus )
        # Si cpuname n'a pas de suffixe @ contenant la frequence,  key peut en avoir un ou pas
        # Mais si cpuname en a un , key l'a aussi
        if cpuname.find("@") <0 : newkey=CleanCpuSuffix(key)  
        else:                     newkey=key   
       
        newkey=newkey.lower()  

        if newcpuname == newkey :
            trace=trace+ f"Trouve: {key}\n"
            value=cpudata["CPUMARK"].replace(",","")  # les valeurs peuvent contenir un separateur de milliers
            return (value,key,trace)

    trace = trace + f"Echec de la recherche...\n"
    return ("","",trace)

#=================================================================
# Stocke dans un csv les correspondances entre noms de cpu
#
# renvoie le nom de cpu modifié si on le trouve dans la liste
#=================================================================
class CpuChange:

    data=None
    csv="cpuchange.csv"

    def __init__(self):
        if self.data is None:

            with open( self.csv ,"r" ) as f:
                lines=f.readlines()

            self.data=[]
            for line in lines:
                line=line.strip(" \r\n")
                if line != "":
                    items=line.split(";",1)
                    self.data.append( items )

    def Adapt( self,cpuname ):
        for elem in self.data:
            pattern,newvalue= elem
            if pattern != "" and cpuname.find( pattern ) > -1 :
                return newvalue
        return cpuname

