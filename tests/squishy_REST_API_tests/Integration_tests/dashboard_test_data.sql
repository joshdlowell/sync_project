-- ===================================================
-- TEST DATA POPULATION SCRIPT
-- ===================================================


-- Define db to use
USE squishy_db;

-- Insert test sites into the authoritative site list
INSERT INTO site_list (site_name, online) VALUES
('SITE1', 1),
('SITE2', 1),
('SITE3', 1),
('SITE4', 1),
('SITE5', 1),
('SITE6', 1),
('SITE7', 1),
('SITE8', 1);

-- Insert state history with different timestamps to test sync status
-- Current baseline (most recent) - created 1 hour ago
INSERT INTO state_history (update_id, hash_value, record_count, created_at) VALUES
('update_current', 'abc123current456789012345678901234567890', 1000, UNIX_TIMESTAMP(NOW() - INTERVAL 1 HOUR));

-- Previous baseline (second most recent) - created 2 hours ago
INSERT INTO state_history (update_id, hash_value, record_count, created_at) VALUES
('update_previous', 'def456previous789012345678901234567890', 950, UNIX_TIMESTAMP(NOW() - INTERVAL 2 HOUR));

-- Hash from within last 24 hours - created 12 hours ago
INSERT INTO state_history (update_id, hash_value, record_count, created_at) VALUES
('update_l24', 'ghi789within24h012345678901234567890', 900, UNIX_TIMESTAMP(NOW() - INTERVAL 12 HOUR));

-- Hash from more than 24 hours ago - created 48 hours ago
INSERT INTO state_history (update_id, hash_value, record_count, created_at) VALUES
('update_g24', 'jkl012older24h345678901234567890', 850, UNIX_TIMESTAMP(NOW() - INTERVAL 48 HOUR));

-- Hash not in history (we'll reference this but not insert it)
-- This will be used to test sync_unknown status

-- Insert sites with different sync and live statuses
-- SITE1: sync_current, live_current (last updated 10 minutes ago)
INSERT INTO sites (site_name, current_hash, last_updated) VALUES
('SITE1', 'abc123current456789012345678901234567890', UNIX_TIMESTAMP(NOW() - INTERVAL 10 MINUTE));

-- SITE2: sync_1_behind, live_1_behind (last updated 1 hour ago)
INSERT INTO sites (site_name, current_hash, last_updated) VALUES
('SITE2', 'def456previous789012345678901234567890', UNIX_TIMESTAMP(NOW() - INTERVAL 1 HOUR));

-- SITE3: sync_l24_behind, live_l24_behind (last updated 12 hours ago)
INSERT INTO sites (site_name, current_hash, last_updated) VALUES
('SITE3', 'ghi789within24h012345678901234567890', UNIX_TIMESTAMP(NOW() - INTERVAL 12 HOUR));

-- SITE4: sync_g24_behind, live_inactive (last updated 48 hours ago)
INSERT INTO sites (site_name, current_hash, last_updated) VALUES
('SITE4', 'jkl012older24h345678901234567890', UNIX_TIMESTAMP(NOW() - INTERVAL 48 HOUR));

-- SITE5: sync_unknown, live_inactive (hash not in state_history, last updated 30 hours ago)
INSERT INTO sites (site_name, current_hash, last_updated) VALUES
('SITE5', NULL, UNIX_TIMESTAMP(NOW() - INTERVAL 30 HOUR));

-- SITE6: sync_unknown, live_inactive (no operational data - site exists but not in sites table)
-- This site will only exist in site_list

-- SITE7: sync_current, live_current (last updated 5 minutes ago)
INSERT INTO sites (site_name, current_hash, last_updated) VALUES
('SITE7', 'abc123current456789012345678901234567890', UNIX_TIMESTAMP(NOW() - INTERVAL 5 MINUTE));

-- SITE8: sync_1_behind, live_1_behind (last updated 45 minutes ago)
INSERT INTO sites (site_name, current_hash, last_updated) VALUES
('SITE8', 'def456previous789012345678901234567890', UNIX_TIMESTAMP(NOW() - INTERVAL 45 MINUTE));

-- Insert some critical errors for the last 24 hours
-- Recent critical errors (within 24h)
INSERT INTO logs (site_id, session_id, log_level, timestamp, summary_message, detailed_message) VALUES
('SITE1', 'session001', 'CRITICAL', UNIX_TIMESTAMP(NOW() - INTERVAL 2 HOUR), 'Critical error on SITE1', 'Detailed error message for SITE1'),
('SITE2', 'session002', 'CRITICAL', UNIX_TIMESTAMP(NOW() - INTERVAL 4 HOUR), 'Critical error on SITE2', 'Detailed error message for SITE2'),
('SITE3', 'session003', 'CRITICAL', UNIX_TIMESTAMP(NOW() - INTERVAL 6 HOUR), 'Critical error on SITE3', 'Detailed error message for SITE3');

-- Older critical errors (more than 24h ago - should not be counted)
INSERT INTO logs (site_id, session_id, log_level, timestamp, summary_message, detailed_message) VALUES
('SITE4', 'session004', 'CRITICAL', UNIX_TIMESTAMP(NOW() - INTERVAL 30 HOUR), 'Old critical error on SITE4', 'This should not be counted'),
('SITE5', 'session005', 'CRITICAL', UNIX_TIMESTAMP(NOW() - INTERVAL 48 HOUR), 'Old critical error on SITE5', 'This should not be counted');

-- Non-critical errors (should not be counted)
INSERT INTO logs (site_id, session_id, log_level, timestamp, summary_message, detailed_message) VALUES
('SITE1', 'session006', 'ERROR', UNIX_TIMESTAMP(NOW() - INTERVAL 1 HOUR), 'Regular error on SITE1', 'This should not be counted'),
('SITE2', 'session007', 'WARNING', UNIX_TIMESTAMP(NOW() - INTERVAL 3 HOUR), 'Warning on SITE2', 'This should not be counted');

-- Critical error from site not in site_list (should not be counted)
INSERT INTO logs (site_id, session_id, log_level, timestamp, summary_message, detailed_message) VALUES
('BADST', 'session008', 'CRITICAL', UNIX_TIMESTAMP(NOW() - INTERVAL 1 HOUR), 'Critical error from unauthorized site', 'This should not be counted');

-- Display expected results
SELECT '=== EXPECTED DASHBOARD RESULTS ===' as info;
SELECT
    'crit_error_count: 3 (SITE1, SITE2, SITE3 within 24h)' as expected_result
UNION ALL SELECT 'hash_record_count: 1000 (from current baseline)'
UNION ALL SELECT 'sync_current: 2 (SITE1, SITE7)'
UNION ALL SELECT 'sync_1_behind: 2 (SITE2, SITE8)'
UNION ALL SELECT 'sync_l24_behind: 1 (SITE3)'
UNION ALL SELECT 'sync_g24_behind: 1 (SITE4)'
UNION ALL SELECT 'sync_unknown: 2 (SITE5 has unknown hash, SITE6 has no data)'
UNION ALL SELECT 'live_current: 2 (SITE1, SITE7 updated within 35 minutes)'
UNION ALL SELECT 'live_1_behind: 2 (SITE2, SITE8 updated between 35m-24h ago)'
UNION ALL SELECT 'live_l24_behind: 1 (SITE3 updated within 24h)'
UNION ALL SELECT 'live_inactive: 3 (SITE4, SITE5, SITE6 no updates or >24h ago)';

SELECT '=== TEST DATA INSERTED SUCCESSFULLY ===' as status;
