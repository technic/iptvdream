SUBDIRS = servicets api

installdir = $(libdir)/enigma2/python/Plugins/Extensions/KartinaTV

etcdir = $(sysconfdir)/iptvdream
etc_DATA = default.epgmap

install_PYTHON = utils.py plugin.py __init__.py htmlentitydefs.py server.py

install_DATA = \
	*.png \
	keymap.xml \
	LICENCE

install_LTLIBRARIES = jtvreader.la

jtvreader_la_SOURCES = \
	jtvreader.cpp

jtvreader_la_LDFLAGS = \
	-avoid-version -module -shared
