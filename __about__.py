__version__ = "4.3.0"
__title__ = 'Audit de PC Linux pour Emmaüs Connect'

__description__: str = """
L'outil est basé sur l'audit Linux jadis développé par Bernard et qui fonctionnait avec le BOLC.

L'abandon du BOLC au profit de tec.tech a rendu nécessaire une adaptation. Celle-ci a pour point de départ la dernière version publiée par Bernard, la 2.7.1., et les versions qui lui correspondent commencent à 3.0.0.

Il y avait deux points d'entrée principaux dans l'outil originel:
  .menu.sh
  .audit.sh
menu.sh étant capable d'activer la fonction d'audit.

Les changements introduits à partir de 3.0.0 ne concernent que la partie "audit" et l'envoi de données générées par celle-ci vers le site administratif (désormais tec.tech). Ainsi, les fonctions autres que l'audit fournies par menu.sh restent théoriquement utilisables en l'état. 
"""

__authors__ = [
    {"name": "Bernard", "email": "bmaison@emmaus-connect.org", "versions": "<=2.7.1"},
    {"name": "Paul", "email": "pghaleb@emmaus-connect.org", "versions":  ">=3.0.0"},
]
# ', '.join([f"{_['name']} <{_['email']}> [{_['versions']}]" for _ in __authors__])

__copyright__ = 'Emmaüs Connect 2023-2026'
__url__ = 'https://github.com/__TBD__'

