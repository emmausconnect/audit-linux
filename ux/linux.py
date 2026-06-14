###################################################################################
#
# Actions techniques pour l'Audit Linux
#
#
# Utilisation:
#  import linux.py
#  infos=AuditMe()
#
#
##################################################################################

import os
import subprocess
import sys

from trace import Tracer
_logger = Tracer().get_logger()

TMPDISK="/tmp"                                  # répertoire où sont générés les fichiers temporaires.

FILESCAN="scan-linux.txt"  # fichier contenant le scan système qu'on copie sur drop.tf
TMPSCANFILE=os.path.join( TMPDISK ,  FILESCAN)           # fichier d'export de la commande inxi

# Variables globales
# infosdict={}  # donnees technique issues du scan systeme

def SystemScan(inxifile):
    result = subprocess.run(["sudo", "inxi", "-F", "-xx", "-y1", "--color", "0"], capture_output=True, text=False, check=False)
    with open(f"{inxifile}", "wb") as f:
        f.write(result.stdout)
    pass

#------------------------------------------
# Execute l'audit technique : lancement du scan, decodage 
#  renvoie infos : dictionnaire de valeurs
#------------------------------------------
from ux.characteristics import get_machine_infos
def AuditMe(datestamp: str):
    infostmp =  get_machine_infos(datestamp=datestamp)
    _logger.debug(infostmp)
    SystemScan(TMPSCANFILE)  # keep those legacy parts around for now
    return infostmp


def asroot() -> (str, str):
    if suu := os.environ.get("SUDO_USER"):
        return True, f"/home/{suu}"
    else:
        return False, os.environ.get("HOME")


def userhomeparams() -> (bool, str, int, int):
    suu, hdir = asroot()
    if suu:
        return True, hdir, int(os.environ.get("SUDO_UID")), int(os.environ.get("SUDO_GID"))
    else:
        return False, hdir, -1, -1


def chown_to_user(somepath: str) -> None:
    # this is a convenience function; in our context, we don't really care if the ownership change fails
    _logger.debug(f"chown_to_user({somepath=}")

    insudo, enduserrootdir, enduseruid, endusergid = userhomeparams()
    _logger.debug(f"{insudo=}, {enduserrootdir=}, {enduseruid=}, {endusergid=}")

    if os.path.isfile(somepath):
        if insudo:
            cmd = f"chown {enduseruid}:{endusergid} {somepath}"
            _logger.debug(cmd)
            os.system(cmd)
    if os.path.isdir(somepath):
        if insudo:
            cmd = f"chown -R {enduseruid}:{endusergid} {somepath}"
            _logger.debug(cmd)
            os.system(cmd)


def get_user_dirs() -> dict[str, str]:
    keys = ["desktop", "download", "documents"]
    udirs = dict.fromkeys(keys, "")
    for k in keys:
        try:
            udirs[k] = subprocess.check_output(["xdg-user-dir", f"{k.upper()}"], text=True).strip()
        except (RuntimeError, Exception):
            pass
    return udirs


#-----------------------------------------------------------
# Copie une liste de fichiers/répertoires sur le Bureau
#   renvoie False si bureau pas trouvé
#
#-----------------------------------------------------------
def Copy2Desktop(files):

    _logger.debug(f"Copy2Desktop({files = })")
    suu, enduserrootdir = asroot()
    BUREAU = get_user_dirs()["desktop"]

    # _logger.debug(f"{BUREAU=}, {insudo=}, {enduserrootdir=}, {enduseruid=}, {endusergid=}")
    _logger.debug(f"{BUREAU=}, {enduserrootdir=}")
    if BUREAU != "":
        for name in files:
            dst = os.path.join(BUREAU, name)
            if os.path.isfile(name):
                CopyFile(name, BUREAU)
                chown_to_user(f"{BUREAU}{os.sep}{os.path.basename(dst)}")
            if os.path.isdir(name):
                CopyDir(name, BUREAU)
                chown_to_user(f"{dst}")
    else:
        return False

    return True


def CopyFile2File( src, dst):
    os.system( f"cp {src} {dst}" )

def CopyFile( src, dstdir):
    os.system( f"rsync {src} {dstdir}/" )

def CopyDir( src, dstdir):
    os.system( f"rsync -r {src} {dstdir}/" )


if  __name__ == "__main__":
    infos_ = AuditMe("19610306.103088")

    # infos_ = infos
    # infos_ = get_machine_infos()

    sys.exit(0)
