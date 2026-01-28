======================================================

   Audit Linux  

======================================================

--------------------------
Rappel:
--------------------------
Pour ouvrir une fenêtre "Terminal", pré-positionnée sur le bon répertoire
- dans l'explorer, ouvrir le répertoire
- click droit sur une zone vide => Ouvrir dans un terminal

Quand un script est marqué "exécutable", on peut l'exécuter directement depuis l'explorer en double cliquant dessus
(choisir ensuite l'option "lancer dans un terminal")
ATTENTION !!!
Pour que ceci fonctionne, il faut que la clé USB soit formatée en Ext4 ou NTFS  ( FAT32 ne supporte pas le flag "exécutable" )



--------------------------
Installation:
--------------------------

  Décompresser le fichier zip dans un répertoire audit sur la clé USB ( ** PAS SUR LA RACINE ** )

  Depuis LMDE7, il est possible de créer une partition DATA sur la clé bootable LMDE7, pour y recopier l'outil d'audit
  (sans casser son caractère bootable)
  Mais il y a 2 conditions pour que ça marche
  - la création de la clé USB doit être faite depuis un poste LMDE7
  - la création de la partition DATA doit être faite depuis un poste LMDE7
  Méthode:
  - utiliser l'outil standard "Accessoires => Disque"
  - important: ne PAS utiliser la totalité de l'espace disponible pour cette partition, mais laisser 100MB de libre
    ( évite d'aller effacer des trucs qui peuvent être en fin de clé USB )
  - formater en Ext4 ( pour ne pas casser le flag "exécutable" de certains fichiers ) . A la rigueur utiliser NTFS

--------------------------
Réglage du clavier
--------------------------
Si on a booté directement sur une clé LMDE , sans installer LMDE , le clavier est prépositionné en qwerty

Pour forcer temporairement le clavier Français, double cliquer au choix sur un de ces scripts:
setxkbmap-fr        ( clavier azerty standard)
setxkbmap-fr-mac    ( clavier azerty variante mac)


--------------------------
Usage:
--------------------------

  Utiliser le login utilisateur normal 
  ( Pas besoin d'être root. Mais le script va temporairement utiliser  'sudo' pour lancer la commande inxi )
 
  Méthode1 : Lancer le menu principal 

    # Se mettre dans le répertoire audit
    bash menu.sh


  Méthode2 : Lancer directement l'audit en saisissant ou non l'identifiant Emmaus

    # Se mettre dans le répertoire audit
    bash audit.sh GRPCxx-xxxx   
    bash audit.sh                 ( l'identifiant Emmaus sera demandé et mémorisé )

  Méthodes alternatives: 
    #double cliquer sur audit.sh ou menu.sh
    ( ne marche pas avec FAT32 )



  REMARQUES:  
  -  L'audit lance désormais une fenêtre qui affiche les infos du PC.  Penser à fermer/minimiser cette fenêtre, si elle recouvre les écrans de saisie ...
  -  Un autre outil permet d'estimer l'autonomie de la batterie
        bash batterie.sh

-------------------------------------------------------------------
Limitations:
-------------------------------------------------------------------
  Ne fonctionne qu'avec LMDE6/LMDE7 ( pas garanti sur d'autres Linux )
   * testé positivement sur LinuxMint22.1 

  Au besoin, booter sur une clé LMDE, et lancer l'audit depuis une autre clé

  Sur d'autres Linux, inxi peut donner des résultats différents, ou il peut manquer des packages : python3-qrcode
  



-------------------------------
Calcul des notes
-------------------------------

Cet outil utilise une méthode originale pour le calcul des notes et de la catégorie
Tout est défini dans le fichier regles.csv, avec 3 sections définies par un mot-clé commençant par # en colonne 1
On peut donc changer les règles, sans toucher au code ...
  #NOTES-LINUX donne les notes de base pour les différents seuils RAM/Disque/CPU
               ( si la valeur est inférieure au seuil, on retourne la note associée
  #MODIF       définit des règles pour corriger ces notes
  #CATEGORY    définit la correspondance Note/Categorie

Remarques:
- pour #MODIF les règles dont la colonne 1 est  vide sont ignorées

-------------------------------
Syntaxe des règles #MODIF
-------------------------------
Chaque règle contient un certain nombre de couples ( CRITn, VALn) non vides  ( n va de 1 à 5 )
Dans le programme la variable infos contient une liste de paires ( key,value)
Par exemple:   key="RAM" value="15.35"

CRITn correspond à key  ,  VALn correspond à value

Une règle se décode de la manière suivante

	CRIT1	VAL1	//OK si la key "SSD" est trouvée dans infos
	SSD

	CRIT2     VAL2	//OK si la key "RAM" existe ET  RAM < 16
	RAM       16

La règle s'applique si
* TOUS les couples (CRITn , VALn) non  vides sont OK

Si la règle s'applique, on regarde les valeurs DELTA et MAX
* Si DELTA non vide => on ajoute le delta (positif ou négatif) à la note
* Si MAX non vide => on réduit la note à cette valeur maximale 

-------------------------------
Calcul de l'indice CPU
-------------------------------
Pour la recherche de l'indice cpu (CPUMARK), on utilise une liste cpus.csv stockée en local
( Issue d'un download de cpubenchmark.net : Merci à Joffrey pour la méthode automatisée )

* avoir un audit indépendant du réseau
* on ne traite que des PC vieux, donc il n'y a pas besoin d'avoir accès aux infos des cpus les plus récentes
* la recherche en temps réel du cpumark dans www.cpubenchmark.net est extrêmement sensible à la moindre modification 
  de la structure et du style de la page web

Il n'est pas nécessaire d'avoir une mise à jour fréquente de ce fichier




-------------------------------
Traces de la commande inxi
-------------------------------
On utilise un format texte "mono-colonne" grace au flag -y1 , beaucoup plus robuste à l'analyse
Mais ce flag n'existe pas sur les vieilles versions de inxi
Génération dans:   tmp/audit-inxi.txt


-----------------------------------------
  Pour signaler un bug
-----------------------------------------

Il faut envoyer:
      les fichiers   /tmp/audit*.*
      la trace d'exécution à l'écran


