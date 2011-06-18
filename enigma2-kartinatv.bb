DESCRIPTION = "enigma2 iptv plugin for KartinaTV & RodnoeTV"
MAINTAINER = "Alex Maystrenko <alexeytech@gmail.com>"
HOMEPAGE = "http://code.google.com/p/kartinatv-dm/"
LICENSE = "GNU GPLv2"
SECTION = "extra"

PN="enigma2-plugin-extensions-kartinatv"

PV="1.7.0"
PR = "r2"

SRC_URI = "file://${FILE_DIRNAME}/build"
S = "${WORKDIR}/build"

EXTRA_OECONF = " \
        BUILD_SYS=${BUILD_SYS} \
        HOST_SYS=${HOST_SYS} \
        STAGING_INCDIR=${STAGING_INCDIR} \
        STAGING_LIBDIR=${STAGING_LIBDIR} \
"
EXTRA_OECONF += " --with-po "

FILES_${PN} += " /usr/share/enigma2/KartinaTV_skin /usr/lib/enigma2/python/Plugins/Extensions/KartinaTV"

FILES_${PN}-dbg = " /usr/lib/enigma2/python/Plugins/Extensions/KartinaTV/.debug "

DEPENDS = "enigma2"

inherit autotools