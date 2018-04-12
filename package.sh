#!/bin/bash

set -xeou
yum install -y zip python27 python27-pip
pip install -U pip

BASEDIR=/data
PIPPACKAGESDIR=${BASEDIR}/lambda-packages

cd ${BASEDIR}

zip log_handler_subscription.zip log_handler_subscription.py

mkdir -p ${PIPPACKAGESDIR}
#/usr/bin/pip install -t ${PIPPACKAGESDIR} -r requirements.txt
/usr/local/bin/pip install -t ${PIPPACKAGESDIR} -r requirements.txt
/usr/local/bin/pip list
cd ${PIPPACKAGESDIR}
zip -r ../log_handler.zip .
