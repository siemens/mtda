#!/bin/sh

MTDA_DATE=$(date +%Y-%m-%d)
MTDA_VERSION=$(python3 -c 'import mtda; print(mtda.__version__)')

set -e

sed -i -e "s,@MTDA_DATE@,${MTDA_DATE},g" -e "s,@MTDA_VERSION@,${MTDA_VERSION},g" configs/bintray.json
cat configs/bintray.json
mkdir -p deploy-armhf
find build-armhf/build/tmp/deploy/isar-apt/apt -name *.deb -exec cp {} deploy-armhf/ \;
dpl --provider=bintray --file=configs/bintray.json --skip_cleanup --user=chombourger --key=${BINTRAYAPIKEY}
