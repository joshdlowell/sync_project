```python
# Get all logs (original behavior)
all_logs = self.get_logs()

# Get logs to ship (session_id is NULL)
logs_to_ship = self.get_logs(session_id_filter='null')

# Get logs for a specific session
session_logs = self.get_logs(session_id_filter='some_session_id')

# Get logs to ship with pagination
logs_to_ship_page = self.get_logs(limit=100, offset=0, session_id_filter='null')
```

If you still want to keep the `collect_logs_to_ship()` method for convenience (which might be cleaner for the API), you can implement it as a simple wrapper:

```python
def collect_logs_to_ship(self) -> list[dict[str, Any]]:
    """
    Find entries in the database that have not been forwarded to the core database yet.

    Returns:
        List of dicts containing log entries to be shipped.
    """
    return self.get_logs(session_id_filter='null')
```