#!/usr/bin/env bash
##############################################################################
# Author: Clive Bostock
#   Date: 1 Dec 2022 (A Merry Christmas to one and all! :o)
#   Name: dccm.sh
#  Descr: Database Client Connection Manager
##############################################################################
PROG=`basename $0`
PROG_PATH=`dirname $0`
FULL_PATH=$0
if [[ "${PROG}" == *\.sh ]]
then
  DCCM_PY=`echo ${FULL_PATH} | sed "s/\.sh/.py/"`
else
  DCCM_PY="${FULL_PATH}.py"
fi
APP_HOME=`echo ${FULL_PATH} | sed "s/${PROG}//; s/\/$//"`
APP_ENV=${PROG_PATH}/venv
if [ -f ${APP_ENV}/bin/activate ]
then
  source ${APP_ENV}/bin/activate
elif [ -f ${APP_ENV}/Scripts/activate ]
then
  source ${APP_ENV}/Scripts/activate
fi 
python ${DCCM_PY} $*
