import os
import sys
import json
import platform
import subprocess
import glob
import re
from math import sqrt

from trace import Tracer
_logger = Tracer().get_logger()

GiB = 1024 * 1024 * 1024
GB = 1000 * 1000 * 1000

type infosDict = dict[str, str | int | list[tuple[str, int, str, str]]]

def _search_for_dict(j, key: str = "id", value: str = " core"):
    ret = dict()
    if isinstance(j, dict):
        if j.get(key)== value:
            return j
        else:
            for k in j:
                if d := _search_for_dict(j[k], key, value):
                    return d
    elif isinstance(j, list):
        for l in j:
            if d := _search_for_dict(l, key, value):
                return d
            else:
                continue
    return ret


def _search_for_root(d: dict) -> dict | None:
    retd = dict()
    _logger.debug(f"_search_for_root({d=})")
    if not d['mountpoint']:
        if d.get('children'):
            for _ in d.get('children'):
                retd = _search_for_root(_)
                if retd:
                    _logger.debug(f"_search_for_root ==> {retd}")
                    return retd
        else:
            _logger.debug(f"_search_for_root ==> {retd}")
            return retd
    else:
        if d['mountpoint'] == '/':
            _logger.debug(f"_search_for_root ==> {d}")
            return d


def _look_for_webcam() -> list:
    retd = []
    for dev in glob.glob("/dev/video*"):
        try:
            out = subprocess.check_output(["udevadm", "info", "--query=property", "--name", dev], text=True)
            if "ID_V4L_CAPABILITIES=:capture:" in out:
                retd.append(dev)
        except subprocess.CalledProcessError:
            pass
    return retd


def _get_platform_info(fil: str) -> infosDict:
    entries = ['Type', 'Marque', 'Modele', 'NumeroSerie', 'Processeur', 'RAM']
    retd: dict[str, str | int] = dict.fromkeys(entries, "")
    retd["RAM"] = 0

    # result = subprocess.run(["LC_ALL=C", "sudo", "lshw", "-json"], capture_output=True, text=True)
    # "sudo" is mandatory, otherwise we don't get the 'vendor' key on which our processing is based
    result = subprocess.run(["sudo", "lshw", "-json"], capture_output=True, text=True,
                            env={**os.environ, "LC_ALL": "C"}, check=False)
    with open(fil, "w") as f:
        f.write(result.stdout)
    _logger.debug(f"Les données générales (lshw) on été sauvegardées dans {fil}")

    # with open(fil, 'r') as jf:
    #     j = json.load(jf)
    j = json.loads(result.stdout)

    # look for the system type: branded or DIY
    d = _search_for_dict(j, key="class", value="system")

    if not d or (d.get('product') != "VirtualBox" and "vendor" not in d):
        return retd

    descr = d['description'].lower()
    retd["Type"] = "Fixe" if ("desktop" in descr or "all" in descr) else "Portable"

    if d["vendor"] == 'System manufacturer' or d["product"] == "VirtualBox":
        # not a branded system: very likely with home-assembled desktops
        dd = _search_for_dict(j, key="id", value="core")
        retd["Marque"] = dd['vendor']
        retd["Modele"] = dd['product']
        retd["NumeroSerie"] = dd['serial']
    else:
        retd["Marque"] = d['vendor']
        retd["Modele"] = d['product']
        retd["NumeroSerie"] = d['serial']

    # look for the processor string
    d = _search_for_dict(j, key="id", value="cpu")
    if not d or not d.get('class') == 'processor':
        retd["Processeur"] = 'processeurInconnu'
    else:
        retd["Processeur"] = d['product']

    # look for the RAM size
    d = _search_for_dict(j, key="id", value="memory")
    try:
        retd["RAM"] = int(d['size'] / GiB)
    except (KeyError, Exception):
        retd["RAM"] = 0


    return retd


def _get_disk_info(fil: str) -> infosDict:

    def disk_type(dinf: dict[str, str | int]) -> str:
        return 'HDD' if dinf['rota'] else 'NVME' if dinf['tran'] == 'nvme' else 'SSD'

    def disk_size(dinf: dict[str, str | int]) -> int:
        return int(dinf['size'] / GB)

    result = subprocess.run(["sudo", "lsblk", "-Jb",
                             "-o", "name,type,size,rota,tran,vendor,model,fstype,mountpoint,serial"],
                            capture_output=True, text=True, check=False)
    with open(fil, "w") as f:
        f.write(result.stdout)
    _logger.debug(f"Les données relatives aux disques (lsblk) on été sauvegardées dans {fil}")

    bdevs = json.loads(result.stdout)['blockdevices']

    ## notes:
    ##   -SIZE is in bytes (-b)
    ##   -ROTA is 1/true for HDD
    ##   -when ROTA is 0/false, TRAN is
    ##       +"sata" for SATA
    ##       +"nvme" for NVMe

    # keep only 'sata' and 'nvme' devices
    bdevs = [_ for _ in bdevs if _['type'] == 'disk' and _['tran'] in {"sata", "nvme"}]
    retd: infosDict = {"DisqueTaille": 0, "DisqueRef": "", "DisqueID": "", "DisqueType": ""}
    snmaindisk = "inconnu"

    if bdevs:
        # we focus only on the device on which the / partition is mounted
        x = None
        rootdev = dict()
        for rootdev in bdevs:
            if x := _search_for_root(rootdev):
                break

        if not x:
            _logger.warning("Le point de montage de / n'a pas été trouvé. Bizarre...")

        if rootdev:
            retd: infosDict = {
                "DisqueTaille": disk_size(rootdev),
                "DisqueRef": rootdev['model'],
                "DisqueID": f"/dev/{rootdev['name']}",
                "DisqueType": disk_type(rootdev)
            }
            snmaindisk = rootdev.get('serial', "inconnu")

    _logger.debug(f"infos disque principal = {retd}")

    result = subprocess.run(["sudo", "lsblk", "-Jbd",
                             "-o", "name,type,size,rota,tran,vendor,model,fstype,mountpoint,serial"],
                            capture_output=True, text=True, check=False)
    disks = json.loads(result.stdout)['blockdevices']
    _logger.debug(disks)
    disks = [_ for _ in disks if _['type'] == 'disk' and _['tran'] in {"sata", "nvme"} and _['serial'] != snmaindisk]

    retd["AutresDisques"] = [(disk_type(_), disk_size(_), _['model'], _['serial']) for _ in disks]

    return retd


def _get_monitor_size() -> str:
    try:
        out = subprocess.check_output(["xrandr", "--current"], text=True)
        m = re.search(r" connected.*? (\d+)mm x (\d+)mm", out)
        if m:
            x = int(m.group(1)) / 10.0
            y = int(m.group(2)) / 10.0
            return f"{round(sqrt(x ** 2 + y ** 2) / 2.54, 1)}"
    except Exception as exc:
        _logger.warning(f"Échec lors du calcul de la taille de l'écran ({exc})")
        pass
    return ""


def _get_battery_health() -> str:
    try:
        out = subprocess.check_output(["inxi", "-Bcy1"], text=True)
        # out = "Battery:\n  ID-1: BAT0\n    charge: 22.5 Wh (94.1%)\n    condition: 23.9/23.9 Wh (100.0%)\n"
        out = out.split('\n')
        _logger.debug(f"Recherche de l'indice de santé de la batterie dans {out}")
        condl = [l for l in out if "condition" in l]
        if not condl or len(condl) > 1:
            return ""
        condl = condl[0].strip()
        # condl looks like 'condition: 23.9/23.9 Wh (100.0%)'
        m = re.match(r'.*\((?P<healthpercentage>(.*%))\)$', condl)
        if not m:
            _logger.warning(f"Échec du calcul de l'état de la batterie ({condl})")
            return ""
        return m.groupdict()['healthpercentage']
    except Exception as exc:
        _logger.warning(f"Exception lors du calcul de l'état de la batterie ({exc})")
        pass

    return ""


def get_machine_infos(datestamp: str) -> infosDict:
    lshwfile = f"/tmp/lshw-{datestamp}.json"
    lsblkfile = f"/tmp/lsblk-{datestamp}.json"

    dplf = _get_platform_info(lshwfile)
    dblk = _get_disk_info(lsblkfile)
    dcam = _look_for_webcam()
    mon = _get_monitor_size()
    bat = _get_battery_health()

    dall: infosDict = {
        **dplf,
        **dblk,
        "Systeme": platform.freedesktop_os_release()['PRETTY_NAME'],
        "LINUX": "oui",
        "Webcam": "oui" if dcam else "non",
        "Ecran": mon,
        "Batterie": bat
    }

    # the legacy categorization function requires that NVME information be stored differently
    if dall["DisqueType"] == "NVME":
        dall["DisqueType"] = "SSD"
        dall["NVME"] = "oui"

    return dall


if __name__ == "__main__":
    infos_ = get_machine_infos("19610306.103088")
    _logger.debug(infos_)
    sys.exit(0)

