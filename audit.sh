##############################################################
# Audit Linux : 
#
# ouvrir une fenêtre shell
# se mettre dans le repertoire contenant audit.sh
# 
# bash audit.sh GRPCxx-xxxx
#       ( le pwd sera peut être demandé pour activer sudo )
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


python3 -B audit.py $1 $2 $3


