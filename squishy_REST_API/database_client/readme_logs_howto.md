## How to Format Log Entries for Consolidation

To ensure your log entries are properly processed by the consolidation method, follow these formatting guidelines:

### 1. **Session Management Messages**
- **Start Session**: Use summary messages containing "START SESSION" (case-sensitive)
  - Set `detailed_message` to the session type (e.g., "File Processing", "Data Import")
  - Example: `summary_message = "START SESSION - File Processing"`

- **Finish Session**: Use summary messages containing "FINISH SESSION" (case-sensitive)
  - Set `detailed_message` to the session type (for showing up in the core logs)
  - Example: `summary_message = "FINISH SESSION - File Processing"`

### 2. **JSON-Encoded Detailed Messages**
Format your `detailed_message` as a JSON string with the following structure:
```json
{
  "created": ["file1.txt", "file2.txt"],
  "modified": ["config.json", "data.csv"],
  "deleted": ["temp.log"],
  "errors": ["Permission denied on file3.txt"],
  "custom_field": ["value1", "value2"]
}
```

### 3. **Log Entry Requirements**
- **session_id**: Must be consistent across all entries in a session
- **log_level**: Will be used to group entries (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **site_id**: Should be consistent within a session
- **summary_message**: Descriptive text for the log entry
- **detailed_message**: Either JSON-encoded data or plain text

### 4. **Example Usage**
```python
# Session start
self.put_log({
    'session_id': 'batch_001',
    'log_level': 'INFO',
    'summary_message': 'START SESSION - Data Processing',
    'detailed_message': 'Batch Data Processing'
})

# Regular entries with JSON data
self.put_log({
    'session_id': 'batch_001',
    'log_level': 'INFO',
    'summary_message': 'Files processed',
    'detailed_message': json.dumps({
        'created': ['output1.csv', 'output2.csv'],
        'modified': ['config.json']
    })
})

# Session end
self.put_log({
    'session_id': 'batch_001',
    'log_level': 'INFO',
    'summary_message': 'FINISH SESSION - Data Processing',
    'detailed_message': 'Batch Data Processing'
})
```

Now you can use it to get entries older than 90 days:

```python
# Get all logs older than 90 days
old_logs = self.get_logs(older_than_days=90)

# Get logs to ship that are older than 90 days
old_logs_to_ship = self.get_logs(session_id_filter='null', older_than_days=90)

# Get logs older than 90 days with pagination
old_logs_page = self.get_logs(limit=100, offset=0, older_than_days=90)

# Get logs older than 30 days, ordered by timestamp ascending
recent_old_logs = self.get_logs(older_than_days=30, order_direction='ASC')
```

If you want a convenience method specifically for cleanup purposes, you could add:

```python
def get_logs_for_cleanup(self, days_old: int = 90) -> List[Dict[str, Any]]:
    """
    Get log entries older than specified days for cleanup purposes.
    
    Args:
        days_old: Number of days old (default: 90)
        
    Returns:
        List of log entries older than specified days
    """
    return self.get_logs(older_than_days=days_old)
```

The SQL query will use MySQL's `DATE_SUB(NOW(), INTERVAL %s DAY)` function to calculate the cutoff date, which is efficient and handles date arithmetic properly.