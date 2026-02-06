# audit-linux (adapté pour tec.tech)

Ceci est la version de l'audit Linux jadis développé par Bernard Maison, qui fonctionnait avec le BOLC et qui a été adapté pour permettre l'envoi des données d'audit vers tec.tech au lieu du BOLC.

Pour mémoire, il se base sur la [dernière version publiée par Bernard](https://audits.emmaus-connect.org/api/apps/linux/download/2.7.1), la 2.7.1

# Limitations actuelles

- l'outil ne permet pas de créer un nouveau matériel dans tec.tech; il faut donc que le matériel audité ait été créé au préalable dans tec.tech, avec un "ID ESN" (```idEsn``` dans l'API) conforme à la notation utilisée par l'outil dans le contexte BOLC. Par exemple: ```GRPC26-0888```

- l'outil est encore en cours de test; il est fortement recommandé de l'utiliser seulement sur la base tec.tech de test (voir ci-dessous)

- certaines des données qui allaient dans le BOLC n'ont pas de point de chute naturel dans tec.tech. L'outil les regroupe dans le champ "commentaire" de tec.tech.

# Obtenir l'outil



# Utiliser l'outil

L'outil fonctionne encore avec le BOLC. Il crée localement les mêmes fichiers quepour le BOLC. La seule différence est que, sur demande, au lieu d'émettre un fichier vers le BOLC, il émet vers tec.tech, une requête de modification du "materiel"

## Avec le BOLC

L'outil modifié s'utilise de la même façon qu'auparavant. Se reporter au fichier README.txt.

## Avec tec.tech

L'outil s'appelle directement avec le script audit.sh. Le script menu.sh ne doit pas être utilisé.

Il faut d'abord créer, au même niveau que audit.sh, un fichier JSON ```tectech-credentials.json``` contenant les identifiants que vous voulez utiliser pour accéder à tec.tech. Ça ressemble à:
```
{
    "client_id": "UbBdc5bp***********KaS57mQwIleVm",
    "client_secret": "5uSXDqTZbOUoQ42N9jkIiyW**************YH3N5wOn-YCVBah0F7iVHrHMCnX"
}
```
Il y a ensuite deux possibilités pour lancer l'audit:

- avec un idEsn (recommandé)
```
sudo python3 -B audit.py <IDESN> TECTECH [PROD|TEST]
```
avec IDESN respectant le modèle:
```
^(BX|CR|GR|LI|LV|LY|MA|MB|RO|SD|ST|VI)(PC|TA)(\\d{2})-(\\d{4})$
```
Par exemple:
```
sudo audit.sh GRRPC25-0322 tectech test
```

- sans idEsn (possible)
```
sudo python3 -B audit.py <IDESN> TECTECH [PROD|TEST]
```
Par exemple:
```
sudo audit.sh tectech test
```
## Notes importantes pour tec.tech
- les paramètres sont convertis en majuscules avant exécution
- le mode PROD est ignoré tant que l'outil est considéré en phase de test
- les gestionnaires de tec.tech demandent à ce qu'on économise les jetons d'accès à la base; pour cela, l'outil stocke le jeton qu'il a acquis dans un fichier local ```token.json``` (ou ```prod-token.json```) puis l'utilise tant qu'il est valide; il est donc important que l'outil puisse écrire dans le répertoire ou se trouve audit.sh
## Rapporter des anomalies, faire des suggestions, etc.
Durant la phase de test, merci d'utiliser les "Issues" de GitHub: c'est un moyen simple et suffisant pour suivre les problèmes/questions/suggesttions.
Pour la suite, cela reste encore à décider...
