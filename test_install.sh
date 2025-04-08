#!/bin/sh

set -e # exit on first error

MYTMP="$(mktemp -d)"
ansible-galaxy collection build --output-path "${MYTMP}"
ansible-galaxy collection install --force "${MYTMP}"/*.tar.gz
rm -rf "${MYTMP}"
cd example
ansible-playbook -vvv zammad_playbook.yml
cd ..
