#!/usr/bin/env bash
##############################################################################
# Author: Clive Bostock
#   Date: 9 Dec 2022 (A Merry Christmas to one and all! :o)
#   Name: eol.sh
#  Descr: Cleanup Windows EOL characters for Linux/Mac usage
##############################################################################
for file in `ls *.sh *.py *.md 2> /dev/null`
do
   cp ${file} ${file}.edit
   echo "Converting EOL for file ${file}"
   cat ${file}.edit |  tr -d '\r' > ${file}
   rm  ${file}.edit
done
echo "Done."
