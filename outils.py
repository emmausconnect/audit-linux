#################################################################
#  outils divers
#
################################################################

import sys,os
import json
import zipfile
import subprocess
# import http.client  # actually no longer used
import urllib.request, urllib.error

from trace import Tracer
_logger = Tracer().get_logger()

import tectech
from convert_bolc_to_tectech import from_bolc_to_tectech

ECAPPSAPIURL = "https://audits.emmaus-connect.org/api"
USERAGENT = "curl/8.11.1"  # "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0"

TMPDISK="/tmp"                                  # répertoire où sont générés les fichiers temporaires.

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


def Browser(file):
    cmd=f"firefox {file} &"
    os.system(cmd)


def Editor(file):
    cmd=f"xed  --new-window {file} &"    # background pour pas bloquer le menu
    os.system(cmd)


def MakeZip( zipname, files ):
    with zipfile.ZipFile( zipname , 'w') as z:
        for filename in files:
            base=os.path.basename(filename)
            z.write( filename, base)


def DownloadFile(url: str, afile: str, siz: int) -> str:
    headers = {
        # 'Accept': 'application/json',
        # 'Content-type': 'application/json',
        'User-Agent' : f'{USERAGENT}'
    }
    req = urllib.request.Request(url=url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read()
            status = response.status
    except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
        errmsg = f'Le téléchargement de la dernière version a échoué ({exc})'
        return errmsg
    if status != 200:
        errmsg = f'Le téléchargement de la dernière version a échoué (status={status})'
        return errmsg
    if len(body) != siz:
        errmsg = "Le fichier téléchargé de la dernière version n'a pas la bonne taille"
        errmsg += f" (attendue: {siz}, obtenue: {len(body)})"
        return errmsg

    try:
        with open(afile, 'wb') as of:
            of.write(body)
    except Exception as exc:
        errmsg = f"La sauvegarde de la dernière version a échoué ({exc})"
        return errmsg

    return "SUCCESS"


def GetRemoteVersionInfo() -> (str, str, str, int):
    defret = "", "", "", 0
    vinfourl = f"{ECAPPSAPIURL}/apps/linux/latest"
    headers = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
        'User-Agent' : f'{USERAGENT}'
    }
    req = urllib.request.Request(url=vinfourl, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read()
            status = response.status
    except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
        _logger.warning(f'La recherche de la dernière version a échoué ({exc})')
        return defret
    if status != 200:
        _logger.warning(f'La recherche de la dernière version a échoué (status={status})')
        return defret
    d = json.loads(body.decode("utf-8"))
    return d['version'], d['final_filename'], d['download_url'], d['size']


def TransfertTectech(filebolcimport="", useprodapi: bool = False, idlot: str = "", idmatrecond: str = "", ecid: str= ""):
    # we chose the easiest possible implementation: take the file destined to BOLC and convert it to something suitable
    # for tectech
    _logger.info("=== Transfert à faire vers tec.tech ===")

    with open(filebolcimport, 'r') as bf:
        line = bf.readline().strip('\n')  # we carelessly read a single line and assume it is what we want
    vals = line.split(';')
    _logger.info(f"Données récupérées de {filebolcimport}:\n{vals}")

    tokfil = "token-test.json" if not useprodapi else "token-prod.json"
    _logger.info(f'fichier jeton: {tokfil}')
    try:
        api = tectech.TecTAPI(useprodapi=useprodapi, credsfile="tectech-credentials.json", tokenfile=tokfil)
    except Exception as exc:
        _logger.error(f"Impossible de créer l'objet tectech.TecTAPI ({exc})")
        sys.exit(1)
    _logger.info(f'base utilisée: {api.prefix}')
    _logger.info(f'jeton        : {api.token[0:32]} ... {api.token[-32:]}')
    _logger.info(f'créé le      : {api.tokencreationtimestr}')
    _logger.info(f'se périme le : {api.tokenexpirytimestr}')

    try:
        mypc = api.lookup_equipment(vals[2], vals[14])
    except Exception as exc:
        _logger.error(f"Erreur lors de la recherche de {vals[2]}/{vals[14]} ({exc})")
        sys.exit(1)

    if mypc:  # mise à jour d'équipement
        _logger.info(f"Équipement {vals[2]}/{vals[14]} trouvé:\n{mypc}")
        d = from_bolc_to_tectech(vals, idlot=mypc['idLot'], idstock=mypc['idStock'],
                                 idmaterielreconditionneur=mypc['idMaterielReconditionneur'])
        d['id'] = mypc['id']
        _logger.info(f"Dictionnaire à envoyer à tec.tech\n{d}")

        # ds = json.dumps([d]).encode('utf-8')
        # _logger.info(f"Le même encodé juste avant XPUT\n{ds}")

        mynewpc = {}
        try:
            # _logger.info("Modification d'un équipement dans tec.tech SIMULÉ et présumé réussi...")
            mynewpc = api.update_equipment(d)
        except Exception as exc:
            _logger.error(f"La mise à jour de l'équipement {vals[2]}/{vals[14]} dans tec.tech a échoué ({exc})")
        _logger.info(f"Nouvel état de l'équipement {vals[2]}/{vals[14]} dans tec.tech:\n{mynewpc[0]}")
    else:  # création d'un nouvel équipement
        _logger.info(f"L'équipement {vals[2]}/{vals[14]} n'a pas été trouvé: il va être créé...")
        d = from_bolc_to_tectech(vals, idlot=idlot, idstock="", idmaterielreconditionneur=idmatrecond)
        _logger.info(f"Dictionnaire à envoyer à tec.tech\n{d}")
        mynewpc = {}
        try:
            # _logger.info("Création d'un équipement dans tec.tech SIMULÉ et présumé réussi...")
            mynewpc = api.create_equipment(d)
        except Exception as exc:
            _logger.error(f"La création de l'équipement {vals[2]}/{vals[14]} dans tec.tech a échoué ({exc})")
        _logger.info(f"Nouvel équipement {vals[2]}/{vals[14]} créé dans tec.tech:\n{mynewpc[0]}")

    # we trustfully use the existing naming scheme...
    dest = os.path.join("..", ecid, f"{ecid}.tect.csv")
    try:
        api.create_tectech_csvfile(mynewpc[0], dest)
    except Exception as exc:
        _logger.error(f"La création de {dest} a échoué ({exc})")
    # else:
    #     _logger.info(f"{dest} aurait dû être créé...")

    _logger.info("=== Transfert vers tec.tec terminé ===")
    return


def TransfertEmmaus(zf, ecid):
    xak = "0972dd465681b821e567d65f"
    desturl = "https://audits.emmaus-connect.org/api/upload/zip"
    cmd = ["curl", "-s", "-X", "POST", f"{desturl}", "-F", f"ecid={ecid}",
           "-F", f"actual_file=@{zf}", "-H", f"X-API-Key: {xak}"]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"})
    _logger.debug(f"result.stderr = {result.stderr}")
    _logger.debug(f"result.stdout = {result.stdout}")

if __name__ == '__main__':
    pass
