import os
import sys
import json
import urllib.request, urllib.error
import argparse
from datetime import datetime, timedelta
import re
import csv

from trace import Tracer
_logger = Tracer().get_logger()

import tectech_data
from ux.linux import chown_to_user

# import http.client
# http.client.HTTPConnection.debuglevel = 1

UNIQUESHA1 = "2999a9e7680a2fa2a152d65dbd43be43f9c7e03e"

PREPRODAPIURL = "https://tec-tech.osc-fr1.scalingo.io/api"
PRODAPIURL = "https://tec-tech-prod.osc-fr1.scalingo.io/api"
USERAGENT = "curl/8.11.1"  # "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0"

class IdesnParser:
    __esnspat = "|".join(['BX', 'CR', 'GR', 'LI', 'LV', 'LY', 'MA', 'MB', 'RO', 'SD', 'ST', 'VI'])
    __crexp = re.compile(fr'^(?P<esn>({__esnspat}))(?P<typ>(PC|TA))' + r'(?P<ann>(\d{2}))-(?P<num>(\d{4}))$',
                         re.ASCII)

    @classmethod
    def parse(cls, idesn: str) -> dict:
        m = re.match(cls.__crexp, idesn)
        if m:
            return m.groupdict()
        return {}


class Token:
    __is_initialized = False
    __tokenfile = ""
    __value = ""
    __type = ""
    __creationtimestr = ""
    __expirytime = datetime.now() - timedelta(seconds=3600)  # by default, force an expired token
    __expirytimestr = ""
    __filepath = ""
    __datefmt = "%Y-%m-%d %H:%M:%S"

    @property
    def value(self):
        return self.__value

    @property
    def type(self):
        return self.__type

    @property
    def expirytime(self):
        return self.__expirytime

    @property
    def expirytimestr(self):
        return self.__expirytimestr

    @property
    def creationtimestr(self):
        return self.__creationtimestr

    @property
    def filepath(self):
        return self.__filepath

    @staticmethod
    def init(prefix: str, tokenfile: str, clientid: str, clientsec: str):
        if Token.__is_initialized:
            return

        uniquetmpfile = "token-prod.json" if "prod" in prefix else "token-test.json"

        if not tokenfile:
            # # this is a trick: when no token file is specified, we force a non-existing file so that the Token
            # # construction code will force the creation of a token file in /tmp
            # tokenfile = f"/tmp/{UNIQUESHA1[::-1]}"  # a non-existing file
            tokenfile = uniquetmpfile
            _logger.warning(f"Fichier jeton manquant ==> forcé à {tokenfile}")

        tfpath = os.path.realpath(os.path.normpath(tokenfile))

        if os.path.isfile(tfpath) and os.access(tfpath, os.R_OK):
            _logger.info(f"Fichier token {tfpath} existe")
            if Token._loadfromfile(tfpath):
                # found a non-expired token
                _logger.info(f"Fichier token {tfpath} valide chargé avec succès")
            else:
                # the token we have is no longer valid
                _logger.info(f"Fichier token {tfpath} chargé mais invalide")
                if os.access(tfpath, os.W_OK):
                    # if the token file is writeable, refresh it
                    _logger.info(f"Écriture du fichier token {tfpath}")
                    Token._getnewtoken(prefix, tfpath, clientid, clientsec)
                else:
                    # create a new token file in /tmp so that we have a chance to reuse it
                    _logger.info(f"Écriture du fichier token {uniquetmpfile}")
                    Token._getnewtoken(prefix, uniquetmpfile, clientid, clientsec)
        else:
            if (os.path.exists(tfpath) and os.access(tfpath, os.W_OK)) or os.access(os.path.dirname(tfpath), os.W_OK):
                # if the token file is writeable, create it or update it
                _logger.info(f"Écriture du fichier token {tfpath}")
                Token._getnewtoken(prefix, tfpath, clientid, clientsec)
            else:
                # create a new token file so that we have a chance to reuse it
                _logger.info(f"Écriture du fichier token {uniquetmpfile}")
                Token._getnewtoken(prefix, uniquetmpfile, clientid, clientsec)

    def __init__(self, prefix: str, tokenfile: str, clientid: str, clientsec: str):
        Token.init(prefix, tokenfile, clientid, clientsec)
        Token.__is_initialized = True

    @staticmethod
    def _isfilestillvalid() -> bool:
        return datetime.now() <= Token.__expirytime

    @staticmethod
    def _loadfromfile(tokenfile: str) -> bool:
        try:
            with open(tokenfile, 'r') as jf:
                d = json.load(jf)

            creationtime = datetime.fromtimestamp(os.stat(tokenfile).st_mtime)
            expirytime = creationtime + timedelta(seconds=int(d["expires_in"] - 3600))

            if datetime.now() > expirytime:
                return False

            Token.__expirytime = expirytime
            Token.__expirytimestr = datetime.strftime(expirytime, Token.__datefmt)
            Token.__creationtimestr = datetime.strftime(creationtime, Token.__datefmt)
            Token.__value = d["access_token"]
            Token.__type = d["token_type"]
            Token.__filepath = tokenfile
        except Exception as exc:
            _logger.error(f'Impossible de charger le token depuis {tokenfile} ({exc})')
            return False
        return True

    @staticmethod
    def _getnewtoken(prefix: str, tokenfile: str, clientid: str, clientsec: str) -> bool:
        epauth = "auth-token"
        authurl = f"{prefix}/{epauth}"
        payload = {"client_id": clientid, "client_secret": clientsec}
        authdata = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url=authurl, data=authdata,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req) as response:
            body = response.read()

        with open(tokenfile, "w", encoding="utf-8") as f:
            json.dump(json.loads(body.decode("utf-8")), f, indent=2)

        return Token._loadfromfile(tokenfile)


class TecTapiError(Exception):
    def __init__(self, msg=""):
        super().__init__(msg)

class TecTapiEquipmentNotFound(TecTapiError):
    pass

class TecTapiDuplicateEquipmentFound(TecTapiError):
    pass

class TecTapiBadIdesnFormat(TecTapiError):
    pass

class TecTapiReadOnlyField(TecTapiError):
    pass

class TecTapiUpdateFailed(TecTapiError):
    pass

class TecTapiForbiddenEnumeratedValue(TecTapiError):
    pass

class TecTapiBolcFileConversionError(TecTapiError):
    pass

class TecTapiMissingMandatoryValueError(TecTapiError):
    pass

class TecTapiUsingIdOnEquipmentCreation(TecTapiError):
    pass

class TecTapiCreationFailed(TecTapiError):
    pass

class TecTapiCsvFileCreationFailed(TecTapiError):
    pass

class TecTAPI:
    __is_initialized = False
    __token = ""
    __selected_prefix = ""
    __token_expiry_time_str = ""
    __token_creation_time_str = ""
    __fields = {  # at the time of writing...
        'id', 'statut', 'typeMateriel', 'numeroSerie', 'IMEI1', 'IMEI2', 'idMaterielReconditionneur', 'idEsn', 'model',
        'marque', 'processeur', 'typeDisqueDur1', 'tailleDisqueDur1', 'typeDisqueDur2', 'tailleDisqueDur2', 'RAM',
        'categorie', 'lecteurDVD', 'webcam', 'commentaire', 'idLot', 'systemeExploitation', 'idStock', 'idGroupe',
        'createdAt', 'updatedAt', 'reconditionneur'}
    __ro_fields = {'id', 'idLot', 'idStock', 'idGroupe', 'reconditionneur', 'createdAt', 'updatedAt'}
    __updatable_fields = __fields - __ro_fields
    __commonheaders = {
        'Accept': 'application/json',
        'Content-type': 'application/json',
        'User-Agent' : f'{USERAGENT}'
    }

    @property
    def token(self):
        return self.__token

    @property
    def prefix(self):
        return self.__selected_prefix

    @property
    def tokenexpirytimestr(self):
        return self.__token_expiry_time_str

    @property
    def tokencreationtimestr(self):
        return self.__token_creation_time_str


    def __init__(self, useprodapi: bool, credsfile: str, tokenfile: str):
        if TecTAPI.__is_initialized:
            return

        cf = os.path.realpath(os.path.normpath(credsfile))
        with open(cf, 'r') as jfile:
            d = json.load(jfile)

        TecTAPI.__selected_prefix = PRODAPIURL if useprodapi else PREPRODAPIURL
        tok = Token(TecTAPI.__selected_prefix, tokenfile, d['client_id'], d['client_secret'])
        TecTAPI.__token = tok.value
        TecTAPI.__token_expiry_time_str = tok.expirytimestr
        TecTAPI.__token_creation_time_str = tok.creationtimestr
        TecTAPI.__is_initialized = True


    @classmethod
    def lookup_equipment_by_id(cls, tectid: str) -> dict:
        # look for a "materiel" in tec.tech, based 'id'
        epmateriel = "materiel"
        maturl = f"{TecTAPI.__selected_prefix}/{epmateriel}/{tectid}"
        headers = cls.__commonheaders | {'Authorization': f'Bearer {cls.__token}'}
        req = urllib.request.Request(url=maturl, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                status = response.status
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
            errmsg = f'La recherche directe de {tectid} par id a échoué ({exc})'
            raise TecTapiEquipmentNotFound(errmsg) from exc

        if status != 200:
            errmsg = f'La recherche directe de {tectid} par id a échoué (status: {status})'
            raise TecTapiEquipmentNotFound(errmsg)

        d = json.loads(body.decode("utf-8"))

        # nb is certainly 1!
        return d


    @classmethod
    def lookup_equipment_by_idmatrec(cls, idmatrec: str) -> dict:
        # look for a "materiel" in tec.tech, based only on idMaterielReconditionneur
        epmateriel = "materiel"
        limit = 2
        maturl = f"{TecTAPI.__selected_prefix}/{epmateriel}?idMaterielReconditionneur={idmatrec}&page=1&limit={limit}"
        headers = cls.__commonheaders | {'Authorization': f'Bearer {cls.__token}'}
        req = urllib.request.Request(url=maturl, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                status = response.status
                # code = response.code
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
            errmsg = f'La recherche de {idmatrec} par idMaterielReconditionneur a échoué ({exc})'
            # _logger.error(errmsg)
            raise TecTapiEquipmentNotFound(errmsg) from exc

        if status != 200:
            errmsg = f'La recherche de {idmatrec} par idMaterielReconditionneur a échoué (status: {status})'
            # _logger.error(errmsg)
            raise TecTapiEquipmentNotFound(errmsg)

        d = json.loads(body.decode("utf-8"))

        nb = int(d['total'])

        if nb > 1:
            errmsg = f"La recherche de {idmatrec} par idMaterielReconditionneur a trouvé plus d'une ({nb}) occurences"
            # _logger.error(errmsg)
            raise TecTapiDuplicateEquipmentFound(errmsg)

        if nb == 0:
            return {}

        # nb is certainly 1!
        return d['data'][0]


    @classmethod
    def lookup_equipment_by_numser(cls, numser: str) -> dict:
        # look for a "materiel" in tec.tech, based only on idMaterielReconditionneur
        epmateriel = "materiel"
        limit = 2
        maturl = f"{TecTAPI.__selected_prefix}/{epmateriel}?numeroSerie={numser}&page=1&limit={limit}"
        headers = cls.__commonheaders | {'Authorization': f'Bearer {cls.__token}'}
        req = urllib.request.Request(url=maturl, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                status = response.status
                # code = response.code
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
            errmsg = f'La recherche de {numser} par idMaterielReconditionneur a échoué ({exc})'
            # _logger.error(errmsg)
            raise TecTapiEquipmentNotFound(errmsg) from exc

        if status != 200:
            errmsg = f'La recherche de {numser} par numeroSerie a échoué (status: {status})'
            # _logger.error(errmsg)
            raise TecTapiEquipmentNotFound(errmsg)

        d = json.loads(body.decode("utf-8"))

        nb = int(d['total'])

        if nb > 1:
            errmsg = f"La recherche de {numser} par numeroSerie a trouvé plus d'une ({nb}) occurences"
            _logger.error(errmsg)
            dd = d['data']
            errmsg = ', '.join([f"({dd[_]['id']}, ns={dd[_]['numeroSerie']}, idmatrec={dd[_]['idMaterielReconditionneur']}, idesn={dd[_]['idEsn']})" for _ in [0, 1]])
            _logger.error(errmsg)
            raise TecTapiDuplicateEquipmentFound(errmsg)

        if nb == 0:
            return {}

        # nb is certainly 1!
        return d['data'][0]


    @classmethod
    def lookup_equipment(cls, idesn: str, numeroserie: str="") -> dict:
        _logger.info(f"Recherche de l'équipement {idesn=}, {numeroserie=}")
        # look for a "materiel" in tec.tech, based only on idEsn and numeroSerie
        epmateriel = "materiel"
        limit = 2
        maturl = f"{TecTAPI.__selected_prefix}/{epmateriel}?idEsn={idesn}&page=1&limit={limit}"
        headers = cls.__commonheaders | {'Authorization': f'Bearer {cls.__token}'}
        req = urllib.request.Request(url=maturl, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                status = response.status
                # code = response.code
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
            errmsg = f'La recherche de {idesn} a échoué ({exc})'
            # _logger.error(errmsg)
            raise TecTapiEquipmentNotFound(errmsg) from exc

        if status != 200:
            errmsg = f'La recherche de {idesn} a échoué (status: {status})'
            # _logger.error(errmsg)
            raise TecTapiEquipmentNotFound(errmsg)

        d = json.loads(body.decode("utf-8"))

        nb = int(d['total'])

        if nb > 1:
            errmsg = f"La recherche de {idesn} a trouvé plus d'une ({nb}) occurences"
            # _logger.error(errmsg)
            raise TecTapiDuplicateEquipmentFound(errmsg)

        if nb == 1:
            _logger.info(f"L'équipement {idesn}/{numeroserie} a été trouvé par son idEsn")
            return d['data'][0]

        # nb is certainly 0!
        _logger.warning(f'La recherche de {idesn} par idEsn a échoué')

        # try to look the equipment up based on idMaterielReconditionneur
        try:
            d = cls.lookup_equipment_by_idmatrec(idesn)
        except (TecTapiEquipmentNotFound, Exception) as exc:
            raise TecTapiEquipmentNotFound from exc

        if d:
            _logger.info(f"L'équipement {idesn}/{numeroserie} a été trouvé par son idMaterielReconditionneur==idEsn")
            return d

        _logger.warning(f'La recherche de {idesn} par idMaterielReconditionneur a échoué')

        if not numeroserie:
            return {}

        # tenter une recherche sur numeroSerie
        try:
            d = cls.lookup_equipment_by_numser(numeroserie)
        except (TecTapiEquipmentNotFound, Exception) as exc:
            raise TecTapiEquipmentNotFound from exc
        else:
            _logger.info(f"L'équipement {idesn}/{numeroserie} a été trouvé par son numeroSerie")
            return d


    @classmethod
    def _check_enumerated_values(cls, mat: dict) -> str:

        # returns an empty string if all is fine, otherwise a message with details
        tocheck = set(mat.keys()) & set(tectech_data.allowed_values.keys())
        ret = ""
        for k in tocheck:
            if mat[k] not in tectech_data.allowed_values[k]:
                ret += f'La valeur "{mat[k]}" n\'est pas autorisée comme "{k}"\n'
        return ret.strip()

    @classmethod
    def update_equipment(cls, mat: dict) -> dict:
        # This method updates an EXISTING equipment:
        #   -"mat" must contain at least a valid idEsn: if not the method raises an Exception
        #   -it also contains the <field, value> pairs that must be updated on the server side
        #      .each such field must exist in the data model (i.e., belong to the set of known fields - 26 at the time
        #      of writing)
        #      .the method does not check thouroughly the "values" since their syntax is not very strictly defined
        #      at this time

        # check the format of idEsn
        idesn = mat.get('idEsn')
        if not idesn or not IdesnParser().parse(idesn):
            errmsg = f"L'idEsn {idesn} est mal formé"
            raise TecTapiBadIdesnFormat(errmsg)

        # check that the equipment already exists
        numser = mat.get('numeroSerie')
        try:
            previous = cls.lookup_equipment(idesn, numser)
        except TecTapiError as exc:
            raise TecTapiEquipmentNotFound from exc

        # run a sanity-check on the fields to be updated
        for f in cls.__ro_fields:
            if f in mat and mat[f] != previous[f]:
                raise TecTapiReadOnlyField(f'Mise à jour du champ {f} interdite')

        maturl = f"{TecTAPI.__selected_prefix}/materiel"
        headers = cls.__commonheaders | {'Authorization': f'Bearer {cls.__token}'}

        matup = {x: mat[x] for x in mat if x == 'id' or (mat[x] and x not in TecTAPI.__ro_fields)}

        if isinstance(matup['statut'], dict):
            matup['statut'] = matup['statut'].get('libelle', '')

        if m := cls._check_enumerated_values(matup):
            raise TecTapiForbiddenEnumeratedValue(m)

        reqdata = [matup]
        payload = json.dumps(reqdata).encode("utf-8")
        _logger.debug(f"payload = >{payload}<")
        req = urllib.request.Request(url=maturl, headers=headers, data=payload, method="PUT")
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                status = response.status
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            # errmsg = f'Erreur serveur lors de la mise à jour de {idesn} ({exc.code}: {exc.reason}/{exc.read().decode("utf-8")})'
            errmsg = f'Erreur serveur lors de la mise à jour de {idesn} ({exc.code}: {exc.reason})'
            # _logger.error(errmsg)
            raise TecTapiUpdateFailed(errmsg) from exc
        except Exception as exc:
            errmsg = f'La mise a jour de {idesn} a échoué ({exc})'
            # _logger.error(errmsg)
            raise TecTapiUpdateFailed(errmsg) from exc

        if status not in [201]:  # is 200 valid here?
            errmsg = f'La recherche de {idesn} a échoué (status: {status})'
            # _logger.error(errmsg)
            raise TecTapiUpdateFailed(errmsg)

        return json.loads(body.decode("utf-8"))


    @classmethod
    def create_equipment(cls, mat: dict) -> dict:
        # This method creates an equipment item.
        # The following fields are mandatory:
        #    "typeMateriel": "ORDINATEUR_PORTABLE",        # mandatory by tec.tech docs
        #    "idMaterielReconditionneur": "EM_2510_0049",  # mandatory by tec.tech docs
        #    "statut": "PRET_A_DISTRIBUER",                # mandatory by tec.tech docs
        #    "idStock": "S-0094",                          # mandatory by tec.tech docs
        #    "numeroSerie": "FDCDXS2",                     # mandatory by tec.tech docs
        #    "idLot": "L-0048"                             # mandatory by tec.tech docs
        # This field is optional for tec.tech, mandatory for ESN Grenoble:
        #    "idEsn": "GRPC25-0322"                       # not mandatory at this time
        #
        # "mat" contains the <field, value> pairs that must be set on the server side:
        #    .each such field must exist in the data model (i.e., belong to the set of known fields - 26 at the time
        #    of writing)
        #    .the method does not check thouroughly the "values" since their syntax is not very strictly defined
        #    at this time

        # check that the mandatory fields are here
        mandfields = {'idEsn', 'typeMateriel', 'idMaterielReconditionneur', 'statut', 'idStock', 'idLot', 'numeroSerie'}
        if not mandfields < set(mat.keys()):
            mandfieldvals = ', '.join ([f"{_}: {mat[_]}" for _ in mandfields])
            errmsg = f"Au moins un champ obligatoire manque pour la création ({mandfieldvals})"
            raise TecTapiMissingMandatoryValueError(errmsg)

        # check that we are not accidentally updating an existing equipment
        if 'id' in mat:
            errmsg = f"On ne peut spécifier l'identifiant TECT lors d'une création {mat['id']}"
            raise TecTapiUsingIdOnEquipmentCreation(errmsg)

        # check the format of idEsn
        idesn = mat['idEsn']
        if not IdesnParser().parse(idesn):
            errmsg = f"L'idEsn {idesn} est mal formé"
            raise TecTapiBadIdesnFormat(errmsg)

        maturl = f"{TecTAPI.__selected_prefix}/materiel"
        headers = cls.__commonheaders | {'Authorization': f'Bearer {cls.__token}'}

        _logger.debug(mat)
        if m := cls._check_enumerated_values(mat):
            raise TecTapiForbiddenEnumeratedValue(m)

        reqdata = [mat]
        payload = json.dumps(reqdata).encode("utf-8")
        _logger.debug(f"payload = >{payload}<")
        req = urllib.request.Request(url=maturl, headers=headers, data=payload, method="PUT")
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                status = response.status
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            errmsg = f'Erreur serveur lors de la création de {idesn} ({exc.code}: {exc.reason})'
            # _logger.error(errmsg)
            raise TecTapiCreationFailed(errmsg) from exc
        except Exception as exc:
            errmsg = f'La création de {idesn} a échoué ({exc})'
            # _logger.error(errmsg)
            raise TecTapiCreationFailed(errmsg) from exc

        if status not in [201]:  # is 200 valid here?
            errmsg = f'La création de {idesn} a échoué (status: {status})'
            # _logger.error(errmsg)
            raise TecTapiCreationFailed(errmsg)

        return json.loads(body.decode("utf-8"))

    @classmethod
    def create_tectech_csvfile(cls, mat: dict, destfile: str):
        # trustfully assume that 'dest' can be (over)written, focus on the data
        # some fields must be removed from 'mat', others must be tweaked
        _logger.info(f"Écriture de {destfile} en cours")
        try:
            if isinstance(mat['statut'], dict):
                mat['statut'] = mat['statut']['libelle']
                pass
            mat['webcam'] = "OUI" if mat['webcam'] else "NON"
            mat['lecteurDVD'] = "OUI" if mat['lecteurDVD'] else "NON"
            d = {tectech_data.internal_to_external_fnames[_]: mat[_] for _ in
                 ['typeMateriel',
                  'idMaterielReconditionneur',
                  'statut',
                  'idStock',
                  'numeroSerie',
                  'IMEI1',
                  'IMEI2',
                  'idEsn',
                  'model',
                  'marque',
                  'processeur',
                  'typeDisqueDur1',
                  'tailleDisqueDur1',
                  'typeDisqueDur2',
                  'tailleDisqueDur2',
                  'RAM',
                  'systemeExploitation',
                  'categorie',
                  'lecteurDVD',
                  'webcam',
                  'commentaire'
                  ]
                 }
            with open(destfile, 'w', encoding='utf-8') as csvfile_:
                fieldnames = list(d.keys())
                writer = csv.DictWriter(csvfile_, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                writer.writerow(d)
            chown_to_user(destfile)
            _logger.info(f"...écriture de {destfile} terminée")
        except Exception as exc:
            errmsg = f"La création du fichier CSV a échoué ({exc})"
            raise TecTapiCsvFileCreationFailed(errmsg) from exc

        return


if __name__ == "__main__":

    parser_ = argparse.ArgumentParser()

    parser_.add_argument("-v", "--verbose", default=False, action='store_true',
                         help="Rendre l'exécution verbeuse")

    parser_.add_argument("-d", "--debug", default=False, action='store_true',
                         help="Afficher les traces d'exécution (aide à la mise au point)")

    parser_.add_argument("-p", "--production", default=False, action='store_true',
                         help="Utiliser le tec.tech de prod")

    parser_.add_argument("-c", "--creds-file", type=str, required=True,
                         help="Fichier contenant les identifiants pour accéder à tec.tech")

    parser_.add_argument("-t", "--token-file", type=str, required=False,
                         help="Fichier où est déjà (ou bien sera) enregistré le jeton d'accès")

    args_ = parser_.parse_args()

    if args_.debug:
        args_.verbose = True

    # if args_.verbose or not args_.production:
    #     _logger.setLevel(logging.INFO)

    for i_ in sorted(vars(args_).items()):
        _logger.info(f'{i_[0]:<12}: {i_[1]}')

    api_ = TecTAPI(args_.production, args_.creds_file, args_.token_file)

    _logger.info(f'base utilisée: {api_.prefix}')
    _logger.info(f'jeton        : {api_.token[0:32]} ... {api_.token[-32:]}')
    _logger.info(f'créé le      : {api_.tokencreationtimestr}')
    _logger.info(f'se périme le : {api_.tokenexpirytimestr}')

    fmt_ = "%Y-%m-%d %H:%M:%S"
    updtime_ = datetime.strftime(datetime.now(), fmt_)

    dros_ = "GRPC26-9999"
    sn_ = "2CE347155K"
    id_ = "M-5639"
    # This is for the tester to make sure that the equipment is properly configured for the test at TECT side
    idesnS_ = [dros_, ""]
    idmatrecS_ = [dros_, f"EM_{dros_}"]
    numserS_ = [sn_, ""]
    cas_ = [(a, b, c) for a in idesnS_ for b in idmatrecS_ for c in numserS_]
    for _ in cas_:
        _logger.info(f"     idEsn={_[0]:11}  idMaterielReconditionneur={_[1]:14}  numeroSerie={_[2]}")
    # (output redacted)
    # There are 4 relevant test cases
    #      idEsn=GRPC26-9999  idMaterielReconditionneur=GRPC26-9999     numeroSerie=2CE347155K
    #      idEsn=GRPC26-9999  idMaterielReconditionneur=EM_GRPC26-9999  numeroSerie=2CE347155K
    #      idEsn=             idMaterielReconditionneur=GRPC26-9999     numeroSerie=2CE347155K
    #      idEsn=             idMaterielReconditionneur=EM_GRPC26-9999  numeroSerie=2CE347155K
    # N/A  idEsn=             idMaterielReconditionneur=EM_GRPC26-9999  numeroSerie=
    # N/A  idEsn=             idMaterielReconditionneur=GRPC26-9999     numeroSerie=
    # N/A  idEsn=GRPC26-9999  idMaterielReconditionneur=EM_GRPC26-9999  numeroSerie=
    # N/A  idEsn=GRPC26-9999  idMaterielReconditionneur=GRPC26-9999     numeroSerie=

    cas_ = [(a, b, c) for a in idesnS_ for b in idmatrecS_ for c in numserS_ if c]
    for _ in cas_:
        _logger.info(f"Make sure that idEsn={_[0]:11}  idMaterielReconditionneur={_[1]:14}  numeroSerie={_[2]} on TECT side")
        try:
            d_ = api_.lookup_equipment_by_id(id_)
            _logger.info(f"{d_=}")
            theid_ = _[0] if _[0] else _[1][3:]
            thesn_ = _[2]
            x_ = api_.lookup_equipment(theid_)
            y_ = api_.lookup_equipment(theid_, thesn_)
        except (TecTapiError, Exception) as exc_:
            _logger.error(f"Got ({exc_})")
            pass
        else:
            _logger.info(f"{x_=}, {y_=}")

    pc_emh_ = "MAPC26_0033"
    pc_emh_numser_ = "PF1P0TFE"
    mypc_emh_ = api_.lookup_equipment(pc_emh_, pc_emh_numser_)

    pc26_ = "MAPC26-2026"  #"MBPC26-0106"
    mypc26_ = api_.lookup_equipment(f"{pc26_}")
    if mypc26_:
        # we need to fo through a modification to get a clean dictionary, ready to generate teh CSV file
        mypc26_["commentaire"] = f'Modified by PaulG on {updtime_}'
        mypc26_["idEsn"] = pc26_
        mynewpc26_ = api_.update_equipment(mypc26_)
        api_.create_tectech_csvfile(mynewpc26_[0], f"{pc26_}.tect.csv")

    pass

    pcpr_ = "GRPC26-9999"
    grpc26_9999_ = api_.lookup_equipment(pcpr_)
    if grpc26_9999_:
        _logger.info("GRPC26-9999 existe déjà; on va faire une mise à jour")
        mygrpc26_9999_ = api_.update_equipment(grpc26_9999_)
    else:  # il s'agit d'une création
        d_ = {'idLot': 'L-0048', 'idMaterielReconditionneur': 'EM_2602_9999', 'idEsn': pcpr_,
              'typeMateriel': 'ORDINATEUR_PORTABLE', 'categorie': 'B', 'statut': 'PRET_A_DISTRIBUER', 'marque': 'APPLE',
              'model': 'MacBookPro12,1', 'numeroSerie': 'C02SX6JJFVH4', 'processeur': 'Intel Core i5-5257U',
              'typeDisqueDur1': 'SSD', 'tailleDisqueDur1': 251, 'RAM': 9, 'systemeExploitation': 'Linux',
              'idStock': 'S-0094',
              'commentaire': 'cpumark: 2837 / Batterie: 75.4% / Écran: 13.3 / Observations:  / PondTech: 0 / PondEsth: 0 / Bénévole: Gérard / Origine: ESN'}
        ds_ = json.dumps([d_]).encode('utf-8')

        mygrpc26_9999_ = api_.create_equipment(d_)
        pass


    mypc25_ = api_.lookup_equipment("GRPC25-0322")
    mypc26_ = api_.lookup_equipment("MBPC26-0106")  #   "GRPC26-1961")


    sys.exit(0)
