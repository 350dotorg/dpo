import polib

class DPOEntry(polib.POEntry):
    def __init__(self, *args, **kwargs):
        polib.POEntry.__init__(self, *args, **kwargs)
        self.dpo_comment = None

    def __unicode__(self, wrapwidth=78):
        """
        Returns the unicode representation of the entry.
        """
        ret = []
        val = self.dpo_comment
        prefix = '# '

        if val:
            ret.append("# ;; Source text ;;")
            for comment in val.split('\n'):
                if wrapwidth > 0 and len(comment) + len(prefix) > wrapwidth:
                    ret += polib.wrap(
                        comment,
                        wrapwidth,
                        initial_indent=prefix,
                        subsequent_indent=prefix,
                        break_long_words=False
                        )
                else:
                    ret.append('%s%s' % (prefix, comment))
            ret.append("# ;;")

        ret.append(polib.POEntry.__unicode__(self))
        ret = polib.u("\n").join(ret)
        return ret

def new_locale(source_pofile):
    """
    Creates a new `POFile` derived from the `source_pofile` suitable for offline use 
    by individual translators.

    Initial `msgstr`s will be populated with the translations from the `source_pofile`.
    If the `source_pofile` contains a `msgstr` then it will be used, otherwise the
    `msgstr` will be left blank.

    If the `msgstr` is populated, some additional metadata is generated for the entry:

      1. The entry receives a "translator comment" reproducing the source msgstrs
      
    These can be used by subsequent translators and managers, to detect divergent
    source strings, review translations, and identify untranslated strings.
    """
    pofile = polib.POFile()
    pofile.header = source_pofile.header

    for entry in source_pofile:
        new_entry = DPOEntry()
        new_entry.merge(entry)

        new_entry.msgstr = entry.msgstr
        if entry.msgstr_plural:
            for pos in entry.msgstr_plural:
                new_entry.msgstr_plural[pos] = entry.msgstr_plural[pos]

        if new_entry.translated():

            ret = []
            if new_entry.msgstr_plural:
                # write the msgstr_plural if any
                msgstrs = new_entry.msgstr_plural
                keys = list(msgstrs)
                keys.sort()
                for index in keys:
                    msgstr = msgstrs[index]
                    plural_index = '[%s]' % index
                    ret += new_entry._str_field("msgstr", "", plural_index, msgstr)
            else:
                # otherwise write the msgstr
                ret += new_entry._str_field("msgstr", "", "", new_entry.msgstr)
            original_text = "\n".join(ret)
            new_entry.dpo_comment = original_text

        pofile.append(new_entry)

    return pofile

if __name__ == '__main__':
    source = polib.pofile("test.po")
    new = new_locale(source)
    new.save("out.po")

