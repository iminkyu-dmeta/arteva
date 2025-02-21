ALTER TABLE `ne` DROP COLUMN `snmp_agent`;
ALTER TABLE `ne` DROP COLUMN `specific_attr`;

DELETE FROM `properties` where `prop_key` = 'ne.snmp_agent.show';
DELETE FROM `properties` where `prop_key` = 'acs.assign.file-dir';
DELETE FROM `properties` where `prop_key` = 'acs.assign.bin-path';
DELETE FROM `properties` where `prop_key` = 'acs.sbc.subscriber-count-max';
DELETE FROM `properties` where `prop_key` = 'acs.sbc.subscriber-count-min';
