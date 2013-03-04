#!/bin/bash
version=`cat enigma2-kartinatv.bb |perl -ne 'if ( s/PV\s*=\s*"(.*)"\n/\1/ or s/VVV\s*=\s*"(.*)"/-$1/) { print $_ }'`
perl -pi -e "s/Version:.*/Version: ${version}/" build/DEBIAN/control
