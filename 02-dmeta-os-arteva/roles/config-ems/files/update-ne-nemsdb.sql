ALTER TABLE `ne` ADD COLUMN `snmp_agent` tinyint(1) NOT NULL DEFAULT '1' COMMENT 'snmp agent(1: clay, 2: snmpd)';
ALTER TABLE `ne` ADD COLUMN `specific_attr` json DEFAULT NULL COMMENT 'specific attributes';
UPDATE `ne` SET specific_attr = JSON_OBJECT();

INSERT IGNORE INTO `properties` VALUES ('ne.snmp_agent.show','no',1,2,'Show snmp_agent checkbox. [no|yes]');
INSERT IGNORE INTO `properties` VALUES ('acs.assign.file-dir','/logs/RCS/HISTORY/REASSIGN/',1,0,'file path');
INSERT IGNORE INTO `properties` VALUES ('acs.assign.bin-path','/apps/RCS/acs_nsteptool/bin/nsteptool.exe',1,0,'bin path');
INSERT IGNORE INTO `properties` VALUES ('acs.sbc.subscriber-count-max','100000',1,0,'Setting the maximum value of subscribers that can be assigned. input type: number');
INSERT IGNORE INTO `properties` VALUES ('acs.sbc.subscriber-count-min','40000',1,0,'Setting the minimum value of subscribers that can be assigned. input type: number');
