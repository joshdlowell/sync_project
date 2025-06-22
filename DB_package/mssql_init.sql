-- Create helper function for UNIX timestamp (MSSQL doesn't have built-in UNIX_TIMESTAMP)
CREATE FUNCTION dbo.UNIX_TIMESTAMP()
RETURNS BIGINT
AS
BEGIN
    RETURN DATEDIFF(SECOND, '1970-01-01 00:00:00', GETUTCDATE())
END;

-- Create hashtable
CREATE TABLE hashtable (
    path NVARCHAR(MAX) NOT NULL,
    hashed_path AS CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', path), 2) PERSISTED PRIMARY KEY,
    current_hash VARCHAR(40) NOT NULL,
    current_dtg_latest INT DEFAULT (dbo.UNIX_TIMESTAMP()),
    current_dtg_first INT DEFAULT (dbo.UNIX_TIMESTAMP()),
    target_hash VARCHAR(40),
    prev_hash VARCHAR(40),
    prev_dtg_latest INT,
    dirs NVARCHAR(MAX),
    files NVARCHAR(MAX),
    links NVARCHAR(MAX)
);

-- Create logs table
CREATE TABLE logs (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    site_id VARCHAR(5) DEFAULT 'local',
    log_level VARCHAR(10) CHECK (log_level IN ('ERROR', 'STATUS', 'WARNING', 'INFO')) DEFAULT 'INFO',
    timestamp INT DEFAULT (dbo.UNIX_TIMESTAMP()),
    summary_message NVARCHAR(MAX) NOT NULL,
    detailed_message NVARCHAR(MAX)
);