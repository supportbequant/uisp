
# uisp-bqn-sync

Simple synchronization script between BQN and a UISP system. The script
will run on a BQN server, it will request the information from the UISP system
using the UISP REST API and update the BQN server using the BQN REST API.

## Installation

### Prerequisites

1. BQN with packages linux-R3.0.13-20231130 or later and bqn-R4.18.8 or later.

2. BQN with REST API enabled (see https://www.bequant.com/docs/rest#rest-configuration).

3. BQN with a DNS server configured (see https://www.bequant.com/docs/initial-configuration#changing-the-management-ip-address).

4. UISP with REST API enabled with access to both NMS and CRM. A common API KEY 
for both types of access must be created.

### Steps

1. Go to code [repository](https://github.com/supportbequant/uisp) and get the code zip file (in repository home page, go to Code->Download ZIP).
![github code zip](github-uisp-get-zip.png)

2. Unzip the code zip file. For example with unzip command:
```
unzip uisp-main.zip
```
This will create a subdirectory named uisp-main.

3. Create a uisp directory in the BQN server root account:
```
ssh root@<BQN-OAM-IP>
mkdir uisp
exit
```
Where \<BQN-OAM-IP\> is the management IP address of the BQN server.

4. Edit the file sync-uisp-bqn.sh to set the parameters to your environment values.
Example:
```
. . .
# BQN management IP address
BQN_OAM_IP=192.168.0.121
# Name of the REST user in the BQN server
BQN_REST_USER=myuser
# Password of the REST user in the BQN server
BQN_REST_PW=mypassword
# IP address or domain of the UISP server
UISP_SERVER=myserver.uisp.com
# REST API KEY of the UISP server
UISP_KEY=5a15d248-376b-1324-cd15-24ad3a37be31
. . .
```

5. Transfer the following files from the PC to the BQN server using scp:
```
scp ./uisp-main/BillingSync.py  ./uisp-main/sync-uisp-bqn ./uisp-main/sync-uisp-bqn.sh root@<BQN-OAM-IP>:uisp
```

6. Make sure the following files are executable in BQN:
```
ssh root@<BQN-OAM-IP>
cd uisp
chmod a+x ./uisp/sync-uisp-bqn
chnod a+x ./uisp/sync-uisp-bqn.sh
exit
```

7. In the BQN, copy sync-uisp-bqn.sh to the crontab directory so it is executed every 5 minutes:
```
ssh root@<BQN-OAM-IP>
cp uisp/sync-uisp-bqn.sh /bqn/root/etc/cron.5
``` 
8. If DNS is needed (BQN server or UISP use domain names), verify that the BQN has the DNS configured (see [DNS configuration](https://www.bequant.com/docs/initial-configuration#changing-the-management-ip-address)).

And that's all, the script will access the UISP every 5 minutes and update the BQN accordingly.
You can check the script log in the BQN:

```
ssh root@<BQN-OAM-IP>
less /tmp/sync-uisp-bqn.log
2024-01-08 12:42:02.430413 synchronization script starts (v1.6)
2024-01-08 12:42:12.478919 synchronization of 15 policies and 327 subscribers
2024-01-08 12:42:12.479752 synchronization script ends
```

To see the policies and subscribers created in the BQN server, see the section
"Check the REST API" in https://www.bequant.com/docs/rest#rest-configuration


## Updates

To update the synchronization script, do the following:

1. Go to code (repository)[https://github.com/supportbequant/uisp] and get the code zip file (in repository home page, go to Code->Download ZIP).

2. Unzip the code zip file. For example with unzip command:
```
unzip uisp-main.zip
```
This will create a subdirectory named uisp-main.

3. Transfer the following files from the PC to the BQN server using scp:
```
scp ./uisp-main/BillingSync.py  ./uisp-main/sync-uisp-bqn root@<BQN-OAM-IP>:uisp
```
Where \<BQN-OAM-IP\> is the management IP address of the BQN server. NOTE 
that the sync-uisp-bqn.sh MUST NOT be updated.

4. Make sure the following updated file remains executable in BQN:
```
ssh root@<BQN-OAM-IP>
cd uisp
chmod a+x ./uisp-main/sync-uisp-bqn
exit
```

## Known limitations

- The first time it may take minutes to run. Following executions will send to BQN only client changes and will be quicker.
- If the synchronization fails, no retry is attempted until the next scheduled task.


