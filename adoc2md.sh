#!/bin/sh

# Convert AsciiDoc text files into MarkDown
#
# The conversion isn't perfect; some of the formatting isn't supported by
# certain common implementations of MarkDown.
# Still, AsciiDoc (being a richer format) produces better documentation,
# so I'm keeping sources in AsciiDoc, providing conversions
# to Markdown for PYPI.
#
# Note that `pandoc` is required (see instructions on https://pandoc.org/installing.html).

input="$1"
output="$2"; test -z "$output" && output="/dev/stdout"

set -e

if test -z "$input"; then
    cat >&2 <<HERE
Usage: $0 input.adoc [output.md]
HERE
    exit 1
fi

# Make sure tools are available
which asciidoc >/dev/null   || (echo "ERROR: asciidoc not installed"; exit 1)
which iconv >/dev/null      || (echo "ERROR: iconv not installed"; exit 1)
which pandoc >/dev/null     || (echo "ERROR: pandoc not installed"; exit 1)

asciidoc -b docbook -o - "$input" | \
    iconv -t utf-8 | \
        pandoc -f docbook -t gfm | \
            iconv -f utf-8 > "$output"
