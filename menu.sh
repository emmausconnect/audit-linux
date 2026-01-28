##############################################################
# Audit Linux : MENU
#
# ouvrir une fenêtre shell
# se mettre dans le repertoire contenant menu.sh
# 
# bash menu.sh 
#
# IMPORTANT
#   Ce script est supposé être lancé sur un OS  LMDE 6
#   Fonctionnement non garanti sur d'autres Linux ...
#   Si la machine n'est pas LMDE6, booter sur une clé LMDE6, et recopier les scripts
##############################################################

# Se positionner dans le repertoire du script
dir=`dirname $0`
if [ "$dir" = "" ]
then
  dir="."
fi

cd $dir

read -p "❗️Entrer le mot de passe: " ZZZEMMAUS
export ZZZEMMAUS
echo ""

sudo -K

python3 -B menu.py $1 $2 $3


