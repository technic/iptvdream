#
# to use this for the localisation of other plugins,
# just change the DOMAIN to the name of the Plugin.
# It is assumed, that the domain ist the same as
# the directory name of the plugin.
#

DOMAIN = @NAME@
installdir = @INSTALLDIR@
GETTEXT = xgettext
MSGFMT = msgfmt

LANGS := @LANGUAGES@
LANGPO := $(foreach LANG, $(LANGS),$(LANG).po)
LANGMO := $(foreach LANG, $(LANGS),$(LANG).mo)

default: $(DOMAIN).pot $(LANGPO) merge $(LANGMO)
	for lang in $(LANGS); do \
		mkdir -p $$lang/LC_MESSAGES; \
		cp $$lang.mo $$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done

merge:
	for lang in $(LANGS); do \
		msgmerge --no-location -s -N -U $$lang.po $(DOMAIN).pot; \
	done


# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
$(DOMAIN).pot:
	$(GETTEXT) -L python --add-comments="TRANSLATORS:" -d $(DOMAIN) -s -o $(DOMAIN).pot ../kartinatv/*.py
	msguniq -o $(DOMAIN)uniq.pot $(DOMAIN).pot
	$(RM) $(DOMAIN).pot
	mv $(DOMAIN)uniq.pot $(DOMAIN).pot

.PHONY: $(DOMAIN).pot


%.mo: %.po
	$(MSGFMT) -o $@ $<

%.po:
	msginit -l $@ -o $@ -i $(DOMAIN).pot --no-translator

CLEANFILES = $(foreach LANG, $(LANGS),$(LANG).mo)

clean:
	$(RM) -r $(LANGS)

install: default
	for lang in $(LANGS); do \
		mkdir -p $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES; \
		cp $$lang.mo $(DESTDIR)$(installdir)/locale/$$lang/LC_MESSAGES/$(DOMAIN).mo; \
	done

uninstall:
	rm -r $(DESTDIR)$(installdir)/locale/
