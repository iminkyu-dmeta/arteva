
Presence r2.0.0 APP Configuration
=========

- VMs OS: RHEL 7.6

Reuirements
------------

- Ansible version 2.7.12

Dependencies
------------

N/A

YML FILE List
------------
00-presence-variable.yml
01-presence-vmconfig.yml
02-presence-vmconfig.yml
03-presence-vmconfig.yml

VMConfig-Presence-FN3.csv : Presence VMconfig file
OSConfig-FN3.csv: Config OS file

Example Playbook
------------

1. Create ansible-playbook variables
------------
- csv file location  ../file
# ansible-playbook 00-presence-variable.yml --extra-vars "vm_csv_file=VMConfig-Presence-FN3.csv"

 Create hosts file per site
- presence_hosts
- wtc1a1_presence_hosts

ansible-playbook 00-presence-variable.yml --extra-vars "vm_csv_file=VMConfig_Presence-FN3.csv" --tags "etc_hosts"

2. 01-presence-vmconfig-nic.yml (hostname, IP, Extention partition, db license)
# ansible-playbook -u attps -i ../inventory/presence.ini 01-presence-vmconfig-nic.yml -k

3. 02-presence-vmconfig-createtable.yml  (DB TABLE CREATE, Configurtaion)
# ansible-playbook -u attps -i ../inventory/presence.ini 02-presence-vmconfig-createtable.yml -k

4. 03-presence-vmconfig-app-config.yml (configuration application and reboot)
# ansible-playbook -u attps -i ../inventory/presence.ini 03-presence-vmconfig-app-config.yml -k

5. 04-presence-sslkey-backup.yml (Backup ssl key, access token)
# ansible-playbook -u attps -i ../inventory/presence.ini 04-presence-sslkey-backup.yml -k

6. 05-presence-emsdb-backup.yml
# ansible-playbook -u attps -i ../inventory/presence.ini  05-presence-emsdb-backup.yml -k
 
7. 06-presence-verify-db-license.yml
# ansible-playbook -u attps -i ../inventory/presence.ini 06-presence-verify-db-license.yml -k 
