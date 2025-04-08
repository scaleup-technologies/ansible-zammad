#!/bin/sh
DEST_DIR="${HOME}/tmp/ansible_collections/scaleuptechnologies/zammad"
mkdir -p "${DEST_DIR}"
rsync -v --delete -r ./* "${DEST_DIR}/"
cd "${DEST_DIR}" || exit
# erase coverage data, not needed rsync overwrites it
# ansible-test coverage erase
if ! ansible-test units --coverage -vv  --python 3.12; then
  exit 1
fi
ansible-test sanity -v --python 3.12
ansible-test coverage html
ansible-test coverage report
