#!/bin/bash

# Set these variables to the specific values of your deployment
#

# BQN management IP address
BQN-OAM-IP=192.168.0.121
# Name of the REST user in the BQN server
BQN-REST-USER=myuser 
# Password of the REST user in the BQN server
BQN-REST-PW=mypassword
# IP address or domain of the UISP server
UISP-SERVER=uisp.com
# REST API KEY of the UISP server
UISP-KEY=apikey

# Main part, do not modify
#

cd /root/uisp
./sync-uisp-bqn -b ${BQN-OAM-IP} ${BQN-REST-USER} ${BQN-REST-PW}  ${UISP-SERVER} ${UISP-KEY} >> /tmp/sync-uisp-bqn.log