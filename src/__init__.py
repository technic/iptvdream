# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
	os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
	gettext.textdomain("enigma2")
	gettext.bindtextdomain("KartinaTV", resolveFilename(SCOPE_PLUGINS, "Extensions/KartinaTV/locale"))

def _(txt):
	t = gettext.dgettext("KartinaTV", txt)
	if t == txt:
		#print "[KartinaTV] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)
