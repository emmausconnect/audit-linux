# audit-linux (adapté pour tec.tech)

Ceci est la version de l'audit Linux jadis développé par Bernard Maison, qui fonctionnait avec le BOLC et qui a été adapté pour permettre l'envoi des données d'audit vers tec.tech au lieu du BOLC.

Pour mémoire, il se base sur la [dernière version publiée par Bernard](https://audits.emmaus-connect.org/api/apps/linuxold/download/2.7.1), la 2.7.1

# Fonctions et limitations actuelles

- l'outil permet, soit de créer un nouveau matériel, soit de modifier un matériel existant, le tout à partir des données d'audit générées par le code *historique* de Bernard

- pour l'outil, l'identifiant utilisé pour désigner un matériel est toujours son "ID ESN" (```idEsn``` dans l'API tec.tech) conforme à la notation utilisée par l'outil dans le contexte BOLC. Par exemple: ```GRPC26-0888```

- l'outil a subi les tests de base mais est encore jeune; il est fortement recommandé de lire les [notes d'évolution](https://audits.emmaus-connect.org/api/apps/linux/changelog/web) et de se familiariser avec l'outil sur la base tec.tech de test (voir ci-dessous)

- pour la même raison, l'outil est encore assez verbeux, dans le but d'aider à la mise au point

- certaines des données qui allaient dans le BOLC n'ont pas de point de chute naturel dans tec.tech. L'outil les regroupe dans le champ "commentaire" de tec.tech


# Obtenir l'outil

- l'outil peut être téléchargé depuis le site [audits.emmaus-connect.org](https://audits.emmaus-connect.org/api/apps/linux/web) sous la forme d'un fichier ```linux-x.y.z.tgz```

- le fichier se décompresse avec une commande qui créera localement un répertoire ```audit-linux-x.y.z``` contenant l'outil:
```
tar xzf linux-x.y.z.tgz
```


# Utiliser l'outil

## Première utilisation

- se positionner dans le bon répertoire le bon répertoire

```cd audit-linux.x.y.z```

- y créer un fichier nommé ```tectech-credentials.json``` avec votre éditeur favori et y placer les données suivantes:
```
{
    "client_id": "UbBdc5bp***********KaS57mQwIleVm",
    "client_secret": "5uSXDqTZbOUoQ42N9jkIiyW**************YH3N5wOn-YCVBah0F7iVHrHMCnX"
}
```
en respectant scrupuleusement la syntaxe.

## Utilisations ultérieures

L'outil s'appelle directement avec le script ```audit.sh```. Le script ```menu.sh``` ne doit pas être utilisé pour faire de l'audit.

Il y a ensuite plusieurs façons lancer l'audit, selon qu'on veut fournir l'*idEsn* sur la ligne de commande et selon qu'on choisit d'accéder à la base de tec.tech de test ([https://tec-tech.osc-fr1.scalingo.io](https://tec-tech.osc-fr1.scalingo.io)) ou celle de prod ([https://tec-tech-prod.osc-fr1.scalingo.io](https://tec-tech-prod.osc-fr1.scalingo.io))

Les différentes façons d'appeler l'outils sont (on prend l'*idEsn* ```GRPC26-0043``` comme exemple):
```
sudo bash python3 -B audit.py                         # [1] idEsn sera demandé, la base de test est choisie
sudo bash python3 -B audit.py GRPC26-0043             # [2] la base de test est choisie
sudo bash python3 -B audit.py [PROD|TEST]             # [3] idEsn sera deamndé
sudo bash python3 -B audit.py GRPC26-0043 [PROD|TEST] # [4] idEsn et la base sont explicitement désignés
```

Lors de l'audit, si l'équipement existe déjà dans tec.tech, l'outil le met à jour, sinon, il le crée, le tout avec les données collectées lors de l'audit.

Pour mémoire, les idEsn doivent se conformer au modèle:
```
^(BX|CR|GR|LI|LV|LY|MA|MB|RO|SD|ST|VI)(PC|TA)(\\d{2})-(\\d{4})$
```

## Notes importantes
- les paramètres sont convertis en majuscules avant exécution
- les gestionnaires de tec.tech demandent à ce qu'on économise les jetons d'accès à la base; pour cela, l'outil stocke le jeton qu'il a acquis dans un fichier local ```token-test.json``` (ou ```token-prod.json```) puis l'utilise tant qu'il est valide; il est donc important que l'outil puisse écrire dans le répertoire ou se trouve audit.sh


## Rapporter des anomalies, faire des suggestions, etc.

Dans cette première phase d'exploitation, je suggère d'utiliser [l'espace GoogleChat dédié à cet outil](https://chat.google.com/room/AAQA-458onA?cls=7).

Pour la suite, cela reste encore à décider...
