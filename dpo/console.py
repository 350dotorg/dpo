import dpo
import optparse
import pkg_resources
import polib
import sys

version = pkg_resources.get_distribution("dpo").version
description = ""

parser = optparse.OptionParser(
    usage="%prog [OPTIONS] path/to/file.po",
    version=version,
    description=description)
parser.add_option(
    "--source",
    action="store_true",
    dest="is_source",
    help="Use file.po translations as source text")
parser.add_option(
    "--upload",
    action="store_true",
    dest="is_upload",
    help="Upload file.po translations and filter out untranslated source text")

def main(args=None):
    if args is None:
        args = sys.argv[1:]
    options, args = parser.parse_args(args)
    if len(args) != 1:
        parser.error("You must provide exactly one argument, the po file")
    if not options.is_source and not options.is_upload:
        parser.error("You must provide either the `source` or `upload` command")
    if options.is_source and options.is_upload:
        parser.error("You cannot run source and upload together")
    pofile = polib.pofile(args[0])
    if options.is_source:
        print dpo.new_locale(pofile)
    elif options.is_upload:
        print dpo.submit_locale(pofile)

if __name__ == '__main__':
    main()
