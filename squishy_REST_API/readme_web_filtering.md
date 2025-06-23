Here's how you can modify your template and Flask app to include a dropdown filter for recent updates:

## Modified Template (templates/dashboard.html):

```html
{% extends "base.html" %}

{% block title %}Dashboard - Squishy REST API{% endblock %}

{% block content %}
<h1>Dashboard</h1>

<div class="stats">
    <h2>Statistics</h2>
    <p><strong>Total Records:</strong> {{ total_records }}</p>
</div>

<div class="recent-updates">
    <h2>Recent Updates</h2>
    
    <!-- Filter Dropdown -->
    <div class="filter-section" style="margin-bottom: 20px;">
        <form method="GET" action="{{ url_for('dashboard') }}" id="filterForm">
            <label for="site-filter">Filter by Site:</label>
            <select name="site_filter" id="site-filter" onchange="this.form.submit()">
                <option value="">All Sites</option>
                {% for site in available_sites %}
                    <option value="{{ site }}" {% if site == selected_site %}selected{% endif %}>
                        {{ site }}
                    </option>
                {% endfor %}
            </select>
            
            <!-- Optional: Keep other existing query parameters -->
            {% for key, value in request.args.items() %}
                {% if key != 'site_filter' %}
                    <input type="hidden" name="{{ key }}" value="{{ value }}">
                {% endif %}
            {% endfor %}
        </form>
    </div>

    {% if recent_updates %}
        <table>
            <thead>
                <tr>
                    <th>Path</th>
                    <th>Site</th>
                    <th>Last Updated</th>
                </tr>
            </thead>
            <tbody>
                {% for update in recent_updates %}
                <tr>
                    <td><a href="/web/hashtable/{{ update.path }}">{{ update.path }}</a></td>
                    <td>{{ update.site_name or 'Unknown' }}</td>
                    <td>{{ update.current_dtg_latest or 'N/A' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <p>No recent updates found{% if selected_site %} for site "{{ selected_site }}"{% endif %}.</p>
    {% endif %}
</div>

<style>
.filter-section {
    padding: 10px;
    background-color: #f5f5f5;
    border-radius: 5px;
}

.filter-section label {
    margin-right: 10px;
    font-weight: bold;
}

.filter-section select {
    padding: 5px 10px;
    border: 1px solid #ddd;
    border-radius: 3px;
    font-size: 14px;
}
</style>
{% endblock %}
```

## Modified Flask Route:

```python
from flask import request

@app.route('/dashboard')
def dashboard():
    # Get filter parameter from URL
    selected_site = request.args.get('site_filter', '')
    
    # Get total records (this might need modification based on your data model)
    total_records = get_total_records()
    
    # Get available sites for dropdown
    available_sites = get_available_sites()  # You'll need to implement this
    
    # Get recent updates with optional filtering
    if selected_site:
        recent_updates = get_recent_updates_by_site(selected_site)
    else:
        recent_updates = get_recent_updates()
    
    return render_template('dashboard.html', 
                         total_records=total_records,
                         recent_updates=recent_updates,
                         available_sites=available_sites,
                         selected_site=selected_site)
```

## Helper Functions You'll Need to Implement:

```python
def get_available_sites():
    """
    Return a list of unique site names from your data
    Modify this based on your data model/database
    """
    # Example implementation - adjust for your data source
    try:
        # If using SQLAlchemy ORM
        sites = db.session.query(YourModel.site_name).distinct().filter(
            YourModel.site_name.isnot(None)
        ).all()
        return [site[0] for site in sites if site[0]]
        
        # Or if using raw SQL
        # cursor.execute("SELECT DISTINCT site_name FROM your_table WHERE site_name IS NOT NULL")
        # return [row[0] for row in cursor.fetchall()]
        
    except Exception as e:
        print(f"Error getting available sites: {e}")
        return []

def get_recent_updates_by_site(site_name, limit=10):
    """
    Get recent updates filtered by site name
    Modify this based on your data model/database
    """
    try:
        # Example implementation - adjust for your data source
        # If using SQLAlchemy ORM
        updates = db.session.query(YourModel).filter(
            YourModel.site_name == site_name
        ).order_by(YourModel.current_dtg_latest.desc()).limit(limit).all()
        
        return updates
        
    except Exception as e:
        print(f"Error getting recent updates by site: {e}")
        return []

def get_recent_updates(limit=10):
    """
    Get all recent updates (your existing function)
    """
    # Your existing implementation
    pass
```

## Alternative: AJAX-based Filtering (No Page Reload):

If you prefer filtering without page reloads, here's a JavaScript approach:

```html
<!-- Add this script section to your template -->
<script>
function filterUpdates() {
    const selectedSite = document.getElementById('site-filter').value;
    
    fetch(`/api/recent-updates?site_filter=${encodeURIComponent(selectedSite)}`)
        .then(response => response.json())
        .then(data => {
            updateTable(data.recent_updates);
        })
        .catch(error => {
            console.error('Error filtering updates:', error);
        });
}

function updateTable(updates) {
    const tbody = document.querySelector('.recent-updates tbody');
    
    if (updates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3">No recent updates found.</td></tr>';
        return;
    }
    
    tbody.innerHTML = updates.map(update => `
        <tr>
            <td><a href="/web/hashtable/${update.path}">${update.path}</a></td>
            <td>${update.site_name || 'Unknown'}</td>
            <td>${update.current_dtg_latest || 'N/A'}</td>
        </tr>
    `).join('');
}
</script>

<!-- Modify the select element -->
<select name="site_filter" id="site-filter" onchange="filterUpdates()">
```

And add this API endpoint:

```python
@app.route('/api/recent-updates')
def api_recent_updates():
    selected_site = request.args.get('site_filter', '')
    
    if selected_site:
        recent_updates = get_recent_updates_by_site(selected_site)
    else:
        recent_updates = get_recent_updates()
    
    # Convert to JSON-serializable format
    updates_data = []
    for update in recent_updates:
        updates_data.append({
            'path': update.path,
            'site_name': getattr(update, 'site_name', None),
            'current_dtg_latest': str(update.current_dtg_latest) if update.current_dtg_latest else None
        })
    
    return jsonify({'recent_updates': updates_data})
```

The first approach (form submission) is simpler and more reliable, while the AJAX approach provides a smoother user experience. Choose based on your preferences and requirements.