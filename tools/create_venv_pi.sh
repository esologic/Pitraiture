#! /usr/bin/env bash

# Run on a Pi, to actually be able to capture images.

# Create a `venv` virtual environment, activate and install all required packages for development.

set -uo pipefail
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd ${DIR}/..

python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade pip
pip install -r ./requirements/prod.txt -r ./requirements/prod-pi.txt