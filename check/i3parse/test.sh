#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail
here="$(dirname ${BASH_SOURCE[0]})"

cd "$here"

i3parse bindings /etc/i3/config > /dev/null
rm -rf venv
virtualenv venv
venv/bin/pip install .
venv/bin/i3parse --help > /dev/null

rm -rf venv
virtualenv -p python3 venv
venv/bin/pip install .
venv/bin/i3parse --help > /dev/null

./gitversion > .test-pass-commit
