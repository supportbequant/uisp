#!/bin/bash

# Set these variables to the specific values of your deployment
#

# BQN management IP address
BQN_OAM_IP=192.168.0.121
# Name of the REST user in the BQN server
BQN_REST_USER=myuser 
# Password of the REST user in the BQN server
BQN_REST_PW='mypassword'
# IP address or domain of the UISP server
UISP_SERVER=uisp.com
# REST API KEY of the UISP server
UISP_KEY=apikey

# Main part, do not modify
#

cd /root/uisp
./sync-uisp-bqn -b ${BQN_OAM_IP} ${BQN_REST_USER} ${BQN_REST_PW} ${UISP_SERVER} ${UISP_KEY} >> /tmp/sync-uisp-bqn.log