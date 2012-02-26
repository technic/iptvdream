SUBDIRS = servicets api

installdir = $(libdir)/enigma2/python/Plugins/Extensions/KartinaTV

install_PYTHON = *.py

install_DATA = \
	*.png \
	keymap.xml \
	LICENCE

install_LTLIBRARIES = jtvreader.la

jtvreader_la_SOURCES = \
	jtvreader.cpp

jtvreader_la_LDFLAGS = \
	-avoid-version -module -shared
