#!/bin/bash

ORIGDIR="$PWD/.."
TESTDIR="/tmp/recursid_dist_test"

rm -rf "$TESTDIR"
mkdir "$TESTDIR"
cd "$TESTDIR"

virtualenv -p python3 test
cd test

. bin/activate
pip3 install "${ORIGDIR}/dist/Recursid-0.1.0-py3-none-any.whl"

cd lib/python3.7/site-packages/recursid/etc/ || exit 1

if [ -e "systemd/system/recursid.service" ] && [ -e "recursid/fluentd_zmq_url_handle.json" ]; then
    echo "Files in etc survived package creation"
else
    echo "THE ETC FILES ARE NOT PRESENT"
    exit 1
fi
