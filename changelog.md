### Généralités

*N'oubliez pas de lire le fichier ```README.pdf``` que j'ai largement revu, rien que pour vous 😃*

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
- ne permet d'agir que sur des matériels déjà présents danstec.tech
- identifie un matériel par son seul 'idEsn' (pas encore par 'idMaterielReconditionneur')
- manque un peu de verbosité (pouvant aider au debug en cette phase de test)
