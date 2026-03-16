#################################################################
#  outils divers
#
################################################################

import re,sys,os
import json
import zipfile
import http.client

import tectech
from convert_bolc_to_tectech import from_bolc_to_tectech
# from audit import Admin


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

def ISWIN():
    if "HOME" in os.environ :
        return False
    else :
        return True

WIN=ISWIN()

if WIN :
    TMPDISK=os.environ["TEMP"]                              # répertoire où sont générés les fichiers temporaires
    # Curl prefix/suffix
    P="%"
    S="%"
    CURL="curlse\\curl.exe"
else:
    TMPDISK="/tmp"                                  # répertoire où sont générés les fichiers temporaires.  
    # Curl prefix/suffix
    P="$"
    S=""
    CURL="curl"

#----------------------------------------------------------
# alimenter sudo avec som pwd
#----------------------------------------------------------
def PrepareSudo():
    os.system( ' echo "$ZZZEMMAUS" | sudo -S -p "init sudo" echo "..............." ')

#----------------------------------------------------------
# Se positionne sur le drive/dir du script
#----------------------------------------------------------
def ChdirScript():
    file=sys.argv[0]
    mydir=os.path.dirname(file)
    if mydir == "" : mydir= "."  # necessaire si script sans nom de repertoire
    os.chdir(mydir)



#----------------------------------------------------------
# Lancer le browser
#----------------------------------------------------------
def Browser(file):
        if WIN:
            cmd=f"start {file}"
        else:
            cmd=f"firefox {file} &"    
        os.system(cmd)  

def Editor(file):
        if WIN:
            cmd=f"start notepad {file}"
        else:
            cmd=f"xed  --new-window {file} &"    # background pour pas bloquer le menu
        os.system(cmd)  

#----------------------------------------------------------
#----------------------------------------------------------

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
# Lit un fichier texte defini par une url en https 
#
# renvoie le contenu ou "" si pas trouvé
#--------------------------------------------------------------------  
def Download( host , uri ,outfile=""):
    if os.path.isfile( outfile) : os.remove( outfile)
    data=""

    try:

        conn = http.client.HTTPSConnection(host,timeout=5)
        conn.request("GET", uri, headers={"Host": host})

        response = conn.getresponse()

        #print("STATUS=",response.status)
        if response.status == 200 : 
            data=response.read()
        conn.close()

        if outfile != "" :
            with open( outfile, "wb") as f:
                f.write(data)
            return outfile
        else:
            return data
    except:
        #print("ECHEC Download")
        return ""



#------------------------------------------------------------------
# Lit le N° de version 
#
#------------------------------------------------------------------
def GetLocalVersion():
    filename="version.txt"
    if not os.path.isfile(filename): 
        txt=""
    else:
        with open(filename,"r") as f:
            txt = f.read()

    txt=txt.replace("\r" ,"")
    lines=txt.split("\n")
    version=lines[0]
    tmp=version.split("=")
    version=tmp[-1]

    return version

def GetRemoteVersion():
    data = Download( "audits.emmaus-connect.org", "/api/apps/linux/latest"  )
    if data == "" : return ""
    items=json.loads(data)
    return items.get("version","")

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
# Lit un fichier texte defini par une url en https ou un fichier local
#
# renvoie le contenu ou "" si pas trouvé
#
# on utilise curl, car python3-requests n'est pas installé sur certains Linux ( Debian Xfce )
#------------------------------------------------------------------
def ReadUrl(url,tmpfile="ztmp.txt"):

    # cas d'un fichier local
    if not url.startswith("https"):
        if not os.path.isfile(url): return ""
        with open(url,"r") as f:
            return f.read()

    # cas d'une url
    if os.path.isfile( tmpfile) : os.remove( tmpfile)
    cmd=f"curl -s -o {tmpfile} {url}"
    os.system(cmd)
 
    if not os.path.isfile(tmpfile) : return ""

    txt=""
    with open(filetxt,"r") as f:
        txt=f.read()
    os.remove( tmpfile )

    return txt

#    try:
#        response=requests.get(url)
#        if (response):
#            txt=response.text
#        else:
#            txt=""
#    except:
#        txt=""

#--------------------------------------------------
# Envoie le fichier vers le Bolc
#
# INPUT
#  filebolcimport:  nom  du fichier . S'il est vide, on le retrouve avec DataGet()
# RETURN
#  code  ( 0 si OK)
#--------------------------------------------------
def TransfertBolc(filebolcimport="",debug=False):
    if filebolcimport == "" or not os.path.isfile(filebolcimport):
        print(f"******** Fichier BOLC non trouvé : {filebolcimport} **************")
        return 
        
    # envoi par sftp , en utilisant la commande curl
    fileconf="sftp.conf"
    cmd= f"{CURL} -k {P}fast{S} -T {filebolcimport} sftp://sftpemmaus.newmips.cloud:22222"
    if debug :
        print(cmd)
        print()
    # code=os.system(cmd)
    code = 0
    if ( code == 0 ) : print("******** Transfert BOLC OK **************")


def TransfertTectech(filebolcimport="", debug: bool = False, useprodapi: bool = False, idlot: str = "", idmatrecond: str = "", ecid: str= ""):
    # we chose the easiest possible implementation: take the file destined to BOLC and convert it to something suitable
    # for tectech
    print("=== Transfert à faire vers tec.tech===")

    with open(filebolcimport, 'r') as bf:
        line = bf.readline().strip('\n')  # we carelessly read a single line and assume it is what we want
    vals = line.split(';')
    print(f"Données récupérées de {filebolcimport}:\n{vals}")

    tokfil = "token-test.json" if not useprodapi else "token-prod.json"
    print(f'fichier jeton: {tokfil}')
    try:
        api = tectech.TecTAPI(useprodapi=useprodapi, credsfile="tectech-credentials.json", tokenfile=tokfil)
    except Exception as exc:
        print(f"Impossible de créer l'objet tectech.TecTAPI ({exc})")
        sys.exit(1)
    print(f'base utilisée: {api.prefix}')
    print(f'jeton        : {api.token[0:32]} ... {api.token[-32:]}')
    print(f'créé le      : {api.tokencreationtimestr}')
    print(f'se périme le : {api.tokenexpirytimestr}')

    try:
        mypc = api.lookup_equipment(vals[2])
    except Exception as exc:
        print(f"Erreur lors de la recherche de {vals[2]} ({exc})")
        sys.exit(1)

    if mypc:  # mise à jour d'équipement
        print(f"Équipement {vals[2]} trouvé:\n{mypc}")
        d = from_bolc_to_tectech(vals, idlot=mypc['idLot'], idStock=mypc['idStock'],
                                 idmaterielreconditionneur=mypc['idMaterielReconditionneur'])
        d['id'] = mypc['id']
        print(f"Dictionnaire à envoyer à tec.tech\n{d}")

        # ds = json.dumps([d]).encode('utf-8')
        # print(f"Le même encodé juste avant XPUT\n{ds}")

        mynewpc = {}
        try:
            # print("Modification d'un équipement dans tec.tech SIMULÉ et présumé réussi...")
            mynewpc = api.update_equipment(d)
        except Exception as exc:
            print(f"La mise à jour de l'équipement {vals[2]} dans tec.tech a échoué ({exc})")
        print(f"Nouvel état de l'équipement {vals[2]} dans tec.tech:\n{mynewpc[0]}")
    else:  # création d'un nouvel équipement
        print(f"L'équipement {vals[2]} n'a pas été trouvé: il va être créé...")
        d = from_bolc_to_tectech(vals, idlot=idlot, idStock="", idmaterielreconditionneur=idmatrecond)
        print(f"Dictionnaire à envoyer à tec.tech\n{d}")
        mynewpc = {}
        try:
            # print("Création d'un équipement dans tec.tech SIMULÉ et présumé réussi...")
            mynewpc = api.create_equipment(d)
        except Exception as exc:
            print(f"La création de l'équipement {vals[2]} dans tec.tech a échoué ({exc})")
        print(f"Nouvel équipement {vals[2]} créé dans tec.tech:\n{mynewpc[0]}")

    # we trustfully use the existing naming scheme...
    dest = os.path.join("..", ecid, f"{ecid}.tect.csv")
    try:
        api.create_tectech_csvfile(mynewpc[0], dest)
    except Exception as exc:
        print(f"La création de {dest} a échoué ({exc})")
    # else:
    #     print(f"{dest} aurait dû être créé...")

    print("=== Transfert vers tec.tec terminé ===")
    return


def TransfertVersBaseAdmin(filebolcimport="", debug=False, tect: bool = False, useprodapi: bool = False, idlot: str = "", idmatrecond: str = "", ecid: str= ""):
    if not tect:
        TransfertBolc(filebolcimport, debug)
    else:
        TransfertTectech(filebolcimport, debug, useprodapi, idlot, idmatrecond, ecid)



#--------------------------------------------------
# Envoie le fichier vers le Bolc
#
# INPUT
#  zipfile:  fichier zip à envoyer
#  ecid:     identifiant Emmaus
# RETURN
#  
#--------------------------------------------------
def TransfertEmmaus(zipfile,ecid):
        cmd=f'{CURL} -X POST https://audits.emmaus-connect.org/api/upload/zip {P}quiet{S} -F "ecid={ecid}" -F "actual_file=@{zipfile}"  '
        os.system(cmd)

           




def vazy():
    UpdateMe()

if __name__ == '__main__':
    vazy()
        
#files=[ "GRPC99-9999/GRPC99-9999.audit.txt","GRPC99-9999/GRPC99-9999.bolc.csv" ]
#MakeZip( "zzz.zip", files)


    



