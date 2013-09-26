#!/bin/sh
#BASEDIR=$(dirname $0)
BASEDIR="/usr/lib/enigma2/python/Plugins/Extensions/KartinaTV/api"
echo "Starting ssclient..." > $BASEDIR/ssclient.log
cd $BASEDIR

if ps | grep -v 'grep' | grep 'ssclient'
then
        start-stop-daemon -K -x $BASEDIR/ssclient
#        sleep 2
fi
echo "Starting ssclient2..." >> $BASEDIR/ssclient.log
start-stop-daemon -b -S -x $BASEDIR/ssclient -- -P 80 -i $1 -p $2 -u $3 -k $4 > $BASEDIR/ssclient.log
#$BASEDIR/ssclient -- -P 8080 -i $1 -p $2 -u $3 -k $4 > $BASEDIR/ssclient.log &
#$BASEDIR/ssclient -i $1 -p $2 -u $3 -k $4 >> $BASEDIR/ssclient.log &
echo "started! $BASEDIR/ssclient -i $1 -p $2 -u $3 -k $4" >> $BASEDIR/ssclient.log 
exit 0
