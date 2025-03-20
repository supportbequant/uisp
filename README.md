
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
root@bqn# mkdir uisp
```
Where \<BQN-OAM-IP\> is the management IP address of the BQN server.

4. Transfer the files from the PC to the BQN server using scp:
```
scp ./uisp-main/* root@<BQN-OAM-IP>:uisp
```

5. Make sure the following files are executable in BQN:
```
ssh root@<BQN-OAM-IP>
root@bqn# chmod a+x ./uisp/setup-uisp.sh
root@bqn# chmod a+x ./uisp/disable.sh
root@bqn# chmod a+x ./uisp/sync-uisp-bqn
```

6. Run the setup script and enter the parameters:
Example:
```
root@bqn# cd uisp
./setup-sh
BQN OAM IP: 192.168.0.121
BQN REST user: myuser
BQN REST password: mypassword
UISP server: myserver.uisp.com
UISP API KEY: 5a15d248-376b-1324-cd15-24ad3a37be31
Get only location groups? (n for full synchronization) (y/n): n
We are about to setup a cron script with these parameters:
  BQN OAM IP: 192.168.0.121
  BQN REST user: myuser
  BQN REST password: mypassword
  UISP server: myserver.uisp.com
  UISP API KEY: 5a15d248-376b-1324-cd15-24ad3a37be31
  Only location groups: false
Do you want to proceed? (y/n): y
Activated billing synchronization
root@bqn#

7. If DNS is needed (BQN server or UISP use domain names), verify that the BQN has the DNS configured (see [DNS configuration](https://www.bequant.com/docs/initial-configuration#changing-the-management-ip-address)).

And that's all, the script will access the UISP every 5 minutes and update the BQN accordingly.
You can check the script log in the BQN:

```
root@bqn# less /tmp/sync-uisp-bqn.log
2024-01-08 12:42:02.430413 synchronization script starts (v1.6)
2024-01-08 12:42:12.478919 synchronization of 15 policies and 327 subscribers
2024-01-08 12:42:12.479752 synchronization script ends
```

To see the policies and subscribers created in the BQN server, see the section
"Check the REST API" in https://www.bequant.com/docs/rest#rest-configuration


## Update scripts

To update the synchronization scripts, do the following:

1. Go to code (repository)[https://github.com/supportbequant/uisp] and get the code zip file (in repository home page, go to Code->Download ZIP).

2. Unzip the code zip file. For example with unzip command:
```
unzip uisp-main.zip
```
This will create a subdirectory named uisp-main.

3. Transfer the files from the PC to the BQN server using scp:
```
scp ./uisp-main/* root@<BQN-OAM-IP>:uisp
```
Where \<BQN-OAM-IP\> is the management IP address of the BQN server.

4. Make sure the following updated files remains executable in BQN:
```
ssh root@<BQN-OAM-IP>
root@bqn# chmod a+x ./uisp/setup-uisp.sh
root@bqn# chmod a+x ./uisp/disable.sh
root@bqn# chmod a+x ./uisp/sync-uisp-bqn
exit
```

## To stop the synchronization

```
ssh root@<BQN-OAM-IP>
root@bqn# uisp/disable.sh
Do you want to stop synchronization with UISP? (y/n): y
Synchronization with UISP removed
root@bqn#
```

## Known limitations

- The first time it may take minutes to run. Following executions will send to BQN only client changes and will be quicker.
- If the synchronization fails, no retry is attempted until the next scheduled task.
