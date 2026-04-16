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
#echo "AUDITDIR=${AUDITDIR}"
#printf "Liste de paramètres:\n"
#for v in $*; do printf ">$v<\n"; done

cd $dir

# Leave the parameter parsing and checking to the Python code
# There is no BOLC compatibility anymore, since BOLC has been phased out. Therefore TECTECH is implied and the only
# possible argument choice are over: equipment id and TEST|PROD instance of tec.tech
# The acceptable parameter list styles are now:
# (all parameters are case-insensitive and will be converted to uppercase)
#   sudo bash audit.sh                         # [1] idEsn sera demandé, la base de PROD est choisie
#   sudo bash audit.sh GRPC26-0043             # [2] la base de PROD est choisie
#   sudo bash audit.sh [PROD|TEST]             # [3] idEsn sera demandé et la base est explicitement désignée
#   sudo bash audit.sh GRPC26-0043 [PROD|TEST] # [4] idEsn et la base sont explicitement désignés

# left as it was but why not:
#   python3 -B audit.py $*
# ?
python3 -B audit.py $*
