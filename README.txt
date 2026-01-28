======================================================

   Audit Linux  

======================================================

--------------------------
Usage:
--------------------------

  Décompresser le fichier zip dans un répertoire audit ( ** PAS SUR LA RACINE ** )

  Utiliser le login utilisateur normal 
  ( Pas besoin d'être root. Mais le script va temporairement utiliser  'sudo' pour lancer la commande inxi )
 
  Se mettre dans le répertoire audit
       bash audit.sh GRPCxx-xxxx

  ( Il faut passer l'Identifiant PC en paramètres: comme ça, si on veux rejouer l'audit, pas besoin de le ressaisir )


  REMARQUE:  
    un autre outil permet d'estimer l'autonomie de la batterie
        bash batterie.sh

-------------------------------------------------------------------
Limitations:
-------------------------------------------------------------------
  Ne fonctionne qu'avec LMDE6 ( pas garanti sur d'autres Linux )
   * testé positivement sur LinuxMint22.1

  Au besoin, booter sur une clé LMDE6, et lancer l'audit depuis une autre clé

  Sur d'autres Linux, inxi peut donner des résultats différents, ou il peut manquer des packages : python3-qrcode
  



-------------------------------------------------------------------
Nouvelles infos détectées:
-------------------------------------------------------------------
Type de sique HDD/SSD
Disque NVME
Taille écran
Webcam  ( fiabilité à vérifier ...)

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
- une marge de 6% est appliquée pour comparer avec les valeurs seuil:
  (un PC de 16GB de mémoire, peut montrer uniquement 15.35GB de mémoire)
- pour #MODIF les règles dont la colonne 1 est  vide sont ignorées
- pour Linux, le seuil pour une note mémoire  -8 est abaissé à 2GB ( Linux marche avec 2GB )

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
Pour la recherche de l'indice cpu (CPUMARK), on utilise une liste cpus.csv
* avoir un audit indépendant du réseau
* on ne traite que des PC vieux, donc il n'y a pas besoin d'avoir accès aux infos des cpus les plus récentes
* la recherche automatique via une url dans www.cpubenchmark.net est extrêmement sensible à la moindre modification 
  de la structure et du style de la page web

Une mise à jour annuelle de ce fichier est suffisante

Pour mettre à jour cpus.csv
* aller sur https://www.cpubenchmark.net/CPU_mega_page.html
* choisir:  show ALL results
* Sélectionner le tableau (en incluant la 1e colonne qui contient une icône, mais pas la ligne d'en-tête)
* Recopier dans cpus.csv  ( le copier/coller peut être très lent ... )
* ATTENTION : ne pas abimer la 1e ligne d'en-tête du CSV


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


