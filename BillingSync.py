#!/usr/bin/python3

################################################################################
#
# Copyright (c) 2022 Bequant S.L.
# All rights reserved.
#
# This product or document is proprietary to and embodies the
# confidential technology of Bequant S.L., Spain.
# Possession, use, duplication or distribution of this product
# or document is authorized only pursuant to a valid written
# license from Bequant S.L.
#
#
################################################################################

import json
import logging
import sys
import datetime
import os
import platform

import requests
from requests.adapters import HTTPAdapter
PY_VERSION = platform.python_version().split('.')
if int(PY_VERSION[1]) >= 7:  # 3.7 or more
  from requests.packages.urllib3.util.ssl_ import create_urllib3_context

################################################################################

class BqnRestAdapter(HTTPAdapter):
    """
    Adapter to control the level of security of SSL sessions of HTTPS requests.
    Needed to avoid issues depending on the python/requests/openssl versions.
    """
    # We use python 3.7 defaults
    CIPHERS = ('DEFAULT:!aNULL:!eNULL:!MD5:!3DES:!DES:!RC4:!IDEA:!SEED:!aDSS:!SRP:!PSK')

    def init_poolmanager(self, connections, maxsize, block=False):
      context = create_urllib3_context(ciphers=BqnRestAdapter.CIPHERS)
      context.check_hostname = False
      pool = super(BqnRestAdapter, self)
      pool.init_poolmanager(connections=connections,
              maxsize=maxsize,
              block=block,
              ssl_context=context)
      return pool

    def proxy_manager_for(self, connections, maxsize, block=False):
      context = create_urllib3_context(ciphers=BqnRestAdapter.CIPHERS)
      context.check_hostname = False
      pool = super(BqnRestAdapter, self)
      pool.proxy_manager_for(connections=connections,
              maxsize=maxsize,
              block=block,
              ssl_context=context)
      return pool

################################################################################

class BillingSync:
  BLOCK_POLICY = "Billing-Block"

  ############################################################################

  def __init__(self, verbose):
    self.logger = logging.getLogger(__name__)
    if verbose == 0:
      self.logger.setLevel(logging.WARNING)
    elif verbose == 1:
      self.logger.setLevel(logging.INFO)
    else:
      self.logger.setLevel(logging.DEBUG)
    #logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
    logging.basicConfig(stream=sys.stdout, format='%(message)s')

  ############################################################################

  def normalizeString(self, str):
    return str.replace(' ', '_')

  def normalize(self, obj):
    # Traverse object to replace strings for BQN normalized form
    # Object must be a dictionary or an array for the funtion to do anything
    if isinstance(obj, dict):
      for key in obj:
        if isinstance(obj[key], str):
          obj[key] = self.normalizeString(obj[key])
        else:
          self.normalize(obj[key])
    elif isinstance(obj, list):
      for i in obj:
        if isinstance(i, str):
          obj[obj.index(i)] = self.normalizeString(i)
        else:
          self.normalize(obj[obj.index(i)])
    else:
      pass # Do nothing
 
  ############################################################################

  def fieldIsNotNull(self, obj, path):
    """
    Starting with an object, tries to access field through a field path.
    Returns False if any field in the path does not exist, it
    is null or empty, and true otherwise.
    Used to check json fields before trying to access them.
    """
    if not obj:
      return False
    if len(path) == 0:  # not null and path completed
      return True
   
    try:
      obj[path[0]]
    except KeyError as e:
      return False
 
    if isinstance(obj[path[0]], list):
      if (len(obj[path[0]]) == 0):
        return False
      else:
        for o in obj[path[0]]:
          if self.fieldIsNotNull(o, path[1:]):
            return True  # At least one element is not null
        return False
    else:
      return self.fieldIsNotNull(obj[path[0]], path[1:])
 
  ############################################################################

  def jsonDumps(self, jsonObj):
    return json.dumps(jsonObj, ensure_ascii=False).encode('utf-8')

  ############################################################################

  def printResponseDetails(self, rsp):
    if self.logger.getEffectiveLevel() != logging.DEBUG:
      return

    self.logger.debug("")
    self.logger.debug("====== Request =======")
    self.logger.debug("%s to URL %s" % (rsp.request.method, rsp.request.url))
    for h in rsp.request.headers:
      self.logger.debug("%s: %s" % (h, rsp.request.headers[h]))
    self.logger.debug("")
    if rsp.request.body:
      self.logger.debug(rsp.request.body)
      self.logger.debug("")
    self.logger.debug("====== Response ======")
    self.logger.debug("HTTP/1.1 %d" % rsp.status_code)
    for h in rsp.headers:
      self.logger.debug("%s: %s" % (h, rsp.headers[h]))
    self.logger.debug("")
    if rsp.text:
      try:
        self.logger.debug(json.dumps(json.loads(rsp.text),  indent=4, separators=(',', ':'), ensure_ascii=False))
      except Exception as e:
        self.logger.debug(rsp.text)

  ############################################################################

  def printSubscriberPolicies(self, data):
    # Calculate size of columns as maximum length of the values to display
    # When the column header may be wider than the displayed values, it is
    # also considered.
    # We create a list with the dictionary field values for each column, get the
    # list item with the maximum length and finally get that length.
    tableSizes = []
    tableSizes.append( len( max(list(x["subscriberIp"] for x in data["subscribers"]), key=len) ) )
    tableSizes.append( len( max(list(x["policyRate"] for x in data["subscribers"]), key=len) ) )
    if len(data["policies"]) > 0:
      tableSizes.append( len( max(list(str(x["policyId"]) for x in data["policies"] if "policyId" in x), key=len) ) )
      tableSizes.append( len( max(list(str(x["rateLimitDownlink"]["rate"]) for x in data["policies"] if "rateLimitDownlink" in x) + ["Dn Kbps"], key=len) ) )
      tableSizes.append( len( max(list(str(x["rateLimitUplink"]["rate"]) for x in data["policies"] if "rateLimitUplink" in x) + ["Up Kbps"], key=len) ) )
    else: # No policies defined, policy Id n/a
      tableSizes.append( len( "Plan Id") )
      tableSizes.append( len( "Dn Kbps" ) )
      tableSizes.append( len( "Up Kbps" ) )
    tableSizes.append( max(len( max(list(str(x["state"]) for x in data["subscribers"]), key=len) ), len("state") ) )
    tableSizes.append( len("Block") )
    tableSizes.append( len( max(list(str(x["subscriberId"]) for x in data["subscribers"] if "subscriberId" in x), key=len) ) )

    rowFormat = ''
    for size in tableSizes:
      rowFormat += "{:<%d}" % (size + 1)
    self.logger.info("\n" + rowFormat.format("IP"
                                      ,"Plan"
                                      ,"Plan Id"
                                      ,"Dn Kbps"
                                      ,"Up Kbs"
                                      ,"State"
                                      ,"Block"
                                      ,"Name"))

  
    for s in data["subscribers"]:
      matches = [x for x in data["policies"] if x["policyName"] == s["policyRate"]]
      if len(matches) == 1:
        policy = matches[0]
      else:
        self.logger.debug("Policy %s not found" % s["policyRate"])
        # Some billing do not return policy details (e.g. wisphub)
        policy ={
            "policyName": s["policyRate"],
            "policyId": 0
        }
      self.logger.info(rowFormat.format(s["subscriberIp"]
                                        ,policy["policyName"]
                                        ,policy["policyId"] if "policyId" in policy else "n/a"
                                        ,policy["rateLimitDownlink"]["rate"] if "rateLimitDownlink" in policy else "n/a"
                                        ,policy["rateLimitUplink"]["rate"] if "rateLimitUplink" in policy else "n/a"
                                        ,s["state"]
                                        ,"yes" if s["block"] else "no"
                                        ,s["subscriberId"] if "subscriberId" in s else "n/a"))

  ############################################################################

  def printSubscriberGroups(self, data):
    # Calculate size of columns as maximum length of the values to display
    # Subscriber groups have no size limit (at the end of the table)
 
    tableSizes = []
    tableSizes.append( len( max(list(x["subscriberIp"] for x in data["subscribers"]), key=len) ) )
    tableSizes.append( len( max(list(str(x["subscriberId"]) for x in data["subscribers"]), key=len) ) )

    rowFormat = ''
    for size in tableSizes:
      rowFormat += "{:<%d}" % (size + 1)
    self.logger.info("\n" + rowFormat.format("IP"
                                      ,"Name") + " Groups")

    for s in data["subscribers"]:
      if not "subscriberGroups" in s:
        continue
      subGroups = ""
      for group in s["subscriberGroups"]:
        subGroups += " %s" % group
      if len(subGroups) > 0:
        self.logger.info(rowFormat.format(s["subscriberIp"]
                                         ,s["subscriberId"]) + subGroups)


  ############################################################################

  def printData(self, data):
    self.printSubscriberPolicies(data)
    self.printSubscriberGroups(data)

  ############################################################################

  def areEqual(self, a, b, keys=None):
    # Compare two variables for equality.
    # keys argument restrict equal operation to those dictonary keys. If none, all checked.
    if isinstance(a, list) and isinstance(b, list):
      return sorted(a) == sorted(b)
    elif isinstance(a, dict) and isinstance(b, dict):
      if not keys:
        return sorted(a.items()) == sorted(b.items())
      else:
        for k in keys:
          # Check if dictionaries have item as key
          if k not in a and k not in b:
            continue
          elif k not in a and k in b:
            if not b[k]:
              continue
            else:
              return False
          elif k in a and k not in b:
            if not a[k]:
              continue
            else:
              return False
          elif not self.areEqual(a[k], b[k]):
            return False
        return True
    else:
      return a == b

  ############################################################################

  def updateBqn(self, bqnIp, bqnUser, bqnPassword, data):

    uriRoot = "https://" + bqnIp + ":3443/api/v1"
    session = requests.Session()
    session.verify = False
    session.auth = (bqnUser, bqnPassword)
    session.headers =  {
      "Content-Type": "application/json; charset=utf-8",
      "Accept-Charset": "utf-8"
    }
    py_version = platform.python_version().split('.')
    # To support TLS1.2 (python default too stringent)
    if int(PY_VERSION[1]) >= 7:  # 3.7 or more
      session.mount(uriRoot, BqnRestAdapter())

    updatedPolicies = 0
    updatedSubscribers = 0

    # Adapt data to BQN format
    for item in data["policies"] + data["subscribers"]:
      self.normalize(item)
    # Add fields not treated by billing
    for p in data["policies"]:
      p["rateLimitDownlink"]["congestionMgmt"] = True
    # Blocked subscribers have block policy
    for s in data["subscribers"]:
      if s["block"]:
        s["policyRate"] = BillingSync.BLOCK_POLICY

    self.logger.info("Create policies is %s" % uriRoot)
    rsp = session.get(uriRoot + "/policies/rate")
    polsInBqn = rsp.json()["items"]
    for p in data["policies"]:
      matches = [x for x in polsInBqn if x["policyName"] == p["policyName"]]
      if len(matches) > 0:
        if len(matches) > 1:
          self.logger.warning("Policy %s found more than once, taking first one" % p["policyName"])
        if self.areEqual(matches[0], p, ["policyId", "rateLimitDownlink", "rateLimitUplink"]):
          continue
      self.logger.debug("Create policy %s" % p["policyId"])
      policyName = requests.utils.quote(p["policyName"], safe='')  # Empty safe char list, so / is not regarded as safe and encoded as well
      payload = self.jsonDumps(p)
      rsp = session.post(uriRoot + "/policies/rate/" + policyName, data=payload)
      self.printResponseDetails(rsp)
      updatedPolicies += 1
    # Generate a block policy to enforce inactive clients
    matches = [x for x in polsInBqn if x["policyName"] == BillingSync.BLOCK_POLICY]
    if len(matches) == 0:
      payload = self.jsonDumps({"policyId": "block", "rateLimitDownlink": {"rate": 0}, "rateLimitUplink": {"rate": 0}})
      rsp = session.post(uriRoot + "/policies/rate/" + BillingSync.BLOCK_POLICY, data=payload)
      self.printResponseDetails(rsp)

    rsp = session.get(uriRoot + "/subscribers")
    subsInBqn = rsp.json()["items"]
    self.logger.info("Create subscribers in %s" % uriRoot)
    for s in data["subscribers"]:
      matches = [x for x in subsInBqn if x["subscriberIp"] == s["subscriberIp"]]
      # If more than one match, we take first one
      if len(matches) > 0:
        if len(matches) > 1:
          self.logger.warning("Subscriber %s found in BQN more than once, taking first one" % s["subscriberIp"])
        if self.areEqual(matches[0], s, ["subscriberId", "policyRate", "subscriberGroups"]):
          continue
        self.logger.debug("Subscriber changed. In BQN: %s" % matches[0])
        self.logger.debug("                In billing: %s" % s)
      self.logger.debug("Create subscriber %s" % s["subscriberIp"])
      payload = self.jsonDumps(s)
      rsp = session.post(uriRoot + "/subscribers/" + s["subscriberIp"], data=payload)
      self.printResponseDetails(rsp) 
      updatedSubscribers += 1

    self.logger.warning("%s synchronization of %d policies and %d subscribers" % \
                 (datetime.datetime.now(), updatedPolicies, updatedSubscribers))

  ################################################################################

