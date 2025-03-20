#!/bin/bash
#
# Copyright (c) 2012 Bequant S.L.
# All rights reserved.
#
# This product or document is proprietary to and embodies the
# confidential technology of Bequant S.L., Spain.
# Possession, use, duplication or distribution of this product
# or document is authorized only pursuant to a valid written
# license from Bequant S.L.
#
# DESCRIPTION:
#  Deactivates synchronization of billing and BQN server.
#
##############################################################################

isConfirmation ()
{
  if [[ $1 =~ ^y|Y|yes|YES|Yes|n|no|NO|No$ ]]; then
    echo $TRUE
  else
    echo $FALSE
  fi
}

isYes ()
{
  if [[ $1 =~ ^y|Y|yes|YES|Yes$ ]]; then
    echo $TRUE
  else
    echo $FALSE
  fi
}

askConfirmation ()
{
  local valid=$FALSE
  local response
  local prompt=$1
  while [[ $valid -eq $FALSE ]]
  do
    read -p "$prompt (y/n): " response
    valid=$(isConfirmation $response)
  done

  echo $(isYes $response)
}

##############################################################################

#
# main
Main ()
{
  confirmation=$(askConfirmation "Do you want to stop synchronization with billing?")
  if [[ $confirmation -eq $FALSE ]]; then
    echo "Doing nothing"
    exit 0
  fi

  rm /bqn/root/cron.5/sync-*-bqn.sh
  echo "Synchronization with billing removed"
  exit 0
}

##############################################################################
#
#  Variable definition section.
#
##############################################################################

PATH=/bin:/usr/bin:/sbin:/usr/sbin
export PATH

FALSE=0
TRUE=1

execName=${0##*/}

##############################################################################
#
#  Execution section.
#
##############################################################################

Main "$@"



