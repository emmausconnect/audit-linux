-------------------- V2.5.0 1 Oct 2025 -------------------------------

Fonctions:
    AuditLinux s'enrichit d'un MENU  [Version BETA]  ( appelable via "bash menu.sh" )
    - Appel d'outils de tests ( disque, batterie, clavier/son/webcam )
    - Saisie des Caractéristiques Matériel ( et mémorisation des infos saisies )
    - Lancement de l'Audit ( mini-audit ou audit+transferts)
    - Utilitaires BOLC ( changement de statut du PC )
    - Accès aux sites web des constructeurs
    - Documentation
    - Oubli de l'identifiant Emmaus, précdemment saisi

    L'audit continue à être appelable directement
        # en fournissant l'identifiant Emmaus
        bash audit.sh  GRPCxx-nnnn

        # sans saisir l'identifiant Emmaus => il sera demandé et mémorisé 
        bash audit.sh  

    Le test de batterie continue à être appelable directement
        bash batterie.sh

Remarque:
    L'audit lance désormais une fenêtre qui affiche les infos du PC.  Penser à fermer/minimiser cette fenêtre, si elle recouvre les écrans de saisie ...

Correctifs:
    On survit désormais au cas particulier où le fichier généré par la commande inxi contient des caractères incorrects ( non UTF-8 ), typiquement dans le nom de la batterie

-------------------- V2.4.1  23 Juin 2025 ------------------------------- -

Correctif:
    calcul du cpumark:
       correction d'un bug, qui provoquait une confusion entre   Intel Core i3-6100U    /  Intel Core i3-6100
       amélioration de la détection des cpuname de type  Intel Core i7 M 620     ( changer en Intel Core i7-620M )

-------------------- V2.4.0  12 Juin 2025 ------------------------------- -

Fonctions:
    Nouvelle catégorisation: mise à jour de regles.csv

    Le fichier cpuchange.csv  permet de mémoriser des listes de correspondances: pour les cas où le nom de CPU trouvé par l'analyse système est très différent de cpubenchmark.net
        ex:  i5 M 520  => Intel Core i5-520M

    Possibilité de saisir le nom commercial du modèle de PC, et de l'injecter dans la FicheAchat

    Copie du fichier LeControleParental.pdf sur le bureau

    MAJ auto: Vérifie l'existence d'une version plus récente sur le serveur Emmaus, et propose le download

Interne:
    Purge de cpus.csv : 
        contient désormais uniquement les cpu "mono socket" ( on ne traite pas de serveurs haut de gamme ! )
        on se débarrasse de la fréquence cpu située après @


-------------------- V2.3.0  25 Mai 2025 ------------------------------- -
Fonctions:
    Génération d'une "FicheAchat.rtf" , suivant le modèle Jean-Jacques
    Renommage "Remarques" en "Observations"
    Documentation: la partie "concepts de base" a été séparée dans un document à part (commun Windows/Linux)

Interne:
    Purge de répertoire, pour éviter une prolifération de fichiers Bolc
    Mémorisation du nom de fichier Bolc, pour pouvoir relancer le transfert ultérieurement
    IHM: changement gestion valeurs initiales
    
-------------------- V2.2.0  27 avril 2025 --------------------------------
Découplage des écrans: Infos Techniques / Infos Administratives
( Ca passe mieux sur des écrans à faible taille X/Y )

On peut modifier le CPUMARK détecté automatiquement

Corrections dans le fichier des CPU

Copie mini-fiche ( formats douchette+smartphone ) sur le Bureau [Suggestion C.Marvin]

-------------------- V2.1.5  11 avril 2025 --------------------------------
Le dépots des fichiers d'audit se fait désormais sur https://audits.emmaus-connect.org 

L'audit linux est maintenant téléchargeable depuis https://audits.emmaus-connect.org/api/apps/linux/download/latest

Séparation Linux

-------------------- V2.1.4  4 avril 2025 --------------------------------
Possibilité de déclarer un matériel comme TA dans l'identifiant
( dans ce cas, le type est forcé à "Tablette" )

Le fichier d'import sftp pour le bolc est systématiquement généré, et rajouté sur drop.tf

-------------------- V2.1.3   30Mars2025 --------------------------------

Nouvelles règles de cotation des PC
- suppression HC , INVENDABLE
- changement du seuil CPUMARK pour la note -8

Rajout des règles de cotation Windows

Une 2e mini fiche avec QRcode spécifique douchette

Les parties spécifiques Linux sont isolées dans linux.py 

-------------------- V2.1.2   15Mars2025 --------------------------------

Compatibilité avec le Bolc des Portables ayant un type non usuel ( "detachable" et autres ) 
Petits trucs
 - renommage "Reconditionneur" en "Nom Bénévole" 
 - affichage des infos techniques AVANT la saisie des infos administratives
 - stoppe tout,  si on abandonne la saisie

Ajustement mini-fiche + rajout Date,CPUMARK
Adaptation Linux des docs de Decouverte-MonPC

------------------- V2.1.0   13Mars2025 -------------------------------

Génération d'une fiche .rtf avec QRCODE
Rajout champ: ID du PC chez le reconditionneur
Rajout champ: "origine" (utilisation variable selon les sites !)

IHM pour saisir les infos administratives


--------------------- V2.0.3   28Fev2025 --------------------------------

Simplification du décodage Inxi et correction d'un bug aléatoire sur la détection du N° de série

suppression de la règle: [ si Linux alors  Catégorie B max ]


-------------------- V2.0.2 27Fev2025 --------------------------------

Date au format jj/mm/aa dans le rapport
Rajout de l'os détaillé dans le fichier Bolc

Ne plus utiliser le package python "requests" pas toujours présent

Rajout du nom de fichier d'import Bolc dans le rapport stocké sur drop.tf 
( permet de facilitier les recherches en cas de pb d'import Bolc)

-------------------- V2.0.1 26Fev2025 --------------------------------

Inxi renvoie des tailles disk/ram en GiB . ( 1024*1024*1024 bytes ) Conversion en GB ( 1000*1000*1000 bytes )

Arrondir les tailles Disk/Ram

Surprise! Inxi renvoie 2 valeurs "serial" parfois différentes sur certains PC !  
La 2e valeur semble correspondre au chassis, avec parfois des valeurs bidon 

-------------------- V2.0.0  25Fev2025 --------------------------------
Diffusion initiale


