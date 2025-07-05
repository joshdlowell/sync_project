-- ===================================================
-- TEST DATA CLEANUP SCRIPT
-- ===================================================

-- Define db to use
USE squishy_db;

-- Disable foreign key checks temporarily to avoid constraint issues
SET FOREIGN_KEY_CHECKS = 0;

-- Delete test data from all tables
DELETE FROM logs WHERE site_id IN ('SITE1', 'SITE2', 'SITE3', 'SITE4', 'SITE5', 'SITE6', 'SITE7', 'SITE8', 'BADSITE');

DELETE FROM sites WHERE site_name IN ('SITE1', 'SITE2', 'SITE3', 'SITE4', 'SITE5', 'SITE6', 'SITE7', 'SITE8');

DELETE FROM state_history WHERE update_id IN ('update_current', 'update_previous', 'update_l24', 'update_g24');

DELETE FROM site_list WHERE site_name IN ('SITE1', 'SITE2', 'SITE3', 'SITE4', 'SITE5', 'SITE6', 'SITE7', 'SITE8');

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Reset auto-increment counters (optional)
ALTER TABLE site_list AUTO_INCREMENT = 1;
ALTER TABLE state_history AUTO_INCREMENT = 1;
ALTER TABLE sites AUTO_INCREMENT = 1;
ALTER TABLE logs AUTO_INCREMENT = 1;

SELECT '=== TEST DATA CLEANUP COMPLETED ===' as status;