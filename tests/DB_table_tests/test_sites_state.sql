-- Test Script for sites_state_init tables (site_list, state_history, sites)
-- Run this in MySQL 9.3 container
-- Tests assume that the tables exist because the container is
-- configured to create them on the first run

-- Enable more detailed error reporting
SET sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Define db to use
USE squishy_db;

-- DECLARE HANDLERs to support constraint and foreign key tests
-- these tests are in procedures declared before/outside the transaction so that
-- rollback will still work (declaring procedures forces a commit)
DELIMITER //

DROP PROCEDURE IF EXISTS test_site_name_required;
DROP PROCEDURE IF EXISTS test_site_name_unique;
DROP PROCEDURE IF EXISTS test_foreign_key_site_name;
DROP PROCEDURE IF EXISTS test_foreign_key_hash_value;
DROP PROCEDURE IF EXISTS test_site_name_max_length;
DROP PROCEDURE IF EXISTS test_update_id_required;
DROP PROCEDURE IF EXISTS test_hash_value_required;
DROP PROCEDURE IF EXISTS test_null_current_hash_allowed;

-- Test required field enforcement for site_list
CREATE PROCEDURE test_site_name_required()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1364: site_name is required';

    DECLARE CONTINUE HANDLER FOR 1364
    BEGIN
        SET test_result='PASSED, Caught error 1364: Field "site_name" doesnt have a default value';
    END;

    SELECT '';

    INSERT INTO site_list (online) VALUES (1);

    SELECT test_result as 'Test 3: site_name is required:';
END//

-- Test unique constraint for site_name
CREATE PROCEDURE test_site_name_unique()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1062: duplicate site_name was accepted';

    DECLARE CONTINUE HANDLER FOR 1062
    BEGIN
        SET test_result='PASSED, Caught error 1062: Duplicate entry for site_name';
    END;

    SELECT '';

    INSERT INTO site_list (site_name) VALUES ('TEST1');

    SELECT test_result as 'Test 4: site_name unique constraint:';
END//

-- Test site_name max length enforcement
CREATE PROCEDURE test_site_name_max_length()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1406: site_name too long was accepted';

    DECLARE CONTINUE HANDLER FOR 1406
    BEGIN
        SET test_result='PASSED, Caught error 1406: Data too long for column site_name';
    END;

    SELECT '';

    INSERT INTO site_list (site_name) VALUES ('TOOLONG');

    SELECT test_result as 'Test 5: site_name max length enforcement:';
END//

-- Test required field enforcement for state_history
CREATE PROCEDURE test_update_id_required()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1364: update_id is required';

    DECLARE CONTINUE HANDLER FOR 1364
    BEGIN
        SET test_result='PASSED, Caught error 1364: Field "update_id" doesnt have a default value';
    END;

    SELECT '';

    INSERT INTO state_history (hash_value) VALUES ('abcd1234567890123456789012345678901234ab');

    SELECT test_result as 'Test 9: update_id is required:';
END//

CREATE PROCEDURE test_hash_value_required()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1364: hash_value is required';

    DECLARE CONTINUE HANDLER FOR 1364
    BEGIN
        SET test_result='PASSED, Caught error 1364: Field "hash_value" doesnt have a default value';
    END;

    SELECT '';

    INSERT INTO state_history (update_id) VALUES ('test-update-123');

    SELECT test_result as 'Test 10: hash_value is required:';
END//

-- Test foreign key constraint for sites table
CREATE PROCEDURE test_foreign_key_site_name()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1452: invalid foreign key was accepted';

    DECLARE CONTINUE HANDLER FOR 1452
    BEGIN
        SET test_result='PASSED, Caught error 1452: Foreign key constraint fails for site_name';
    END;

    SELECT '';

    INSERT INTO sites (site_name) VALUES ('BADID');

    SELECT test_result as 'Test 15: Foreign key constraint on site_name:';
END//

CREATE PROCEDURE test_foreign_key_hash_value()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1452: invalid foreign key was accepted';

    DECLARE CONTINUE HANDLER FOR 1452
    BEGIN
        SET test_result='PASSED, Caught error 1452: Foreign key constraint fails for current_hash';
    END;

    SELECT '';

    -- Use a valid site_name but invalid hash_value (non-NULL)
    INSERT INTO sites (site_name, current_hash) VALUES ('TEST2', 'badhash12345678901234567890123456789012');

    SELECT test_result as 'Test 16: Foreign key constraint on current_hash:';
END//

CREATE PROCEDURE test_null_current_hash_allowed()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, NULL current_hash was rejected';
    DECLARE test_completed BOOLEAN DEFAULT FALSE;

    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
    BEGIN
        SET test_result = 'FAILED, NULL current_hash caused an error';
        SET test_completed = TRUE;
    END;

    SELECT '';

    INSERT INTO sites (site_name, current_hash) VALUES ('TEST2', NULL);

    IF NOT test_completed THEN
        SET test_result = 'PASSED, NULL current_hash was accepted';
    END IF;

    SELECT test_result as 'Test 16.5: NULL current_hash is allowed:';
END//

DELIMITER ;

-- Start transaction for testing
START TRANSACTION;

-- =============================================================================
-- SITE_LIST TABLE TESTS
-- =============================================================================

-- Test 1: Basic insert into site_list
SELECT 'Test 1: Basic insert into site_list:' as '';
INSERT INTO site_list (site_name) VALUES ('TEST1');

SELECT
    CASE
        WHEN COUNT(*) = 1 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM site_list
WHERE site_name = 'TEST1';

-- Test 2: Verify default values for site_list
SELECT 'Test 2: Verify default values for site_list:' as '';
SELECT
    CASE
        WHEN online = 1 AND id IS NOT NULL THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    id,
    site_name,
    online
FROM site_list
WHERE site_name = 'TEST1';

-- Test 3: Required field enforcement
CALL test_site_name_required();

-- Test 4: Unique constraint test
CALL test_site_name_unique();

-- Test 5: Max length enforcement
CALL test_site_name_max_length();

-- Test 6: Insert with all fields specified
SELECT 'Test 6: Insert with all fields specified:' as '';
INSERT INTO site_list (site_name, online) VALUES ('TEST2', 0);

SELECT
    CASE
        WHEN site_name = 'TEST2' AND online = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    id,
    site_name,
    online
FROM site_list
WHERE site_name = 'TEST2';

-- =============================================================================
-- STATE_HISTORY TABLE TESTS
-- =============================================================================

-- Test 7: Basic insert into state_history
SELECT 'Test 7: Basic insert into state_history:' as '';
INSERT INTO state_history (update_id, hash_value)
VALUES ('update-001', 'a1b2c3d4e5f6789012345678901234567890abcd');

SELECT
    CASE
        WHEN COUNT(*) = 1 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM state_history
WHERE update_id = 'update-001'
    AND hash_value = 'a1b2c3d4e5f6789012345678901234567890abcd';

-- Test 8: Verify default timestamp generation
SELECT 'Test 8: Verify default timestamp generation:' as '';
SELECT
    CASE
        WHEN created_at > NOW() - 60 AND id IS NOT NULL THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    id,
    update_id,
    hash_value,
    created_at
FROM state_history
WHERE update_id = 'update-001';

-- Test 9: Required field enforcement - update_id
CALL test_update_id_required();

-- Test 10: Required field enforcement - hash_value
CALL test_hash_value_required();

-- Test 11: Insert with all fields
SELECT 'Test 11: Insert with all fields:' as '';
INSERT INTO state_history (update_id, hash_value, record_count, created_at)
VALUES ('update-002', 'b2c3d4e5f6789012345678901234567890abcdef', 150, TIMESTAMP('2024-01-15 12:30:00'));

SELECT
    CASE
        WHEN update_id = 'update-002'
        AND hash_value = 'b2c3d4e5f6789012345678901234567890abcdef'
        AND record_count = 150
        AND created_at = TIMESTAMP('2024-01-15 12:30:00')
        THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    id,
    update_id,
    hash_value,
    record_count,
    created_at
FROM state_history
WHERE update_id = 'update-002';

-- Test 12: Test index performance (basic check)
SELECT 'Test 12: Index existence check:' as '';
SELECT
    CASE
        WHEN COUNT(*) >= 2 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    'Indexes found for state_history' as note
FROM information_schema.statistics
WHERE table_schema = 'squishy_db'
    AND table_name = 'state_history'
    AND index_name IN ('idx_hash_value', 'idx_created_at');

-- =============================================================================
-- SITES TABLE TESTS
-- =============================================================================

-- Test 13: Basic insert into sites (should work with existing site_list entry)
SELECT 'Test 13: Basic insert into sites:' as '';
INSERT INTO sites (site_name) VALUES ('TEST1');

SELECT
    CASE
        WHEN COUNT(*) = 1 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM sites
WHERE site_name = 'TEST1';

-- Test 14: Verify default timestamp and auto-increment
SELECT 'Test 14: Verify default timestamp and auto-increment:' as '';
SELECT
    CASE
        WHEN last_updated > NOW() - 60 AND id IS NOT NULL THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    id,
    site_name,
    current_hash,
    last_updated
FROM sites
WHERE site_name = 'TEST1';

-- Test 15: Foreign key constraint - invalid site_name
SELECT 'Test 15: Foreign key constraint on site_name:' as '';
SAVEPOINT before_test15;
CALL test_foreign_key_site_name();
ROLLBACK TO SAVEPOINT before_test15;

-- Test 16: Foreign key constraint on current_hash
SELECT 'Test 16: Foreign key constraint on current_hash:' as '';
SAVEPOINT before_test16;
CALL test_foreign_key_hash_value();
ROLLBACK TO SAVEPOINT before_test16;

-- Test 16.5: NULL current_hash is allowed
SELECT 'Test 16: NULL current_hash is allowed:' as '';
SAVEPOINT before_test16_5;
CALL test_null_current_hash_allowed();
ROLLBACK TO SAVEPOINT before_test16_5;

-- Test 17: Valid insert with foreign key references
SELECT 'Test 17: Valid insert with foreign key references:' as '';
INSERT INTO sites (site_name, current_hash)
VALUES ('TEST2', 'a1b2c3d4e5f6789012345678901234567890abcd');

SELECT
    CASE
        WHEN site_name = 'TEST2'
        AND current_hash = 'a1b2c3d4e5f6789012345678901234567890abcd'
        THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    id,
    site_name,
    current_hash,
    last_updated
FROM sites
WHERE site_name = 'TEST2';

-- Test 18: Update operation and ON UPDATE trigger
SELECT 'Test 18: Update operation and ON UPDATE trigger:' as '';
-- Record the original timestamp
SET @original_timestamp = (SELECT last_updated FROM sites WHERE site_name = 'TEST2');

-- Wait a moment and update
SELECT SLEEP(1);
UPDATE sites SET current_hash = 'b2c3d4e5f6789012345678901234567890abcdef' WHERE site_name = 'TEST2';

SELECT
    CASE
        WHEN last_updated > @original_timestamp THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    @original_timestamp as original_timestamp,
    last_updated as new_timestamp
FROM sites
WHERE site_name = 'TEST2';

# -- Test 19: Test NULL current_hash is allowed
# SELECT 'Test 19: Test NULL current_hash is allowed:' as '';
# INSERT INTO sites (site_name, current_hash) VALUES ('TEST4', NULL);
# SELECT SLEEP(1);
# SELECT
#     CASE
#         WHEN current_hash IS NULL THEN 'PASSED'
#         ELSE 'FAILED'
#     END as test_result,
#     id,
#     site_name,
#     current_hash,
#     last_updated
# FROM sites
# WHERE site_name = 'TEST4' AND current_hash IS NULL;

-- =============================================================================
-- STORED PROCEDURE TESTS
-- =============================================================================

-- Test 20: SyncSiteOperationalData procedure
SELECT 'Test 20: SyncSiteOperationalData procedure:' as '';

-- Add a new site to site_list that's not in sites
INSERT INTO site_list (site_name) VALUES ('TEST3');

-- Count before sync
SET @before_count = (SELECT COUNT(*) FROM sites);

-- Run the sync procedure
CALL SyncSiteOperationalData();

-- Count after sync
SET @after_count = (SELECT COUNT(*) FROM sites);

SELECT
    CASE
        WHEN @after_count = @before_count + 1
        AND EXISTS (SELECT 1 FROM sites WHERE site_name = 'TEST3')
        THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    @before_count as before_count,
    @after_count as after_count;

-- =============================================================================
-- CASCADE DELETE TESTS
-- =============================================================================

-- Test 21: Cascade delete functionality
SELECT 'Test 21: Cascade delete functionality:' as '';

-- Count sites before delete
SET @sites_before = (SELECT COUNT(*) FROM sites WHERE site_name = 'TEST3');

-- Delete from site_list (should cascade to sites)
DELETE FROM site_list WHERE site_name = 'TEST3';

-- Count sites after delete
SET @sites_after = (SELECT COUNT(*) FROM sites WHERE site_name = 'TEST3');

SELECT
    CASE
        WHEN @sites_before = 1 AND @sites_after = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    @sites_before as sites_before_delete,
    @sites_after as sites_after_delete;

-- =============================================================================
-- COMPREHENSIVE DATA INTEGRITY TESTS
-- =============================================================================

-- Test 21.5: Test ON DELETE SET NULL for current_hash
SELECT 'Test 21.5: Test ON DELETE SET NULL for current_hash:' as '';

-- First, ensure we have a site with a valid current_hash
UPDATE sites SET current_hash = 'a1b2c3d4e5f6789012345678901234567890abcd' WHERE site_name = 'TEST2';

-- Verify the hash is set
SET @hash_before = (SELECT current_hash FROM sites WHERE site_name = 'TEST2');

-- Delete the referenced hash from state_history
DELETE FROM state_history WHERE hash_value = 'a1b2c3d4e5f6789012345678901234567890abcd';

-- Check if current_hash was set to NULL
SET @hash_after = (SELECT current_hash FROM sites WHERE site_name = 'TEST2');

SELECT
    CASE
        WHEN @hash_before IS NOT NULL AND @hash_after IS NULL THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    @hash_before as hash_before_delete,
    @hash_after as hash_after_delete;

-- Test 22: Complex query test across all tables
SELECT 'Test 22: Complex query with joins:' as '';
SELECT
    CASE
        WHEN COUNT(*) > 0
        AND AVG(LENGTH(sl.site_name)) <= 5
        AND COUNT(DISTINCT s.id) = COUNT(DISTINCT sl.id)
        THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    COUNT(*) as total_joined_records,
    AVG(LENGTH(sl.site_name)) as avg_site_name_length,
    COUNT(DISTINCT s.id) as unique_sites,
    COUNT(DISTINCT sl.id) as unique_site_list_entries
FROM site_list sl
JOIN sites s ON sl.site_name = s.site_name;

-- Test 23: Data consistency check (Updated for NULL support)
SELECT 'Test 23: Data consistency across tables:' as '';
SELECT
    CASE
        WHEN orphaned_sites = 0 AND orphaned_hashes = 0 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    orphaned_sites,
    orphaned_hashes
FROM (
    SELECT
        (SELECT COUNT(*) FROM sites s LEFT JOIN site_list sl ON s.site_name = sl.site_name WHERE sl.site_name IS NULL) as orphaned_sites,
        -- Updated to only check for orphaned hashes when current_hash is NOT NULL
        (SELECT COUNT(*) FROM sites s LEFT JOIN state_history sh ON s.current_hash = sh.hash_value
         WHERE s.current_hash IS NOT NULL AND sh.hash_value IS NULL) as orphaned_hashes
) as consistency_check;

-- =============================================================================
-- TEST SUMMARY
-- =============================================================================

SELECT '';
SELECT '=== TEST SUMMARY ===' as summary;

SELECT 'Site List Records:' as metric, COUNT(*) as value FROM site_list;
SELECT 'State History Records:' as metric, COUNT(*) as value FROM state_history;
SELECT 'Sites Records:' as metric, COUNT(*) as value FROM sites;

SELECT 'Sites with current_hash:' as metric, COUNT(*) as value
FROM sites WHERE current_hash IS NOT NULL;

SELECT 'Sites with NULL current_hash:' as metric, COUNT(*) as value
FROM sites WHERE current_hash IS NULL;

SELECT 'Sites with current_hash:' as metric, COUNT(*) as value
FROM sites WHERE current_hash IS NOT NULL;

SELECT 'Online sites:' as metric, COUNT(*) as value
FROM site_list WHERE online = 1;

-- Display all test data
SELECT '=== ALL TEST DATA ===' as data_review;
SELECT 'site_list:' as table_name;
SELECT * FROM site_list ORDER BY id;

SELECT 'state_history:' as table_name;
SELECT * FROM state_history ORDER BY id;

SELECT 'sites:' as table_name;
SELECT * FROM sites ORDER BY id;

-- Rollback transaction to clean up test data
ROLLBACK;

SELECT 'All tests completed. Transaction rolled back to clean up test data.' as final_message;