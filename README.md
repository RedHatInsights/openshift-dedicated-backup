# Openshift Dedicated Backup
Script to backup project resources from Openshift Dedicated into a Git repo.

Structure
---
- Each project is backed up to a branch named by the OpenShift project.
- There is a folder per OpenShift resource type.
- There is a new commit per backup

Resources Backed Up
---
- Service
- DeploymentConfig
- BuildConfig
- ImageStream
- Route
- ConfigMap
- StatefulSet
- Secret (separate repo)

How to Run
---
1. `pipenv install`
2. Define environment variables in env.sh of project root
```
#!/bin/bash

# openshift access token
export KUBERNETES_TOKEN=asdf290834jfsldkjf28jf2lksjdf

# openshift api port
export KUBERNETES_SERVICE_PORT=443

# openshift api host
export KUBERNETES_SERVICE_HOST=api.myopenshift.com

# location of ssh private key for BACKUP_GIT_REPO and SECRET_GIT_REPO
export GIT_SSH_PRIVATE_KEY_LOC=/home/me/.ssh/id_rsa

# git repo where all projects and resources (except secrets) will be stored
export BACKUP_GIT_REPO=git@github.com:RedHatInsights/insights-osd-backup.git

# git repo where secrets for all projects will be stored
export SECRET_GIT_REPO=git@github.com:RedHatInsights/inights-osd-backup-secret.git

# temporary directory where repos will be cloned
export WORKING_DIR=/mnt

# SSL certificate for KUBERNETES_SERVICE_HOST
export SERVICE_CERT_FILENAME=/home/me/certs/myopenshift.ca.crt
```
3. `source env.sh`
4. `pipenv run python3 src/backup.py`
