#!/bin/bash
OPENSHIFT_CRONDIR=${OPENSHIFT_HOMEDIR}"app-root/repo/cronscripts"
python $OPENSHIFT_CRONDIR/su.py -l 2016-12-18 -r 2017-01-17 -t 1600 -j
