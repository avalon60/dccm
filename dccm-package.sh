#!/usr/bin/env bash
#
# Script to package up DCCM
#
PROG=`basename $0`
ART_CODE="dccm"
E="-e"

APP_HOME=$(dirname $0) 
APP_HOME=$(realpath ${APP_HOME}) 
cd ${APP_HOME}
APP_HOME=$(pwd)

date_time()
{
  DATE=`date +"%Y/%m/%d %T"`
  echo $DATE
}

app_version()
{
  version_file="${APP_HOME}/libm/${ART_CODE}_m.py"
  if [ ! -f "${version_file}" ]
  then
    echo $E "ERROR: Cannot find main model Python file, libm/${ART_CODE}_m.py".
    exit 1
  fi
  version=$(head -30 ${version_file} | grep "__version__" | cut -f3 -d " " |  sed 's/"//g' | tr -d '\r')
  echo "$version"
}   

display_usage()
{
  echo "Usage: ${PROG}  -v <version_tag>"
  echo $E "\nIf you don't wish to include the <artifactory-url>, <artifactory_username> and / or <artifactory_key>,"
  echo $E "on the command line, you may export them to the shell variables ARTIFACTORY_LOC, ART_USER_ID and ART_KEY"
  echo $E "respectively."
  echo $E "\nIf not supplied, the default Artifactory URL, is https://artifacthub-iad.oci.oraclecorp.com/hcgbu-dev-generic-local."
  echo $E "\nExample:"
  echo $E "\n        ./${PROG} -v 1.3.0"
  echo $E "\nThis example assumes that the ART_KEY is exported as a shell variable."
  exit
}
while getopts "v:l" options;
do
  case $options in
    v) VERSION_TAG=${OPTARG};;
    l) WRITE_LOG=Y;;
    *) display_usage;
       exit 1;;
   \?) display_usage;
       exit 1;;
  esac
done

app_vers=`app_version`
if [ "${VERSION_TAG}" != "${app_vers}" ]
then
   echo -e "ERROR: A version tag of \"${VERSION_TAG}\", when ${ART_CODE}.py, thinks that it is version \"${app_vers}\""
   exit 1
fi

echo -e "Application home: ${APP_HOME}\n"
cd ${APP_HOME}
${APP_HOME}/freeze.sh
if [ -d ../stage/dccm ]
then 
  rm -fr ../stage/dccm
fi
mkdir -p ../stage/dccm
for file in `cat bom.lst`
do 
  if [ -d "${file}" ]
  then
    echo $E "cp -r ${file} ../stage/dccm"
    cp -r ${file} ../stage/dccm
  elif [ -f "${file}" ]
  then
    echo $E "cp $file ../stage/dccm/${file}"
    cp $file ../stage/dccm
  else
    echo "ERROR: Unrecognised type:  ${file}"
  fi
done
# Make sure we don't include the SQLite3 database.
rm ../stage/dccm/assets/data/*.db 2> /dev/null
cd ../stage
STAGE_LOC=`pwd`
cd dccm

find . -type f -name "*.json" -exec dos2unix "{}" ";" 
find . -type f -name "*.py" -exec dos2unix "{}" ";" 
find . -type f -name "*.txt" -exec dos2unix "{}" ";" 
find . -type f -name "*.md" -exec dos2unix "{}" ";" 
find . -type f -name "*.sh" -exec dos2unix "{}" ";" 

cd ${STAGE_LOC}
echo -e "\nWorking from : `pwd`"
export arch_file="${ART_CODE}-${VERSION_TAG}.zip"
echo "Creaing artifact archive:  ${arch_file}"
if [ -f ${arch_file} ]
then
  rm ${arch_file}
fi
zip -r ${arch_file} dccm 
if [ $? -ne 0 ]
then 
   exit 1
fi
# rm -fr ../stage/dccm
echo "Done."
