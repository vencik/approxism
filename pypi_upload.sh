#!/bin/sh

set -e

rm -f approxism-*.tar.gz
./build.sh -ug
twine upload approxism-*.tar.gz
