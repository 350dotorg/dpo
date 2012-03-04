import os
import polib
import tempfile

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

def source_text(entry):
    if not entry.tcomment:
        return None
    source_text = None
    for line in entry.tcomment.splitlines():
        if line.strip() == polib.u(";;"):
            break
        if source_text is not None:
            source_text.append(line)
        if line.strip() == polib.u(";; Source text ;;"):
            source_text = []

    if source_text and source_text[0].startswith("msgid"):
        source_text = None

    return source_text

def unicode_with_source_msgstr(self, wrapwidth=78):
    """
    Returns the unicode representation of the entry.
    """
    if self.obsolete:
        delflag = '#~ '
    else:
        delflag = ''
    ret = []
    # write the msgctxt if any
    if self.msgctxt is not None:
        ret += self._str_field("msgctxt", delflag, "", self.msgctxt, wrapwidth)
    # write the msgid
    ret += self._str_field("msgid", delflag, "", self.msgid, wrapwidth)
    # write the msgid_plural if any
    if self.msgid_plural:
        ret += self._str_field("msgid_plural", delflag, "", self.msgid_plural, wrapwidth)

    source = source_text(self)
    if source is not None:
        ret += source
    else:
        if self.msgstr_plural:
            # write blank msgstr_plurals if any
            msgstrs = self.msgstr_plural
            keys = list(msgstrs)
            keys.sort()
            for index in keys:
                msgstr = msgstrs[index]
                plural_index = '[%s]' % index
                ret += self._str_field("msgstr", delflag, plural_index, "", wrapwidth)
        else:
            # otherwise write a blank msgstr
            ret += self._str_field("msgstr", delflag, "", "", wrapwidth)
    ret.append('')
    ret = polib.u('\n').join(ret)
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
    pofile.metadata = source_pofile.metadata

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

        else:

            ret = []
            ret += new_entry._str_field("msgid", "", "", new_entry.msgid)

            if new_entry.msgid_plural:
                ret += new_entry._str_field("msgid_plural", "", "", new_entry.msgid_plural)
                new_entry.msgstr_plural['0'] = new_entry.msgid
                new_entry.msgstr_plural['1'] = new_entry.msgid_plural
            else:
                new_entry.msgstr = new_entry.msgid

            original_text = "\n".join(ret)
            new_entry.dpo_comment = original_text

        pofile.append(new_entry)

    return pofile

def reconstruct_source_file(self):
    ret, headers = '', self.header.split('\n')
    for header in headers:
        if header[:1] in [',', ':']:
            ret += '#%s\n' % header
        else:
            ret += '# %s\n' % header

    if not isinstance(ret, polib.text_type):
        ret = ret.decode(self.encoding)

    ret = [ret]
    entries = [self.metadata_as_entry()] + \
        [e for e in self if not e.obsolete]
    for entry in entries:
        if not entry.translated():
            ret.append(entry.__unicode__(self.wrapwidth))
        else:
            ret.append(unicode_with_source_msgstr(entry, self.wrapwidth))
    for entry in self.obsolete_entries():
        if not entry.translated():
            ret.append(entry.__unicode__(self.wrapwidth))
        else:
            ret.append(unicode_with_source_msgstr(entry, self.wrapwidth))

    ret = polib.u('\n').join(ret)
    return ret

def submit_locale(pofile):
    """
    Inspects a `pofile` for "source text" annotations, and compares
    those source texts with the translations.  If an entry has a
    translation that matches its source text exactly, then the entry
    is considered untranslated, and its `msgstr` is removed.
    """
    fd, path = tempfile.mkstemp(prefix="--dpo-reconstructed--", suffix=".po")
    reconstructed = reconstruct_source_file(pofile)
    with open(path, 'w') as r:
        r.write(reconstructed)
    reconstructed = polib.pofile(path)
    for entry, source_entry in zip(pofile, reconstructed):
        if entry.translated():
            if entry.msgstr_plural:
                msgstrs = entry.msgstr_plural
                keys = list(msgstrs)
                keys.sort()
                for i, index in enumerate(keys):
                    if msgstrs[index] == source_entry.msgstr_plural[index]:
                        msgstrs[index] = ''
                    else:
                        if i == 0 and msgstrs[index] == source_entry.msgid:
                            msgstrs[index] = ''
                        elif msgstrs[index] == source_entry.msgid_plural:
                            msgstrs[index] = ''
            else:
                if entry.msgstr == source_entry.msgstr or entry.msgstr == source_entry.msgid:
                    entry.msgstr = ''
                    

    os.unlink(path)
    del(fd)
    return pofile

if __name__ == '__main__':
    import doctest
    import os
    doctest.testfile(os.path.join("tests", "test.txt"), encoding="utf8",
                     optionflags=doctest.REPORT_UDIFF | doctest.NORMALIZE_WHITESPACE | doctest.REPORT_ONLY_FIRST_FAILURE)

