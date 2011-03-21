DESCRIPTION = "enigma2 iptv plugin for KartinaTV & RodnoeTV"
MAINTAINER = "Alex Maystrenko <alexeytech@gmail.com>"
HOMEPAGE = "http://code.google.com/p/kartinatv-dm/"
LICENSE = "GNU GPLv2"
SECTION = "extra"

PN="enigma2-plugin-extensions-kartinatv"

PV="1.6.3"
PR = "r2"

PACKAGES = " ${PN} "

SRC_URI = "file://${FILE_DIRNAME}/build"
S = "${WORKDIR}/build"

EXTRA_OECONF = " \
        BUILD_SYS=${BUILD_SYS} \
        HOST_SYS=${HOST_SYS} \
        STAGING_INCDIR=${STAGING_INCDIR} \
        STAGING_LIBDIR=${STAGING_LIBDIR} \
"
FILES_${PN} += " /usr/share/enigma2/KartinaTV_skin /usr/lib/enigma2/python/Plugins/Extensions/KartinaTV"

FILES_${PN}-meta = "${datadir}/meta"
PACKAGES += "${PN}-meta"

DEPENDS = "enigma2"

inherit autotools

python populate_packages_prepend () {
	
	def getControlLines(mydir, d, package):
		try:
			#ac3lipsync is renamed since 20091121 to audiosync.. but rename in cvs is not possible without lost of revision history..
			#so the foldername is still ac3lipsync
			if package == 'audiosync':
				package = 'ac3lipsync'
			src = open(mydir + package + "/CONTROL/control").read()
		except IOError:
			return
		for line in src.split("\n"):
			if line.startswith('Package: '):
				full_package = line[9:]
			if line.startswith('Depends: '):
				bb.data.setVar('RDEPENDS_' + full_package, ' '.join(line[9:].split(', ')), d)
			if line.startswith('Description: '):
				bb.data.setVar('DESCRIPTION_' + full_package, line[13:], d)
			if line.startswith('Replaces: '):
				bb.data.setVar('RREPLACES_' + full_package, ' '.join(line[10:].split(', ')), d)
			if line.startswith('Conflicts: '):
				bb.data.setVar('RCONFLICTS_' + full_package, ' '.join(line[11:].split(', ')), d)
			if line.startswith('Maintainer: '):
				bb.data.setVar('MAINTAINER_' + full_package, line[12:], d)

	mydir = bb.data.getVar('D', d, 1) + "/../build/"
	for package in bb.data.getVar('PACKAGES', d, 1).split():
		getControlLines(mydir, d, package.split('-')[-1])
}
