# audit-linux (adapté pour tec.tech)

Cet outil est la version de l'audit Linux jadis développé par Bernard Maison, qui fonctionnait avec le BOLC et qui a été adapté pour permettre l'envoi des données d'audit vers tec.tech au lieu du BOLC.

Pour mémoire, il se base sur la [dernière version publiée par Bernard](https://audits.emmaus-connect.org/api/apps/linuxold/download/2.7.1), la 2.7.1

# Fonctions et limitations actuelles

- l'outil permet, soit de créer un nouveau matériel, soit de modifier un matériel existant, le tout à partir des données d'audit générées par le code *historique* de Bernard (code qui a été amélioré)

- son unique vocation étant de faire de l'audit, l'outil ne permet pas de modifier certains attributs déjà déclarés dans la base tec.tech (```'id', 'idLot', 'idStock', 'idGroupe', 'reconditionneur', 'createdAt', 'updatedAt'```)

- pour l'outil, à partir de la version `5.0.0`, l'identifiant utilisé pour désigner un matériel est une chaîne de format libre, passée en paramètre lors du lancement

- l'outil a été testé mais peut encore avoir des défauts; il est fortement recommandé de lire les [notes d'évolution](https://audits.emmaus-connect.org/api/apps/linux/changelog/web) et de se familiariser avec l'outil sur la base tec.tech de test (voir ci-dessous)

- certaines des données d'audit qui allaient dans le BOLC jusqu'à la version `2.7.1` n'ont pas de point de chute naturel dans tec.tech: elles sont regroupées dans le champ "commentaire" de tec.tech


# Obtenir l'outil

- l'outil peut être téléchargé depuis le site [audits.emmaus-connect.org](https://audits.emmaus-connect.org/api/apps/linux/web) sous la forme d'un fichier `linux-x.y.z.tgz`

- le fichier se décompresse avec une commande qui créera localement un répertoire `audit-linux-x.y.z` contenant l'outil:
    ```
    tar xzf linux-x.y.z.tgz
    ```

# Rapporter une anomalie, faire des suggestions, …

Pour des questions générales ou des suggestions, vous pouvez utiliser [l'espace GoogleChat dédié à cet outil](https://chat.google.com/room/AAQA-458onA?cls=7).

Si vous constatez une anomalie, vous pouvez, soit m'envoyer un mail, soit utiliser [l'espace GoogleChat](https://chat.google.com/room/AAQA-458onA?cls=7). Merci de bien vouloir joindre à votre signalement le fichier de trace créé à chaque exécution. Le nom complet de ce fichier est affiché dans les toutes premières lignes de la console; par exemple:
```
[INFO]: Nom du fichier de trace: /tmp/audit-linux-journal-20260406.112818.txt
```
Dans certains cas, il peut aussi être intéressant de joindre les fichiers suivants, portant la même horodate que que le fichier de trace:
```
/tmp/lshw-20260406.112818.json
/tmp/lsblk-20260406.112818.json
```
Notez que ces fichiers, du fait qu'ils sont placés dans `/tmp`, ne survivent pas à un rédémarrage du PC.

# Utiliser l'outil

## Première utilisation

- se positionner dans le bon répertoire
    ```commandline
    cd audit-linux.x.y.z
    ```

- y créer un fichier nommé `tectech-credentials.json` avec votre éditeur favori et y placer les données suivantes:
    ```commandline
    {
        "client_id":     " *valeur à demander à l'équipe tec.tech* ",
        "client_secret": " *valeur à demander à l'équipe tec.tech* ",
        "esn": " *une valeur parmi 'BX', 'CR', 'GR', 'LI', 'LV', 'LY', 'MA', 'MB', 'RO', 'SD', 'ST', 'VI'* "
    }
    ```
en respectant scrupuleusement la syntaxe (notamment la casse, les guillemets et la virgule en fin des lignes `client_id` et `client_secret`)

Les valeurs de `client_id` et de `client_secret` sont propres à chaque ESN et doivent être obtenues auprès de l'équipe tec.tech.

La valeur de `esn` sert à deux choses:
- dans le cas d'une création de matériel, déterminer le stock de destination dans tec.tech,
- déterminer le répertoire de destination des données d'audit dans la base des audits (indépendante de tec.tech).

La valeur de `esn` éventuellement passée en paramètre de la ligne de commande supplante celle qui se trouve dans `tectech-credentials.json`.


## Utilisations ultérieures

L'outil s'appelle directement avec le script `audit.sh`. Le script `menu.sh` ne doit pas être utilisé pour faire de l'audit.

L'audit se lance depuis la ligne de commande.

##### Obtenir une aide en ligne complète
```commandline
bash audit.sh -h
```
##### Usage standard: audit puis transferts vers base d'audits et tec.tech
```commandline
bash audit.sh -i IdentifiantPC
```
##### Mini-audit: réaliser un audit sans identifier le PC et quitter
```commandline
bash audit.sh --mini
```
##### Usage avancé: utilisation de la base tec.tech de test
```commandline
bash audit.sh -i IdentifiantPC --test
```

Lors de l'audit, si l'équipement existe déjà dans tec.tech, l'outil le met à jour, sinon, il le crée, le tout avec les données collectées lors de l'audit.

## Modification d'un matériel existant v/s création d'un nouveau matériel
L'outil d'audit ne sait faire des recherches qu'avec l'identifiant qu'on lui donne en paramètre (`IdentifiantPC` est pris ici comme exemple) ou bien le numéro de série du matériel, tel qu'extrait par l'outil lui-même.

De ma compréhension actuelle de tec.tech, pour un PC:

- reconditionné par un pro: `idMaterielReconditionneur` contient l'identifiant attribué par le pro,
- reconditionné par l'ESN: `idMaterielReconditionneur` contient l'identifiant *eePCaa-nnnn*, attribué par l'ESN.

Dans tous les cas, pour tec.tech, `idEsn` est un champ libre, que certains ESN utilisent comme identifiant unique. Autrement dit, `idEsn` est une valeur conforme à la syntaxe *eePCaa&#x2011;nnnn* et unique dans tec.tech, alors que pour tec.tech, ce champ n'est nullement contraint.

Dans notre exemple, l'outil d'audit cherche le PC d'abord par `idEsn=IdentifiantPC` puis, en cas d'échec, par `idMaterielReconditionneur=IdentifiantPC` et enfin, en cas d'échec, par son *numéro de série*:

- s'il trouve, tout va bien: il s'agit de la modification d'un équipement déjà déclaré dans tec.tech,

- s'il ne trouve pas:
  - si on a donné un numéro de lot, il considère que c'est une création et il la réalise,
  - sinon, il ne fait rien.

Ça marche très bien si les PC ont été déclarés par leur `idEsn` dans tec.tech avant de les mettre entre les mains des bénévoles pour l'audit.

Ça marche aussi pour des PC reconditionnés par un pro, qui ont été déclarés dans tec.tech avec un `idMaterielReconditionneur` (au format propre au pro) et un `numeroSerie`, et pour lesquels `idEsn` n'a pas encore été renseigné.

Ça marche assez bien si le référent déclare au moins le lot. Comme vu ci-dessus, l'outil d'audit sait créer des matériels dans tec.tech à partir des deux infos: `idLot` et `IdentifiantPC`.

Pour mémoire, les `idEsn` des PC doivent se conformer au modèle:
```
^(BX|CR|GR|LI|LV|LY|MA|MB|RO|SD|ST|VI)PC(\\d{2})-(\\d{4})$
```

Lors d'une création de matériel:
- `idMaterielReconditionneur` prend la valeur `IdentifiantPC`
- si `idEsn` est conforme à la syntaxe décrite ci-dessus, alors il prend aussi la valeur `IdentifiantPC`, sinon il reste vide

De façon générale, à ma connaissance, la notion de doublon n'est pas définie formellement dans tec.tech au delà de l'unicité des différents *ID* (qui est requise par le SGBD sous-jacent). Par exemple, à l'heure où j'écris, il existe dans tec.tech plusieurs dizaines de cas où des matériels différents (*ID* différents) ont les mêmes `idMaterielReconditionneur+numeroSerie`…


## Notes importantes

- les paramètres sont convertis en majuscules avant exploitation

- les gestionnaires de tec.tech demandent à ce qu'on économise les jetons d'accès à la base; pour cela, l'outil stocke le jeton qu'il a acquis dans un fichier local `token-prod.json` (ou `token-test.json`) puis l'utilise tant qu'il est valide; il est donc important que l'outil puisse écrire dans le répertoire ou se trouve audit.sh.
