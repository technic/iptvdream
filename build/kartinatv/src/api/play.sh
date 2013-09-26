#!/bin/sh
#BASEDIR=$(dirname $0)
BASEDIR="/usr/lib/enigma2/python/Plugins/Extensions/KartinaTV/api"
cd $BASEDIR

if ps | grep -v 'grep' | grep 'ssclient'
then
        start-stop-daemon -K -x $BASEDIR/ssclient
fi
echo "Starting ssclient2..." >> $BASEDIR/ssclient.log
start-stop-daemon -b -S -x $BASEDIR/ssclient -- -P 5000 -i $1 -p $2 -u $3 -k $4
exit 0
