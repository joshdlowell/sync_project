-- Test Script for logs table
-- Run this in MySQL 9.3 container
-- Tests assume that the table(s) exist because the container is
-- configured to create them on the first run

-- Enable more detailed error reporting
SET sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- Define db to use
USE squishy_db;

-- DECLARE HANDLERs to support Tests 3, 5, 7
-- these tests are in a procedure declared before/outside the test transaction so that
-- rollback will still work (declaring a procedure forces a commit)
DELIMITER //

DROP PROCEDURE IF EXISTS test_log_insert;
DROP PROCEDURE IF EXISTS test_without_required;
DROP PROCEDURE IF EXISTS test_max_length;

-- Enforcement of required fields test 3
CREATE PROCEDURE test_without_required()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1364: invalid log entry was accepted';

    DECLARE CONTINUE HANDLER FOR 1364
    BEGIN
        SET test_result='PASSED, Caught error 1364: "summary_message" doesnt have a default value';
    END;

    SELECT '';

    INSERT INTO logs (site_id, log_level)
    VALUES ('sit0', 'info');

    SELECT test_result as 'Test 3: Summary message is required:';
END//
-- Enforcement of site_id max length test 5
CREATE PROCEDURE test_max_length()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1406: invalid length site_id was accepted';

    DECLARE CONTINUE HANDLER FOR 1406
    BEGIN
        SET test_result='PASSED, Caught error 1406: Data too long for column "test_result" at row 1';
    END;

    SELECT '';

    INSERT INTO logs (site_id, summary_message)
    VALUES ('sit0a1', 'bad site id');

    SELECT test_result as 'Test 5: site_id max length is enforced:';
END//

-- Invalid log_level test 7
CREATE PROCEDURE test_log_insert()
BEGIN
    DECLARE test_result VARCHAR(75) DEFAULT 'FAILED, did not catch error 1265: invalid log level was accepted';

    DECLARE CONTINUE HANDLER FOR 1265
    BEGIN
        SET test_result='PASSED, Caught error 1265: Data truncated for log_level';
    END;

    SELECT '';

    INSERT INTO logs (summary_message, log_level)
    VALUES ('Bad level test message', 'awful');

    SELECT test_result as 'Test 7: log_level does not accept not permitted levels:';
END//
DELIMITER ;


-- Start transaction for testing
START TRANSACTION;


-- Test 1: Insert basic record
SELECT 'Test 1: Basic insert:' as '';

-- Insert a record
INSERT INTO logs (summary_message)
VALUES ('Happy day, booting complete');

-- Verify the insert worked
SELECT
    CASE
        WHEN COUNT(*) = 1 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM logs
WHERE summary_message = 'Happy day, booting complete';

-- Test 2: Verify log_entry auto increments
SELECT 'Test 2: Verify log_entry auto increments:' as '';

-- Insert first record
INSERT INTO logs (summary_message)
VALUES ('info message');

-- Insert second record
INSERT INTO logs (summary_message)
VALUES ('info message 2');

-- Verify auto increment is working
SELECT
    CASE
        WHEN COUNT(*) = 2
        AND MAX(log_entry) - MIN(log_entry) = 1
        THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM logs
WHERE summary_message IN ('info message', 'info message 2');

-- Optional: Show the actual values for debugging
SELECT 'Debug - Actual values:' as '';
SELECT log_entry, summary_message
FROM logs
WHERE summary_message IN ('info message', 'info message 2')
ORDER BY log_entry;

-- Test 3: enforcement of required fields
CALL test_without_required();

-- Test 4: auto-population of fields
SELECT 'Test 4: auto-population of fields:' as '';
SELECT
    CASE
        WHEN log_entry IS NOT NULL
        AND site_id = 'local'
        AND log_level = 'INFO'
        AND timestamp > UNIX_TIMESTAMP() - 60
        THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM logs
WHERE summary_message ='info message';

SELECT * FROM logs;

-- Test 5: length of site_id
CALL test_max_length();

-- Test 6: log_level accepts desired levels
SELECT 'Test 6: log_level accepts desired levels:' as '';
-- test log_level accepts desired levels 'INFO'
INSERT INTO logs (summary_message, log_level)
VALUES ('INFO level test message', 'INFO');
-- Verify the insert worked
SELECT
    'key: INFO' as log_level,
    CASE

        WHEN COUNT(*) = 1 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM logs
WHERE summary_message = 'INFO level test message' AND log_level = 'INFO';
-- test log_level accepts desired levels 'ERROR'
INSERT INTO logs (summary_message, log_level)
VALUES ('ERROR level test message', 'ERROR');
-- Verify the insert worked
SELECT
    'key: ERROR' as log_level,
    CASE
        WHEN COUNT(*) = 1 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM logs
WHERE summary_message = 'ERROR level test message' AND log_level = 'ERROR';
-- test log_level accepts desired levels 'STATUS'
INSERT INTO logs (summary_message, log_level)
VALUES ('STATUS level test message', 'STATUS');
-- Verify the insert worked
SELECT
    'key: STATUS' as log_level,
    CASE
        WHEN COUNT(*) = 1 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM logs
WHERE summary_message = 'STATUS level test message' AND log_level = 'STATUS';
-- test log_level accepts desired levels 'WARNING'
INSERT INTO logs (summary_message, log_level)
VALUES ('WARNING level test message', 'WARNING');
-- Verify the insert worked
SELECT
    'key: WARNING' as log_level,
    CASE
        WHEN COUNT(*) = 1 THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result
FROM logs
WHERE summary_message = 'WARNING level test message' AND log_level = 'WARNING';

-- Test 7: log_level does not accept other levels
CALL test_log_insert();

-- Test 8: Test full insert
SELECT 'Test 8: Test all values are populated:' as '';
INSERT INTO logs (
    site_id,
    log_level,
    timestamp,
    summary_message,
    detailed_message
) VALUES (
    'SIT0',
    'STATUS',
    UNIX_TIMESTAMP() + 1002,
    'Test status message',
    'This is a test status message for testing'
);

-- Verbose output

SELECT
    CASE
        WHEN site_id = 'SIT0'
        AND log_level = 'STATUS'
        AND timestamp > UNIX_TIMESTAMP() + 1000
        AND summary_message = 'Test status message'
        AND detailed_message = 'This is a test status message for testing'
        THEN 'PASSED'
        ELSE 'FAILED'
    END as test_result,
    site_id,
    log_level,
    timestamp,
    summary_message,
    detailed_message
FROM logs
WHERE site_id = 'SIT0' AND summary_message = 'Test status message';

-- Test 9: Test site_id and log_level are case-insensitive
SELECT 'Test 9: Test site_id and log_level are case-insensitive:' as '';

SELECT
    CASE
        WHEN COUNT(*) > 0 THEN 'PASSED'
        ELSE 'FAILED'
    END as site_id
FROM logs
WHERE site_id = 'LoCaL';
SELECT
    CASE
        WHEN COUNT(*) > 0 THEN 'PASSED'
        ELSE 'FAILED'
    END as log_level
FROM logs
WHERE log_level = 'info';


-- Test Summary
SELECT '';
SELECT '=== TEST SUMMARY ===' as summary;

SELECT
    'Total records inserted: ' as metric,
    COUNT(*) as value
FROM logs;

SELECT
    'Unique entries: ' as metric,
    COUNT(DISTINCT log_entry) as value
FROM logs;

SELECT
    'Records with all fields populated: ' as metric,
    COUNT(*) as value
FROM logs
WHERE detailed_message IS NOT NULL;

-- Display all test data
SELECT '=== ALL TEST DATA ===' as data_review;
SELECT * FROM logs ORDER BY log_entry;

-- Rollback transaction to clean up test data
ROLLBACK;

SELECT 'All tests completed. Transaction rolled back to clean up test data.' as final_message;
