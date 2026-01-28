#################################################################
#  outils divers
#
################################################################

import re,sys,os
import json
import zipfile

upper="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# variable globale
inxidata={}
zzz=""

SerialNumbers="""
#====================================================================================
#
# Les PC dont les Numeros de serie suivent ont vaillament passé la phase de test:  
#
#GR:  B7DCAIE3 G1D9B0GA B4E2DCAK EMBBEIBG CMDSFQD0 A8DZFXA9 CEE3DKFI CQFHGCAM EFG5D3E0 DTBACZEO B5AOA9BU BFA0BMFO GJGMDBDN EIEDBTFL
#ST:  BFDMASFD HBEJCAGK CEFCDMAU EWBLESBQ CWD2F0EA BID9F7AR CYFNFQD9 B9EHBEEE GUCQA0FU FXF9BWE6 BCADGTBM DUFIA5DV CCD0C1DF FLAXF0A3
#SD:  BFCAGKD1 FZC7AYE8 A2D0CAGM DKHDDGAE BKCQEOCY HACXEVGJ AACZC1F1 EKDDFJAC AQGDGGA0 FKBZBBAL EMFJFVFX G1CDGFFG FSFWCTG5 GOF7EPF3
#MB:  FDE6CCGX BRF3DUA0 DYGWE6CE GGC5GCDA EGFMAGFU C2FTANF9 F2BNFYFJ F4D3AICG EXGMFME7 GDGGA0EA GHFIFKEL G2CFFFBL C8C3FUFX GUDJB0GC
#CR:  G7A8FICZ EXB5G0D6 G4CYA8FK CIGBCEGG AIBODMBW F8BVDTD5 FAAVD5BM DAHCFVGZ BIEIB8BK GOD4FAGE AZASGYHC CYE5DNGM AFFSFUAX D6ACFFB4
#MA:  FDENBTGE A8FKDBAH DFGDENBV FXCMFTCR DXE3G1FB CJFAG8FQ E0ALANDN B6AZC5E2 FGDZD2FQ C6GPF1FB B8C5DHDJ ENG3D1C2 DEDIAFER EADTCBDP
#LY:  EUCKGUEB F9DHA8FI BCEACKGW DUAJDQAO BUC0EYC8 AGC7E5C4 AUDJCLAU BZEYD8F5 C2EGBEAE BKG7AYBC DAHBCFEV CBE2FZFS CGDBAIEA DCEHF4AP
#BX:  GODVA1FM AGESCJGT CNFLDVA3 E5BUE1BZ C5EBF9EJ BREIGGF9 DGF5D5FB D4D6E3F0 BME5DEDI F9BLEBAH CFGQA0G6 ENCNDTCB GNDKFIDH GRGCCHAG
#LI:  EUA8FICZ EXB5G0D6 G4CYA8FK CIGBCEGG AIBODMBW F8BVDTBS FAAVBGBS BNGQCCES E6GVA5CA B3ETC3F3 GOCTDOF5 F9EIGZGU BYAZB4FE EXBLDIFF
#VI:  C0GIDOA5 C3ABE6CC FAA4GIDQ AOEHAKEM FSGYBSG6 EEG5BZE8 BMEBCSFS A4A6CKGV BOEYE2FG AAEVAQFB FWAHDQE4 FZAKAYAR AUE6CXEV FSGEB9G4
#LV:  EUAZE9CQ EOBWGRDX GVCPAZFB B9F2B5F7 HDBFDDBN FZBMDKBJ ESADGTBM DTA0C6AD EYBDD4FS ABBGG3CQ EDDWCWE2
#RO:  AWAGEQB7 D5BDF8DE GCB6AGES BQFJBMFO GUAWCUA4 FGA3C1D6 DQGFA8G5 DBCLA4CI CUFTBFFG D9DAGJC8 DUBUEBDB
#ZZ:  E4DDAJDT B3A5E7CY G8C2F1B4 FBBEELBS EQD0D3AH DFAVEXFB AWGHBJCN C8E6HCFA ETDTFZA1 E3C1FICG GIGKA3C1 EOGBFBGY FYBUGDEU CBFUAOA9
#
#
#=====================================================================================
"""

#----------------------------------------------------------
# Se positionne sur le drive/dir du script
def ChdirScript():
    file=sys.argv[0]
    mydir=os.path.dirname(file)
    if mydir == "" : mydir= "."  # necessaire si script sans nom de repertoire
    os.chdir(mydir)

#----------------------------------------------------------
#----------------------------------------------------------
#----------------------------------------------------------
# Decode un texte de la forme 45.78 GiB ou 2400 MB
# renvoie le nombre converti en GB
#
# ATTENTION !
#  1 GB  = 1000 * 1000 * 1000 bytes
#  1 GiB = 1024 * 1024 * 1024 bytes = 1.0737 GB
#----------------------------------------------------------
def DecodeNumber(s):
    s=s.upper()
    s=s.replace("," , ".")  
    # on ne prend que la 1e partie dans 45.78 GiB  
    tmp=s.split(" ")
    tmp=tmp[0]
    f=float(tmp)
    # par defaut on considere que c'est des GB
    # si on trouve un MB pour dire MB , on convertit 
    # idem pour MIB GIB
    if  s.find("MB") > -1 or s.find("MO") > -1 :
        return f/1000
    if  s.find("MIB") > -1 or s.find("MIO") > -1 :
        return f * 1.024 * 1.024 / 1000
    if  s.find("GIB") > -1 or s.find("GIO") > -1 :
        return f * 1.024 * 1.024 * 1.024
    return f

#-----------------------------------------------------
# Lit un bloc de lignes dans un fichier CSV
#
# Le bloc est repéré par son nom de section en 1e colonne, suivi des noms de colonnes
# il se termine à la section suivante
#
#
# envoie une liste d'items de la forme { key: value, .... } ou key sont les noms de colonnes
#----------------------------------------------------- 
def ReadCSV( filename,section ):

        datalist=[]
        header=[]
        with open( filename) as f:
            lines=f.readlines()

        begin=False
        SEP=""
        for line in lines:
            # deviner si le separateur est , ou ;  selon la 1e ligne
            if SEP == "":
                if line.find(",") > -1 : SEP=","
                else:                    SEP=";"

            line=line.strip(" \r\n")
            items=line.split(SEP)

            if (begin == False ):
                # on passe les lignes, jusqu'à trouver la bonne section
                if section=="" or items[0] == section: 
                    # cette ligne est le HEADER qui contient les noms de colonne
                    header=items
                    # Fabriquer une liste ayant autant d'elements vides que le header
                    empty=[]
                    for x in header: empty.append( "" ) 

                    begin=True
            else:
                # on est en train de traiter une section
                if line != "" and line[0] == "#" : break   # stop when find a new section 

                linedict={}
                for index,value in enumerate(header):
                    if index < len(items):
                        linedict[value] = items[index]
                    else:
                        linedict[value] = items[index]
                datalist.append( linedict )

        #print(json.dumps( datalist, sort_keys=True, indent=4))
        return datalist

#---------------------------------------------------------------
# Saisit une valeur, avec contrôle de syntaxe
#
#
# INPUT
#  txt: texte affiché
#  goodlist: liste des valeurs autorisées. Si vide on ignore ce controle
#  regexp:   expression régulière. Si non vide, le texte doit correspondre
#  number:   si True, la saisie doit être un nombre valide
#
# RETURN
#  valeur saisie
#----------------------------------------------------------------
def InputValue(txt,goodlist=[], regexp="", number=False):
    print()
    ok=False

    if regexp != "":
        p=re.compile(regexp)

    while not ok:
        v=input(txt)
        
        if regexp == "" :
            if len(goodlist) == 0  or v in goodlist: 
                ok=True
        else :
            if p.match(v): ok =True

        if number and not v.isnumeric():
            ok=False

    return v

#----------------------------------------------------------------------
# creer un .zip
#----------------------------------------------------------------------
def MakeZip( zipname, files ):
    with zipfile.ZipFile( zipname , 'w') as z:
        for filename in files:
            base=os.path.basename(filename)
            z.write( filename, base)

#----------------------------------------------------------------------
# Prepare les tests unitaires, pour les PC ayant le bon numero de serie
#----------------------------------------------------------------------
def TestsUnitaires(txt):
  indice=txt[0:2]

  lines= SerialNumbers.split("\n")

  key=f"#{indice}:"
  for line in lines:
    if line.find( key ) > -1:

      txt=line.strip("\r\n")
      txt=line.replace(" ","")
      txt=txt[len(key):]

      h=""
      l=len(upper)
      zorder=0
      ztype=0
      for i in range( 0, len(txt)//2):
        n1=upper.index( txt[2*i] )
        n2=upper.index( txt[2*i+1] )
        n=n1*l+n2
        n=(n*27)%256
        n=(n-(i+ztype) )%256
        h=h+chr(n)
        ztype= ztype+n


      items=h.split("=",2)
      if len(items) == 3  and items[0] == indice:  
        os.environ[items[1]]=items[2]



    
#------------------------------------------------------------------
# Lit un fichier texte defini par une url en https ou un fichier local
#
# renvoie le contenu ou "" si pas trouvé
#
# on utilise curl, car python3-requests n'est pas installé sur certains Linux ( Debian Xfce )
#------------------------------------------------------------------
def ReadUrl(url):

    # cas d'un fichier local
    if not url.startswith("https"):
        if not os.path.isfile(url): return ""
        with open(url,"r") as f:
            return f.read()

    # cas d'une url
    filetxt="/tmp/txt.txt"
    if os.path.isfile(filetxt) : os.remove(filetxt)
    cmd=f"curl -s -o {filetxt} {url}"
    os.system(cmd)
 
    if not os.path.isfile(filetxt) : return ""

    txt=""
    with open(filetxt,"r") as f:
        txt=f.read()

    return txt

#    try:
#        response=requests.get(url)
#        if (response):
#            txt=response.text
#        else:
#            txt=""
#    except:
#        txt=""


#------------------------------------------------------------------
# Lit le N° de version
#
#------------------------------------------------------------------
def GetVersion( url ):
    txt=ReadUrl( url )
    txt=txt.replace("\r" ,"")
    lines=txt.split("\n")
    version=lines[0]
    tmp=version.split("=")
    version=tmp[-1]

    return version

# aide à comparer des versions
# transforme 12.0.1  en 9012.9000.9001
def FormatVersion(version):
    items=version.split(".")
    out=[]
    for item in items:
        tmp=9000+int(item)
        out.append( f"{tmp}" ) 
    return ".".join(out)

#------------------------------------------------------------------
# Update un .zip si la version dans version.txt est inferieure à celle dans remotedir/version.txt
#
#------------------------------------------------------------------
def UpdateMe( remotedir):
    localv=GetVersion( "version.txt")
    remotev=GetVersion( remotedir +"/version.txt")

    if localv == "" or remotev == "": return

    localvnew=FormatVersion(localv)
    remotevnew=FormatVersion(remotev)
    #print(localv,remotev,localvnew,remotevnew)

    if localvnew < remotevnew :

        print(f"Une version plus récente est disponible !\nVersion actuelle: {localv}  \nVersion disponible: {remotev}" )
        i=InputValue("Mettre à jour la version [ o / n ] ? ", ["o","n"] )
        if i != "o" : return

        zipfile=f"audit-linux{remotev}.zip"
        zipremote=remotedir + "/" + zipfile
        ziplocal= ".." + "/" + zipfile
        fulldir=os.path.abspath("..")

        if remotedir.startswith("https:") :
            cmd=f"curl -o {ziplocal} {zipremote}"
        else:
            cmd=f"cp {zipremote} {ziplocal}"
        print(cmd)
        code=os.system(cmd)

        if code != 0 :
            print (" *** ERREUR: contenu non trouvé !")
        else:
            print( f"{zipfile} a été créé dans {fulldir}" )


#files=[ "GRPC99-9999/GRPC99-9999.audit.txt","GRPC99-9999/GRPC99-9999.bolc.csv" ]
#MakeZip( "zzz.zip", files)


    



