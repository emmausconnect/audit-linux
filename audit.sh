#!/bin/bash

##############################################################
# Audit Linux : 
#
# ouvrir une fenêtre shell
# se mettre dans le repertoire contenant audit.sh
# 
# Variante1:
#   bash audit.sh GRPCxx-xxxx
#
# Variante2:
#   bash audit.sh   ( l'identifiant du PC sera demandé et mémorisé )
#       
#
# NOTE:
# le pwd sera peut être demandé pour activer sudo 
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

export AUDITDIR=$(readlink -e $(dirname $0))
echo "AUDITDIR=${AUDITDIR}"
printf "Liste de paramètres:\n"
for v in $*; do printf ">$v<\n"; done

cd $dir

# Leave the parameter parsing and checking to the Python code
# However, the acceptable parameter list styles are:
#   python3 -B audit.py                      # [1] backward comptible with BOLC
#   python3 -B audit.py GRPC26-0043          # [2] backward comptible with BOLC
#   python3 -B audit.py             TECTECH [PROD|TEST] # [3] works with tec.tech (case-insensitive)
#   python3 -B audit.py GRPC26-0043 TECTECH [PROD|TEST] # [4] works with tec.tech (case-insensitive)

# left as it was but why not:
#   python3 -B audit.py $*
# ?
python3 -B audit.py $1 $2 $3


