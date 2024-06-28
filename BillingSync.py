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

  def printPolicies(self, data):
    if not data or not "policies" in data or len(data["policies"]) == 0:
      self.logger.debug("No policies to print")
      return

    # Calculate size of columns as maximum length of the values to display
    # When the column header may be wider than the displayed values, it is
    # also considered.
    # We create a list with the dictionary field values for each column, get the
    # list item with the maximum length and finally get that length.
    tableSizes = []
    tableSizes.append( len( max(list(x["policyName"] for x in data["policies"]) + ["Policy"], key=len) ) )
    tableSizes.append( len( max(list(str(x["policyId"]) for x in data["policies"] if "policyId" in x) + ["Policy-Id"], key=len) ) )
    tableSizes.append( len( max(list(str(x["rateLimitDownlink"]["rate"]) for x in data["policies"] if "rateLimitDownlink" in x) + ["Dn-Kbps"], key=len) ) )
    tableSizes.append( len( max(list(str(x["rateLimitUplink"]["rate"]) for x in data["policies"] if "rateLimitUplink" in x) + ["Up-Kbps"], key=len) ) )

    rowFormat = ''
    for size in tableSizes:
      rowFormat += "{:<%d}" % (size + 1)
    self.logger.info("\nPOLICIES\n" + rowFormat.format("Policy"
                                      ,"Policy-Id"
                                      ,"Dn-Kbps"
                                      ,"Up-Kbps"
                                      ))

  
    for p in data["policies"]:
      policyId = "n/a"
      rateLimitDownlink = "n/a"
      rateLimitUplink = "n/a"

      if "policyId" in p:
        policyId = p["policyId"]
      if "rateLimitDownlink" in p:
        rateLimitDownlink = p["rateLimitDownlink"]["rate"]
      if "rateLimitUplink" in p:
        rateLimitUplink = p["rateLimitUplink"]["rate"]

      self.logger.info(rowFormat.format(p["policyName"]
                                        ,policyId
                                        ,rateLimitDownlink
                                        ,rateLimitUplink
                                        ))


  ############################################################################

  def printSubscribers(self, data):
    if not data or not "subscribers" in data or len(data["subscribers"]) == 0:
      self.logger.debug("No subscribers to print")
      return

    # Similar calculation of format as in print Policies
    tableSizes = []
    tableSizes.append( len( max(list(x["subscriberIp"] for x in data["subscribers"]), key=len) ) )
    tableSizes.append( len( max(list(x["policyRate"] for x in data["subscribers"] if "policyRate" in x) + ["Policy"], key=len) ) )
    tableSizes.append( max(len( max(list(str(x["state"]) for x in data["subscribers"]), key=len) ), len("state") ) )
    tableSizes.append( len("Block") )
    tableSizes.append( len( max(list(str(x["subscriberId"]) for x in data["subscribers"] if "subscriberId" in x), key=len) ) )

    rowFormat = ''
    for size in tableSizes:
      rowFormat += "{:<%d}" % (size + 1)
    self.logger.info("\nSUBSCRIBERS\n" + rowFormat.format("IP"
                                      ,"Policy"
                                      ,"State"
                                      ,"Block"
                                      ,"Name"))

  
    for s in data["subscribers"]:
      subscriberId = "n/a"
      block = "n/a"
      state = "n/a"
      policyName = "n/a"

      if "subscriberId" in s:
        subscriberId = s["subscriberId"]
      if "state" in s:
        state = s["state"]
      if "block" in s:
        block ="yes" if s["block"] else "no"
      if "policyRate" in s:
        policyName =  s["policyRate"]

      self.logger.info(rowFormat.format(s["subscriberIp"]
                                        ,policyName
                                        ,state
                                        ,block
                                        ,subscriberId))

  ############################################################################

  def printSubscriberGroups(self, data):
    if not data or not "subscriberGroups" in data or len(data["subscriberGroups"]) == 0:
      self.logger.debug("No subscriber groups to print")
      return

    # Similar calculation of format as in print Policies
    tableSizes = []
    tableSizes.append( len( max(list(x["subscriberGroupName"] for x in data["subscriberGroups"]) + ["Group"], key=len) ) )
    tableSizes.append( len( max(list(x["policyRate"] for x in data["subscriberGroups"] if "policyRate" in x) + ["Policy"], key=len) ) )
    tableSizes.append( 48 ) #  maximum length of a IPv6 address

    rowFormat = ''
    for size in tableSizes:
      rowFormat += "{:<%d}" % (size + 1)
    self.logger.info("\nSUBSCRIBER GROUPS\n" + rowFormat.format("Group", "Policy", "Member-IP/Range"))

    for sg in data["subscriberGroups"]:
      policyRate = sg["policyRate"] if "policyRate" in sg else "n/a"
      if "subscriberMembers" in sg:
        for ip in sg["subscriberMembers"]:
          self.logger.info(rowFormat.format(sg["subscriberGroupName"],
                                          policyRate,
                                          str(ip)))
      if "subscriberRanges" in sg:
        for ip in sg["subscriberRanges"]:
          self.logger.info(rowFormat.format(sg["subscriberGroupName"],
                                          policyRate,
                                          str(ip)))

  ############################################################################

  def printData(self, data):
    self.printPolicies(data)
    self.printSubscribers(data)
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

  def updateBqnPolicies(self, uriRoot, session, data):
    updates = 0

    if not "policies" in data or len(data["policies"]) == 0:
      self.logger.debug("No policy information to update")
      return updates

    rsp = session.get(uriRoot + "/policies/rate")
    if rsp.status_code == 200:
      polsInBqn = rsp.json()["items"]
    else:
      polsInBqn = []
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
      updates += 1
    # Generate a block policy to enforce inactive clients
    matches = [x for x in polsInBqn if x["policyName"] == BillingSync.BLOCK_POLICY]
    if len(matches) == 0:
      payload = self.jsonDumps({"policyId": "block", "rateLimitDownlink": {"rate": 0}, "rateLimitUplink": {"rate": 0}})
      rsp = session.post(uriRoot + "/policies/rate/" + BillingSync.BLOCK_POLICY, data=payload)
      self.printResponseDetails(rsp)

    return updates

  ############################################################################

  def updateBqnSubscribers(self, uriRoot, session, data):
    updates = 0

    if not "subscribers" in data or len(data["subscribers"]) == 0:
      self.logger.debug("No subscriber information to update")
      return updates

    rsp = session.get(uriRoot + "/subscribers")
    if rsp.status_code == 200:
      subsInBqn = rsp.json()["items"]
    else:
      subsInBqn = []
    self.logger.info("Create subscribers in %s" % uriRoot)
    for s in data["subscribers"]:
      matches = [x for x in subsInBqn if x["subscriberIp"] == s["subscriberIp"]]
      # If more than one match, we take first one
      if len(matches) > 0:
        if len(matches) > 1:
          self.logger.warning("Subscriber %s found in BQN more than once, taking first one" % s["subscriberIp"])
        # subscriber group membership checked at subscriber group level
        if self.areEqual(matches[0], s, ["subscriberId", "policyRate"]):
          continue
        self.logger.debug("Subscriber changed. In BQN: %s" % matches[0])
        self.logger.debug("                In billing: %s" % s)
      self.logger.debug("Create subscriber %s" % s["subscriberIp"])
      payload = self.jsonDumps(s)
      rsp = session.post(uriRoot + "/subscribers/" + s["subscriberIp"], data=payload)
      self.printResponseDetails(rsp) 
      updates += 1

    return updates

  ############################################################################

  def updateBqnSubscriberGroups(self, uriRoot, session, data):
    updates = 0

    if not "subscriberGroups" in data or len(data["subscriberGroups"]) == 0:
      self.logger.debug("No subscriber group information to update")
      return updates

    rsp = session.get(uriRoot + "/subscriberGroups")
    if rsp.status_code == 200:
      sgsInBqn = rsp.json()["items"]
    else:
      sgsInBqn = []
    for sg in data["subscriberGroups"]:
      matches = [x for x in sgsInBqn if x["subscriberGroupName"] == sg["subscriberGroupName"]]
      if len(matches) > 0:
        if len(matches) > 1:
          self.logger.warning("Subscriber group %s found more than once, comparing with first one" % sg["subscriberGroupName"])
        if self.areEqual(matches[0], sg, ["subscriberMembers", "subscriberRanges", "policyRate"]):
          continue
      self.logger.debug("Create subscriber group %s" %  sg["subscriberGroupName"])
      groupName = requests.utils.quote(sg["subscriberGroupName"], safe='')  # Empty safe char list, so / is not regarded as safe and encoded as well
      payload = self.jsonDumps(sg)
      rsp = session.post(uriRoot + "/subscriberGroups/" + groupName, data=payload)
      self.printResponseDetails(rsp)
      updates += 1
    
    return updates

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
    # To support TLS1.2 (python default too stringent)
    if int(PY_VERSION[1]) >= 7:  # 3.7 or more
      session.mount(uriRoot, BqnRestAdapter())

    # Adapt data to BQN format
    for item in data["policies"] + data["subscribers"] + data["subscriberGroups"]:
      self.normalize(item)
    # Add fields not treated by billing
    for p in data["policies"]:
      p["rateLimitDownlink"]["congestionMgmt"] = True
    # Blocked subscribers have block policy
    for s in data["subscribers"]:
      if s["block"]:
        s["policyRate"] = BillingSync.BLOCK_POLICY
      # Remove block/state fields, unknown to BQN and no longer needed
      del s["block"]        
      del s["state"]        

    updatedPolicies = self.updateBqnPolicies(uriRoot, session, data)
    updatedSubscribers = self.updateBqnSubscribers(uriRoot, session, data)
    updatedSubscriberGroups = self.updateBqnSubscriberGroups(uriRoot, session, data)

    self.logger.warning("%s synchronization of %d policies, %d subscribers and %d groups" % \
                 (datetime.datetime.now(), updatedPolicies, updatedSubscribers, updatedSubscriberGroups))

  ################################################################################

