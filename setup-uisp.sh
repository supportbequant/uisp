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
#  Activates synchronization of UISP and BQN server.
#
##############################################################################
#
#  Function definition section.
#
##############################################################################


cronSetup ()
{
  local argRoot=""
  local csBackup=0
  local csDir="$argRoot/etc/cron.5"
  local csDirBqn="$argRoot/bqn/root/etc/cron.5"

  # Add bqncron to crontab
  grep bqncron "$argRoot/etc/crontab" >/dev/null 2>/dev/null
  if [ $? -ne 0 ]; then
    [ ! -x "$argRoot/opt/bqn/sbin/bqncron" ] && return
    if [ ! -e "$argRoot/bqn/root/etc/crontab" ]; then
      cp -f "$argRoot/etc/crontab" "$argRoot/bqn/root/etc/crontab"
    fi
    grep bqncron "$argRoot/bqn/root/etc/crontab" >/dev/null 2>/dev/null
    if [ $? -ne 0 ]; then
      echo "-*/5 * * * *   root  test -x /opt/bqn/sbin/bqncron && /opt/bqn/sbin/bqncron >/dev/null 2>&1" >> "$argRoot/bqn/root/etc/crontab"
      csStatus=$?
      if [ $csStatus -ne 0 ]; then
        echo "Error: Cannot update \"$argRoot/bqn/root/etc/crontab\" cron file ($csStatus)"
        return
      fi
    fi
    # Backup crontab
    if [ -e "$argRoot/etc/crontab" ]; then
      mv -f "$argRoot/etc/crontab" "$argRoot/etc/crontab.bak" 2>/dev/null >/dev/null
      csStatus=$?
      if [ $csStatus -eq 0 ]; then
        csBackup=1
      else
        echo "Warning: Cannot backup \"$argRoot/etc/crontab\" file ($csStatus)"
      fi
    fi
    # Create symbolic link to new crontab.
    ln -s "/bqn/root/etc/crontab" "$argRoot/etc/crontab"
    csStatus=$?
    if [ $csStatus -ne 0 ]; then
      [ $csBackup -eq 1 ] && \
        mv -f "$argRoot/etc/crontab.bak" "$argRoot/etc/crontab" 2>/dev/null >/dev/null
      echo "Error: Cannot create link for \"$argRoot/etc/crontab\" file ($csStatus)"
      return
    fi
  fi

  # Create BQN CRON directory.
  if [ ! -d "$csDirBqn" ]; then
    mkdir -p "$csDirBqn"
    csStatus=$?
    [ $csStatus -ne 0 ] && \
      echo "Error: Cannot create \"$csDirBqn\" directory ($csStatus)"
  fi
  if [ ! -h "$csDir" -a ! -d "csDir" ]; then
    ln -s "$csDirBqn" "$csDir"
    csStatus=$?
    [ $csStatus -ne 0 ] && \
      echo "Error: Cannot create link for \"$csDir\" file ($csStatus)"
  fi

  # Restart CRON service.
  systemctl restart cron.service
}

##############################################################################

isIp ()
{
  if [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo $TRUE
  else
    echo $FALSE
  fi
}

##############################################################################

askIp ()
{
  local valid=$FALSE
  local address
  local prompt=$1
  while [[ $valid -eq $FALSE ]]
  do
    read -p "$prompt: " address
    valid=$(isIp $address)
  done
  echo ${address}
}


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

echoBoolean ()
{
  local boolean=$1
  if [[ $boolean -eq $TRUE ]]; then
    echo "true"
  else
    echo "false"
  fi
}

##############################################################################

#
# main
Main ()
{
  BQN_OAM_IP=$(askIp "BQN OAM IP")
  read -p "BQN REST user: " BQN_REST_USER
  read -p "BQN REST password: " BQN_REST_PW
  read -p "UISP server: " UISP_SERVER
  read -p "UISP API KEY: " UISP_KEY
  ONLY_GROUPS=$(askConfirmation "Get only location groups? (n for full synchronization)")

  echo "We are about to setup a cron script with these parameters:"
  echo "  BQN OAM IP: $BQN_OAM_IP"
  echo "  BQN REST user: $BQN_REST_USER"
  echo "  BQN REST password: $BQN_REST_PW"
  echo "  UISP server: $UISP_SERVER"
  echo "  UISP API KEY: $UISP_KEY"
  echo "  Only location groups: $(echoBoolean $ONLY_GROUPS)"

  confirmation=$(askConfirmation "Do you want to proceed?")
  if [[ $confirmation -eq $FALSE ]]; then
    echo "Not proceeding"
    exit 0
  fi

  if [[ $ONLY_GROUPS -eq $TRUE ]]; then
    ONLY_GROUPS_OP="-og"
  fi
 
  cronSetup

  # Copy script to cron.5
  echo "cd /root/uisp; ./sync-uisp-bqn -b ${BQN_OAM_IP} ${BQN_REST_USER} ${BQN_REST_PW} ${ONLY_GROUPS_OP} ${UISP_SERVER} ${UISP_KEY} >> /tmp/sync-uisp-bqn.log" > ${cronScript}
  chmod a+x  ${cronScript}

  echo "Activated billing synchronization"
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
cronScript=/bqn/root/cron.5/sync-uisp-bqn.sh

##############################################################################
#
#  Execution section.
#
##############################################################################

Main "$@"



