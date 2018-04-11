#!/usr/bin/env groovy
pipeline {
    agent any

    stages {
        stage('Prepare') {
            steps {
                step([$class: 'WsCleanup'])
                checkout(scm)
                sh("""virtualenv venv
        . venv/bin/activate
        pip install -r requirements-tests.txt
        nosetests -v --with-cover --cover-erase --cover-package=log_handler_subscription tests/*.py
        flake8 log_handler_subscription.py
        deactivate""")
            }
        }
        stage('Build artefact') {
            steps {
                sh('docker run -t -v $(pwd):/data amazonlinux /data/package.sh')
            }
        }
        stage('Generate sha256') {
            steps {
                sh('openssl dgst -sha256 -binary log_handler_subscription.zip | base64 > log_handler_subscription.zip.base64sha256')
            }
        }
        stage('Upload to s3') {
            steps {
                sh("""aws s3 cp log_handler_subscription.zip s3://mdtp-lambda-functions-integration/log_handler_subscription.zip --acl=bucket-owner-full-control
        aws s3 cp log_handler_subscription.zip.base64sha256 s3://mdtp-lambda-functions-integration/log_handler_subscription.zip.base64sha256 --content-type text/plain --acl=bucket-owner-full-control""")
            }
        }
    }
}