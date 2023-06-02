#!/usr/bin/env bash
##############################################################################
# Author: Clive Bostock
#   Date: 1 Dec 2022 (A Merry Christmas to one and all! :o)
#   Name: dccm.sh
#  Descr: Setup Python environment and modules for DCCM
##############################################################################
fix_eols ()
{
  echo "Ensuring Linux style line terminators."
  for file in `ls *.sh *.py *.md 2> /dev/null`
  do
   cp ${file} ${file}.edit
   echo "Converting EOL for file ${file}"
   cat ${file}.edit |  tr -d '\r' > ${file}
   rm  ${file}.edit
  done
  echo "Done."
}
echo "DCCM Build started..."
fix_eols
PROG_PATH=`dirname $0`
python3 -m venv venv
APP_ENV=${PROG_PATH}/venv
source ${APP_ENV}/bin/activate
python get-pip.py
${APP_ENV}/bin/pip install -r requirements.txt
echo "Done."
