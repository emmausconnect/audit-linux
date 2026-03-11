import sys
import json
import urllib.request, urllib.error, urllib.parse
import logging

# http.client.HTTPConnection.debuglevel = 1
USERAGENT = "curl/8.11.1"  # "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0"
MARKSAPIURL = "https://audits.emmaus-connect.org/api/cpu"

_logger = logging.getLogger("cpumark")
_logger.level = logging.DEBUG
_hdlr = logging.StreamHandler()
_formatter = logging.Formatter('[%(levelname)-7s] %(filename)s(%(lineno)d): %(message)s')
_hdlr.setFormatter(_formatter)
_logger.addHandler(_hdlr)

# $ curl -sk 'https://audits.emmaus-connect.org/api/cpu/Intel(R)%20Core(TM)%20i5-1145G7%20@%202.60GHz%20(1.50%20GHz)' | jq -r '.'
# {
#   "error": false,
#   "mark": "9266",
#   "cpustr": "Intel(R) Core(TM) i5-1145G7 @ 2.60GHz (1.50 GHz)",
#   "hint": "CLEVER_1",
#   "cpuscsv": "cpumarks-20251113.120116.csv",
#   "linenum": "2521",
#   "line": "Intel Core i5-1145G7 @ 2.60GHz",
#   "details": [],
#   "version": "1.0.1"
# }


def FindCpuMark(cpuname: str):
    """
    cpuname is a string like the one returned by "lshw" command, e.g.:
    "Intel(R) Core(TM) i5-1145G7 @ 2.60GHz (1.50 GHz)"
    The function returns a string with either a non-zero mark (success) or 0
    The function never raises exceptions - all incidents are reported trhough the logging mechanism
    """
    headers = {'Accept': 'application/json', 'Content-type': 'application/json', 'User-Agent': f'{USERAGENT}'}

    url = f"{MARKSAPIURL}/{urllib.parse.quote(cpuname)}"
    req = urllib.request.Request(url=url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            body = response.read()
            status = response.status
            # code = response.code
    except (urllib.error.HTTPError, urllib.error.URLError, Exception) as exc:
        errmsg = f'La recherche de {cpuname} a échoué ({exc})'
        _logger.error(errmsg)
        return ""
    if status != 200:
        errmsg = f'La recherche de {cpuname} a échoué (status: {status})'
        _logger.error(errmsg)
        return ""

    try:
        d = json.loads(body.decode("utf-8"))
        _logger.debug(f"Answer received from cpumarks site:\n{d}")
    except Exception as exc:
        _logger.warning(f"Exception {exc} raised while decoding cpumarks site's answer")
        return ""

    if d['error']:
        return ""
    else:
        return d['mark']


if  __name__ == "__main__":
    p = "Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz"
    m = FindCpuMark(p)
    print(f"Mark >{m}< found for '{p}'")

    p = "prout de gros caca"
    m = FindCpuMark(p)
    print(f"Mark >{m}< found for '{p}'")

    sys.exit(0)
