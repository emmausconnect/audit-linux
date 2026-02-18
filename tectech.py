import os
import sys
import json
import urllib.request, urllib.error
import argparse
import logging
from datetime import datetime, timedelta
import re
import tectech_data

UNIQUESHA1 = "2999a9e7680a2fa2a152d65dbd43be43f9c7e03e"

PREPRODAPIURL = "https://tec-tech.osc-fr1.scalingo.io/api"
PRODAPIURL = "https://tec-tech-prod.osc-fr1.scalingo.io/api"


_logger = logging.getLogger("tectech")
_logger.level = logging.DEBUG
_hdlr = logging.StreamHandler()
_formatter = logging.Formatter('[%(levelname)-7s] %(filename)s(%(lineno)d): %(message)s')
_hdlr.setFormatter(_formatter)
_logger.addHandler(_hdlr)


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

        uniquetmpfile = f"token-prod.json" if "prod" in prefix else f"token-test.json"

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
    def __init__(self, msg):
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
    def lookup_equipment_by_idesn(cls, idesn: str) -> dict:
        # look for a "materiel" in tec.tech, based only on idEsn
        epmateriel = "materiel"
        limit = 2
        maturl = f"{TecTAPI.__selected_prefix}/{epmateriel}?idEsn={idesn}&page=1&limit={limit}"
        headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'inclureGroupesLies': 'true',
            'Authorization': f'Bearer {TecTAPI.__token}'
        }
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

        if nb == 0:
            errmsg = f'La recherche de {idesn} a échoué'
            raise TecTapiEquipmentNotFound(errmsg)

        if nb > 1:
            errmsg = f"La recherche de {idesn} a trouvé plus d'une ({nb}) occurences"
            # _logger.error(errmsg)
            raise TecTapiDuplicateEquipmentFound(errmsg)

        return d['data'][0]

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
    def update_equipment_by_idesn(cls, mat: dict) -> dict:
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
        try:
            previous = cls.lookup_equipment_by_idesn(idesn)
        except TecTapiError as exc:
            raise exc

        # run a sanity-check on the fields to be updated
        for f in cls.__ro_fields:
            if f in mat and mat[f] != previous[f]:
                raise TecTapiReadOnlyField(f'Mise à jour du champ {f} interdite')

        maturl = f"{TecTAPI.__selected_prefix}/materiel"
        headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
            'inclureGroupesLies': 'true',
            'Authorization': f'Bearer {TecTAPI.__token}'
        }

        matup = {x: mat[x] for x in mat if x == 'id' or (mat[x] and x not in TecTAPI.__ro_fields)}

        if isinstance(matup['statut'], dict):
            matup['statut'] = matup['statut'].get('libelle', '')

        if m := cls._check_enumerated_values(matup):
            raise TecTapiForbiddenEnumeratedValue(m)

        reqdata = [matup]
        payload = json.dumps(reqdata).encode("utf-8")
        req = urllib.request.Request(url=maturl, headers=headers, data=payload, method="PUT")
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read()
                status = response.status
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
            errmsg = f'La mise à jour de {idesn} a échoué ({exc})'
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
        return mat


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

    if args_.verbose or not args_.production:
        _logger.setLevel(logging.INFO)

    for i_ in sorted(vars(args_).items()):
        _logger.info(f'{i_[0]:<12}: {i_[1]}')

    api_ = TecTAPI(args_.production, args_.creds_file, args_.token_file)

    _logger.info(f'base utilisée: {api_.prefix}')
    _logger.info(f'jeton        : {api_.token[0:32]} ... {api_.token[-32:]}')
    _logger.info(f'créé le      : {api_.tokencreationtimestr}')
    _logger.info(f'se périme le : {api_.tokenexpirytimestr}')

    mypc_ = api_.lookup_equipment_by_idesn("GRPC25-0322")

    fmt_ = "%Y-%m-%d %H:%M:%S"
    updtime_ = datetime.strftime(datetime.now(), fmt_)
    mypc_["commentaire"] = f'Modified by PaulG on {updtime_}'
    idesn_ = mypc_["idEsn"]

    mynewpc_ = api_.update_equipment_by_idesn(mypc_)

    sys.exit(0)
