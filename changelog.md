# Version actuelle
## Si vous utilisez cet outil pour la première fois…

- l'outil peut être téléchargé depuis le site [audits.emmaus-connect.org](https://audits.emmaus-connect.org/api/apps/linux/web) sous la forme d'un fichier ```linux-x.y.z.tgz```

- le fichier se décompresse avec une commande qui créera localement un répertoire ```audit-linux-x.y.z``` contenant l'outil:
```
tar xzf linux-x.y.z.tgz
```

#### Ensuite, ```README.pdf``` reste la référence 😃

Depuis la ```4.3.1```, le style d'appel de la commande a changé. Voici des exemples pour les cas les plus courants:
##### Usage standard: audit puis transferts vers base d'audits et tec.tech
```commandline
bash audit.sh -i IdentifiantPC
```
##### Mini-audit: réaliser un audit sans identifier le PC et quitter
```commandline
bash audit.sh -m
```
##### Aide plus complète
```commandline
bash audit.sh -h
```

## 5.0.0

Cette version introduit des **changements importants**:

- l'utilisation du format `eePCaa-nnnn` pour identifier un PC n'est désormais plus obligatoire; les équipements sont désormais identifiés par une chaîne de caractères de format libre correspondant à `idMaterielReconditionneur` dans le cas où elle ne respecte pas le format `eePCaa-nnnn`; reportez-vous au `README.pdf` pour plus de détails

- comme conséquence du point précédent, il est désormais nécessaire de spécifier l'ESN concerné; cela peut se faire de deux façons:
  - soit via l'entrée `"esn"` de `techtech-credentials.json`,
  - soit via le paramètre `-e|--esn` de la ligne de commande (supplante la valeur éventuellement présente dans `techtech-credentials.json`)

- l'ancien style de passage des paramètres n'est plus disponible: chaque paramètre doit désormais être nommé; par exemple, au lieu de:
    ```commandline
    # syntaxe obsolète
    bash audit.sh identifiant_quelconque
    ```
    on écrira:
    ```commandline
    # syntaxe valide
    bash audit.sh -i identifiant_quelconque
    ```


## Si vous souhaitez rapporter une anomalie, faire des suggestions, …

Pour des questions générales ou des suggestions, vous pouvez utiliser [l'espace GoogleChat dédié à cet outil](https://chat.google.com/room/AAQA-458onA?cls=7).

Si vous constatez une anomalie, vous pouvez, soit m'envoyer un mail, soit utiliser [l'espace GoogleChat](https://chat.google.com/room/AAQA-458onA?cls=7). Merci de bien vouloir joindre à votre signalement le fichier de trace créé à chaque exécution. Le nom complet de ce fichier est affiché dans les toutes premières lignes de la console; par exemple:
```
[INFO]: Nom du fichier de trace: /tmp/audit-linux-journal-20260406.112818.txt
```
Dans certains cas, il peut aussi être intéressant de joindre les fichiers suivants portant la même horodate que que le fichier de trace:
```
/tmp/lshw-20260406.112818.json
/tmp/lsblk-20260406.112818.json
```
Notez que ces fichiers, du fait qu'ils sont placés dans `/tmp`, ne survivent pas à un rédémarrage du PC.

# Versions antérieures
## 4.4.1

Cette version corrige quelques défauts mineurs:

- la "*CPU string*" est désormais correctement extraite sur certains équipements (signalé par Philippe R. et, à ce jour, visible seulement sur certains MacBook)

- le résultat de la commande ```inxi``` est désormais traité comme du binaire pour créer le fichier ```scan-linux.txt``` (signalé par Charles M.: sur un équipement particulier, unique à ce jour, le résultat de ```inxi``` ne se décode pas en UTF-8)

- une référence (Python) erronée lors de la création d'un équipement a été corrigée (signalé par Martin G.)

- la nouvelle implémentation, encore en cours de test, de la procédure de catégorisation intègre désormais le bonus/malus technique ou esthétique (aucune incidence pour vous)

Cette version devrait être la dernière de la lignée ```4.x.y```. En effet, il est prévu que **la prochaine version (```5.x.y```) introduise un changement majeur**: l'utilisation de l'```idEsn``` ne sera plus obligatoire. 

## Si vous souhaitez rapporter une anomalie, faire des suggestions, …

Pour des questions générales ou des suggestions, vous pouvez utiliser [l'espace GoogleChat dédié à cet outil](https://chat.google.com/room/AAQA-458onA?cls=7).

Si vous constatez une anomalie, vous pouvez, soit m'envoyer un mail, soit utiliser [l'espace GoogleChat](https://chat.google.com/room/AAQA-458onA?cls=7). Merci de bien vouloir joindre à votre signalement le fichier de trace créé à chaque exécution depuis la ```4.3.0```. Le nom complet de ce fichier est affiché dans les toutes premières lignes de la console; par exemple:
```
[INFO]: Nom du fichier de trace: /tmp/audit-linux-journal-20260406.112818.txt
```
Dans certains cas, il peut aussi être intéressant de joindre les fichiers suivants portant la même horodate que que le fichier de trace:
```
/tmp/lshw-20260406.112818.txt
/tmp/lsblk-20260406.112818.txt
```

# Versions antérieures
## 4.4.0

- le bug (signalé par Philippe P.) qui bloquait la création d'un matériel en l'absence d'un idMaterielReconditionneur est corrigé: dans un tel cas on force sa valeur à celle de idEsn

- les PC avec un disque principal utilisant une connexion ATA, généralement très vieux, sont désormais bien pris en compte (limite signalée par Jean-Jacques F.)

- j'ai introduit une nouvelle implémentation, encore en cours de test, de la procédure de catégorisation; à ce jour, elle n'a aucune incidence sur l'audit: elle est exécutée en plus et, en cas d'écart, alimente une base de données qui est analysée par ailleurs


## 4.3.1

- le bug relatif au calcul de la note en cas de SSD est corrigé (signalé par Charles M.)

- j'ai introduit un nouveau style de commande (plus standard) pour lancer l'audit; l'ancien style reste utilisable mais pourrait être supprimé dans une prochaine version; compte tenu de l'urgence pour le bug mentionné ci-dessus, la mise à jour du README est reportée à plus tard

- il est désormais possible de lancer un "mini-audit": il se limitera à l'affichage des informations d'audit à l'écran (sans contact avec les serveurs d'audit et tec.tech)

- l'affichage des informations dans la boîte de saisie manuelle des informations techniques est plus précis

- la gestion des "marques" a été améliorée pour les cas où la marque détectée ne correspond pas exactement a une de celles listées dans tec.tech


## 4.3.0 - ne pas utiliser (cette version a un bug gênant dans le cas ou le disque principal est un SSD)

Cette version est importante quoique quasiment *cosmétique*. Vu des utilisateurs, l'intention est de marquer une pause dans les modifications fonctionnelles en attendant un plus large retour d'expérience.

- les actions du menu principal (lancé avec ```menu.sh```) et qui impliqueraient une interaction avec tec.tech ont été supprimées de ce menu

- quand une nouvelle version est téléchargée, elle va désormais dans ```${HOME}/Téléchargements``` (ou son équivalent pour les langues autres que le français)

- l'affichage de messages au fil de l'exécution a été entièrement revu:
  - seuls les messages les plus importants apparaissent dans la console
  - tous les messages pouvant aider au debug vont dans un fichier de trace dont l'usage est décrit dans README.pdf


## 4.2.1

- numéro de version corrigé!


## 4.2.0

- une section "première fois…" a été ajoutée ici-même pour aider les débutant(e)s

- on utilise les *statuts* définis par tec.tech (et non plus ceux du BOLC)

- on affiche plus clairement la nature du disque principal (HDD/SSD, ATA/NVME)

- ```../eettaa-nnnn/...``` appartient désormais à l'utilisateur qui lance l'audit (et non plus à ```root```); on peut donc le supprimer aisément (demande de Charles M.)

- le fichier CSV tec.tech a été ajouté au ```.zip``` envoyé vers la base des audits

- un gros travail de nettoyage du code *historique* a été commencé:
  - suppression de toutes les analyses du résultat de *inxi* (ledit résultat est néamoins conservé)
  - suppression de ```version.txt``` (sa fonction est désormais fournie par ```__about__.py```)
  - suppression des accès au BOLC
  - suppression des références à Windows
  - limitation de l'usage de variables globales trans-fichiers, qui rendent la maintenance très difficile


## 4.1.0

- quand les deux premiers critères de recherche n'ont pas trouvé l'équipement, l'outil lance désormais une recherche basée sur le numéro de série qu'il a lui-même extrait (demande de Éric D.) Voir le README pour les détails


## 4.0.0

Je considère cette version comme *expérimentale* bien que je l'aie testée du mieux que je pouvais. Si toutefois elle vous pose problème, n'hésitez pas à revenir à la précédente après me l'avoir signalé.

- j'ai entièrement refondu l'extraction des caractéristiques physiques de la machine; elle est désormais plus robuste; cela se voit notamment quand on a affaire à des équipements inhabituels (type "tout-en-un" par exemple); j'ai néanmoins conservé l'affichage de messages relatifs à l'ancienne extraction pour faciliter l'analyse en cas de problème; je réduirai la verbosité de la console au fur et à mesure

- la caractéristique "NVME" (v/s "SATA") est maintenant bien traitée quand on a un disque SSD

- pour ce qui est des disques, je ne prends en compte que le disque principal (celui qui contient la partition ```/```) pour la catégorisation; en effet:
  - les règles de catégorisation ne sont pas claires pour moi pour le cas où il y a plusieurs disques de types différents
  - il est très rare d'avoir plusieurs disques sur les PC que nous traitons
  - j'ai rajouté une ligne AutreDisques dans la liste des caractéristiques affichées, ce qui poussera éventuellement à une pondération technique  

- le fichier TGZ se décompresse désormais en un répertoire dont le nom inclut le n° de version

- le nom de la *version récente* téléchargée par l'outil est désormais le nom du fichier TGZ (au lieu de ```.zip``` auparavant)

- le propriétaire (au sens Linux) des fichiers copiés sur le *bureau* ne devrait plus poser de problèmes de *permissions Linux*


## 3.2.3

- j'ai corrigé un bug signalé par Antoine H.: l'outil tentait à tort de modifer l'```idStock``` d'un matériel existant. Pour un matériel à créer, l'outil déduit la valeur de ```idStock``` à partir des deux premières lettres de ```idEsn```.


## 3.2.2

- la recherche de la "note CPU" se fait désormais via l'URL dédiée https://audits.emmaus-connect.org/api/cpu/CPUSTR (cette recherche a un taux de réussite proche de 100%)

- les tailles de RAM et de disque sont désormais rapportées dans les unités communément utilisées:

  - GiB (Gio) pour la RAM ==> plus de PC avec 9 ou 17 *gigas* de RAM

  - GB (Go) pour les disques ==> un disque vendu comme faisant *500 gigas* apparaîtra avec cette taille dans l'audit

- le README a été enrichi d'un nouveau paragraphe et amélioré pour l'existant

## 3.2.1

- j'ai corrigé un bug signalé par Éric D. (et relatif aux "marques")

## 3.2.0

- c'est désormais **la base PROD qui est sélectionnée par défaut** (demande de Éric D.)

- un fichier CSV compatible TECT est créé à côté des autres fichiers d'audit (demande de Charles M.)

- la version de la distribution Linux est ajoutée au champ "commentaire" (demande de Philippe R.)

## 3.1.1

- j'ai corrigé un bug signalé par Éric D.

## 3.1.0

- l'outil ne force plus le mode "*base de test*"

- l'outil permet désormais de créer un nouveau matériel en précisant *idEsn* et *idLot*

- voir ```README.md``` pour la façon d'appeler l'outil à partir de cette version

- les messages d'erreur et de trace ont été améliorés

- on ne met plus sur le bureau que ```DecouverteMonPC-Linux/*``` et ```LeControleParental.pdf```

## 3.0.4

Bug corrigé:

- l'indication de présence d'une wecbcam est maintenant correctement gérée

## 3.0.2

Quelques améliorations, à la suite des premiers retours de Charles M. et Éric D., que je remercie pour leur patience.

- la recherche d'un matériel par l'identifiant `eettaa-nnnn` (e.g.: GRPC26-1961) donné lors du lancement de `audit.sh` se fait désormais de la façon suivante
    - on recherche d'abord une correspondance sur le champ `ID ESN` de TECT; si on trouve, on en reste là
    - sinon, on recherche une correspondance sur le champ `ID matériel chez le reconditionneur`; ce dernier cas est assez fréquent pour les matériels reconditionnés en ESN: l'équipe TECT a décidé, dans un tel cas, de mettre cet identifiant dans `ID matériel chez le reconditionneur` et de laisser `ID ESN` vide.

- le mode DEBUG est par défaut pour avoir des messages plus détaillés dans cette phase


## 3.0.1

Ceci est une version de test, la toute première version de l'audit Linux destinée à fonctionner avec tec.tech.

Elle a plusieurs limites et défauts déjà identifiés:

- ne fonctionne qu'avec le script `audit.sh` (`menu.sh` n'est pas garanti de bien marcher avec tec.tech)
- ne permet d'agir que sur des matériels déjà présents dans tec.tech
- identifie un matériel par son seul 'idEsn' (pas encore par 'idMaterielReconditionneur')
- manque un peu de verbosité (pouvant aider au debug en cette phase de test)
