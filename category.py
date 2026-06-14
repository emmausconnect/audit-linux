import os
import subprocess
import urllib.request, urllib.error

from trace import Tracer
_logger = Tracer().get_logger()

type thresholdTable = tuple[list[tuple[int, int | str]], int]

def _make_lookup(threshold_table: thresholdTable):
    def lookup(val):
        ll = threshold_table[0]
        if val < ll[0][0]:
            return ll[0][1]
        for i in range(len(ll)):
            if val >= ll[i][0]:
                continue
            else:
                return ll[i][1]
        return threshold_table[1]
        # for i, m in enumerate(threshold_table[0]):
        #     if val >= m[0]:
        #         return threshold_table[i - 1]  # m[1]
        # return threshold_table[1]
    return lookup

_ramTable: thresholdTable = ([(4, 0), (5, 1), (8, 2), (16, 3)], 4)
_ssdTable: thresholdTable = ([(64, 0), (128, 1), (200, 2), (500, 3)], 4)
_hddTable: thresholdTable = ([(160, 0), (256, 1), (1000, 2)], 3)
_cpuTable: thresholdTable = ([(2000, 0), (3500, 1), (5000, 2), (7000, 3)], 4)
_ram_mark_lookup = _make_lookup(_ramTable)
_ssd_mark_lookup = _make_lookup(_ssdTable)
_hdd_mark_lookup = _make_lookup(_hddTable)
_cpu_mark_lookup = _make_lookup(_cpuTable)

# _catTable: thresholdTable = ([(4, 5000), (6, 5001), (8, 5002), (11, 5003), (9999, 5004)], 5004)
# _intcat_to_strcat = {5000: "D", 5001: "C", 5002: "B", 5003: "A", 5004: "PREMIUM"}

def _cat_lookup(val: int) -> str:
    if val < 4:
        return "D"
    elif val < 6:
        return "C"
    elif val < 8:
        return "B"
    elif val < 11:
        return "A"
    else:
        return "PREMIUM"

# _cat_mark_lookup = make_lookup(_catTable)

# x = _ram_mark_lookup(9)

_DISKTYPES = {"HDD", "SSDATA", "SSDNVME"}

class ComputeCategoryError(Exception):
    def __init__(self, msg=""):
        super().__init__(msg)

class ComputeCategoryNoSuchType(ComputeCategoryError):
    pass

def compute_category(cpumark: int, ramsiz: int, dsksiz: int, dsktyp: str) -> tuple[int, int, int, int, str, str]:
    if dsktyp not in _DISKTYPES:
        raise ComputeCategoryNoSuchType(f"Le type de disque doit être dans {{{_DISKTYPES}}}")

    ncpu = _cpu_mark_lookup(cpumark)
    nram = _ram_mark_lookup(ramsiz)
    if dsktyp == "HDD":
        ndsk = _hdd_mark_lookup(dsksiz)
    else:
        ndsk = _ssd_mark_lookup(dsksiz)

    ntot = ncpu + nram + ndsk

    details = "notes de base:"
    cat = _cat_lookup(ntot)
    details += f" CPU={ncpu}, RAM={nram}, DSK({dsktyp})={ndsk}, catégorie={cat}"

    if cpumark < 3500:
        if dsktyp == "HDD":
            if cat in {"PREMIUM", "A", "B"}:
                cat = "C"
                details += f"; CPU<3500 et HDD ==> catégorie = {cat}"
        else:
            if cat in {"PREMIUM", "A"}:
                cat = "B"
                details += f"; CPU<3500 et SSD ==> catégorie = {cat}"
    else:
        if dsktyp == "SSDNVME":
            ntot += 1
            cat = _cat_lookup(ntot)
            details += f"; SSDNVME ==> catégorie = {cat}"

    return ncpu, nram, ndsk, ntot, cat, details


def add_data_to_remote_logfile(lf: str, data: str) -> None:
    # This function should never raise an Exception: any unexepcted event should be reported through the logging
    # mechanism
    # By convention, 'data' is a JSON dictionary string + ending LF character
    # Note: to reinitialize the remote file:
    #   echo '{"content": "Categorization failure event file - please do not erase"}' > categorization.log
    #   cat categorization.log
    #   curl -X 'POST'   'https://audits.emmaus-connect.org/api/upload/audit' \
    #     -H 'accept: application/json' -H 'X-API-Key: 0972dd.............7d65f' \
    #     -H 'Content-Type: multipart/form-data' -F 'region=GRENOBLE' \
    #     -F 'actual_file=@categorization.log;type=text/plain'
    # You can then double-check by loading https://audits.emmaus-connect.org/GRENOBLE/categorization.log in a browser
    rlf = "https://audits.emmaus-connect.org/GRENOBLE/" + lf
    try:
        # read the existing remote logfile
        llf, headers = urllib.request.urlretrieve(url=rlf)
        # add the data
        with open(llf, 'a', encoding="utf-8") as of_:
            of_.write(data)
        # write the remote logfile back
        xak = "0972dd465681b821e567d65f"
        desturl = "https://audits.emmaus-connect.org/api/upload/audit"
        cmd = ["curl", "-s", "-X", "POST", f"{desturl}",
               "-F", f"actual_file=@{llf};type=text/plain;charset=utf-8;filename={lf}",
               "-H", "Content-Type: multipart/form-data",
               "-F", "region=GRENOBLE",
               "-H", f"X-API-Key: {xak}"
               ]
        result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"},
                                check=False)  # we don't really care if this particular transfer fails
        _logger.debug(f"result.stderr = {result.stderr}")
        _logger.debug(f"result.stdout = {result.stdout}")
        pass
    except Exception as exc:
        _logger.debug(f"Could not write the categorization data to the remote file ({exc})")
        pass
    return


def _test_add_data_to_remote_logfile():
    lf = "categorization.log"
    add_data_to_remote_logfile(lf, '{"vers": "Ô rage! Ô désespoir! Ô vieillesse ennemie!"}\n')
    pass



if __name__ == "__main__":
    import sys
    import csv

    # testing add_data_to_remote_logfile
    # _test_add_data_to_remote_logfile()

    def cattime(d: str) -> tuple[str, ...]:
        return tuple(d.split('/')[::-1])

    def readcsvdict(ff: str, delimiter=';') -> dict:
        dd = {}
        with open(ff, 'r', encoding="utf-8-sig") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)
            line = 2
            for row in reader:
                dd[line] = row
                line += 1
        return dd

    def read_bolcdata(ff: str) -> dict:
        return readcsvdict(ff)

    def isintstr(s: str) -> bool:
        try:
            i = int(s)
        except ValueError:
            return False
        else:
            return True

    def check_against_bolc():
        BOLCFILE = "/home/ghalebp/tmp/check_bolc_to_tec_tech/bolc-all-pc-20260212-utf8.csv"
        dbolc = read_bolcdata(BOLCFILE)
        wantedkeys = {'ID Emmaüs Connect', 'Catégorie', 'Type disque 1', 'Taille disque 1', 'RAM', 'Indice CPU',
                      'Date de prise en charge', 'Date de vente'}
        wantedcategories = {'A', 'B', 'C', 'D', 'PREMIUM'}
        wanteddisktypes = {'NVMe': "SSDNVME",
                       'SSD': "SSDATA",
                       'NVME SSD': "SSDNVME",
                       'SATA SSD': "SSDATA",
                       'NVME': "SSDNVME",
                       'HDD': "HDD"}
        # clean the data set up first
        for n in dbolc:
            dbolc[n]['KEEP'] = True
            # basic clean-up
            for k in wantedkeys:
                dbolc[n][k] = dbolc[n][k].strip()
            # we want valid figures for disk sizes, RAM, CPU marks and disk types, and at leaset one date
            if (not isintstr(dbolc[n]['Taille disque 1'])
                or not isintstr(dbolc[n]['RAM'])
                or not isintstr(dbolc[n]['Indice CPU'])
                or dbolc[n]['Type disque 1'] not in wanteddisktypes
                or {dbolc[n]['Date de prise en charge'], dbolc[n]['Date de vente']} <= {'-'}
                or dbolc[n]['Catégorie'] not in wantedcategories):
                dbolc[n]['KEEP'] = False
                continue
            # standardize disk types
            dbolc[n]['DISKTYPWAS'] = dbolc[n]['Type disque 1']
            dbolc[n]['Type disque 1'] = wanteddisktypes[dbolc[n]['Type disque 1']]
            # turn strings to int where used
            dbolc[n]['Indice CPU'] = int(dbolc[n]['Indice CPU'])
            dbolc[n]['RAM'] = int(dbolc[n]['RAM'])
            dbolc[n]['Taille disque 1'] = int(dbolc[n]['Taille disque 1'])
            # we need at least one date
            d1 = dbolc[n]['Date de prise en charge']
            d2 = dbolc[n]['Date de vente']
            if d1 == '-':
                dbolc[n]['CATTIME'] = d2
            else:
                if d2 == '-':
                    dbolc[n]['CATTIME'] = d1
                else:
                    dbolc[n]['CATTIME'] = d1 if cattime(d1) > cattime(d2) else d2

        # process a clean data set
        nhit = 0
        nmiss = 0
        latestmiss = cattime('01/01/2001')
        for n in dbolc:
            if not dbolc[n]['KEEP']:
                continue
            row = dbolc[n]
            c, r, d, t = row['Indice CPU'], row['RAM'], row['Taille disque 1'], row['Type disque 1']
            myc, myr, myd, myntot, mycat, mydet = compute_category(c, r, d, t)
            if mycat == row['Catégorie']:
                nhit += 1
            else:
                nmiss += 1
                print(f"{n=:<3}  {row['Catégorie']=:<7}  {mycat=:<7} ({row['CATTIME']}, {row['DISKTYPWAS']})"
                      f"  {c=:<5}({myc}) {r=:<2}({myr}) {d=:<4}({myd}) {t=:<7} {myntot=} {mydet=}")
                if cattime(row['CATTIME']) > latestmiss:
                    latestmiss = cattime(row['CATTIME'])
                else:
                    # print(f"...left alone")
                    pass
                pass

        pass

    # check_against_bolc()

    def check_on_data_set():
        vtestram_ = {1, 3, 4, 5, 6, 8, 14, 16, 20}
        vtestssd_ = {50, 64, 100, 128, 200, 250, 500, 700}
        vtesthdd_ = {12, 160, 250, 256, 1000, 1500}
        vtestcpu_ = {1800, 2000, 3000, 3500, 4000, 5000, 6000, 7000, 7100}


        # setsSSD_ = [("ram", vtestram_), ("cpu", vtestcpu_), ("ssd", vtestssd_)]
        # setsHDD_ = [("ram", vtestram_), ("cpu", vtestcpu_), ("hdd", vtesthdd_)]

        vrowsSSD_ = [(vc_, vr_, vd_) for vc_ in vtestcpu_ for vr_ in vtestram_ for vd_ in vtestssd_]
        vrowsHDD_ = [(vc_, vr_, vd_) for vc_ in vtestcpu_ for vr_ in vtestram_ for vd_ in vtesthdd_]

        fieldnames_ = ["cpu", "ram", "dsk", "typ", "ntot", "cat", "det"]

        def go_for(csvf, vrows, typ):
            for _ in vrows:
                typ = typ
                ntot, cat, det = compute_category(_[0], _[1], _[2], typ)
                drow = dict(zip(fieldnames_, [_[0], _[1], _[2], typ, ntot, cat, det]))
                csvf.writerow(drow)
                print(drow)
                pass

        destfile_ = "toutecategories.csv"
        with open(destfile_, 'w', encoding='utf-8') as csvfile_:
            writer_ = csv.DictWriter(csvfile_, fieldnames=fieldnames_, delimiter=',')
            writer_.writeheader()
            go_for(writer_, vrowsSSD_, "SSDATA")
            go_for(writer_, vrowsSSD_, "SSDNVME")
            go_for(writer_, vrowsHDD_, "HDD")


    c, r, d, t = 6100, 8, 256, "SSDNVME"
    myc, myr, myd, myntot, mycat, mydet = compute_category(c, r, d, t)
    sys.exit(0)
