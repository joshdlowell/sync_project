To add a route that displays dynamic content from the database using HTML templates, you'll need to make a few additions to your Flask app. Here's how you can do it:

## 1. First, install Flask's template rendering dependency (if not already installed):
```bash
pip install flask
```

## 2. Create a templates directory structure:
```
your_project/
├── squishy_REST_API/
├── templates/
│   ├── base.html
│   ├── hashtable_list.html
│   └── hashtable_detail.html
└── static/ (optional, for CSS/JS)
```

## 3. Add the render_template import to your routes module:

```python
"""
Routes module for REST API package.

This module defines the API routes and registers them with the Flask application.
"""
from flask import jsonify, request, Flask, render_template

from squishy_REST_API.app_factory.database import db_instance
from squishy_REST_API.app_factory.logging_config import logger
```

## 4. Add HTML template routes to your register_routes function:

```python
def register_routes(app: Flask):
    """
    Register API routes with the Flask application.

    Args:
        app: Flask application instance
    """
    
    # Your existing API routes here...
    # (keep all your existing routes as they are)

    # NEW HTML TEMPLATE ROUTES
    @app.route('/')
    def index():
        """Display the main dashboard with hashtable overview."""
        logger.debug("GET / - Dashboard request")
        try:
            # Get some summary data from your database
            # You'll need to implement these methods in your db_instance if they don't exist
            total_records = db_instance.get_total_record_count() if hasattr(db_instance, 'get_total_record_count') else 0
            recent_updates = db_instance.get_recent_updates(limit=10) if hasattr(db_instance, 'get_recent_updates') else []
            
            return render_template('dashboard.html', 
                                 total_records=total_records,
                                 recent_updates=recent_updates)
        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            return render_template('error.html', error="Failed to load dashboard"), 500

    @app.route('/web/hashtable')
    def web_hashtable_list():
        """Display all hashtable records in HTML format."""
        logger.debug("GET /web/hashtable - HTML hashtable list request")
        try:
            # Get all records or implement pagination
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            search = request.args.get('search', '')
            
            # You'll need to implement these methods in your db_instance
            if search:
                records = db_instance.search_hash_records(search, page, per_page) if hasattr(db_instance, 'search_hash_records') else []
            else:
                records = db_instance.get_all_hash_records(page, per_page) if hasattr(db_instance, 'get_all_hash_records') else []
            
            total_count = db_instance.get_total_record_count() if hasattr(db_instance, 'get_total_record_count') else len(records)
            
            return render_template('hashtable_list.html', 
                                 records=records,
                                 page=page,
                                 per_page=per_page,
                                 total_count=total_count,
                                 search=search)
        except Exception as e:
            logger.error(f"Error rendering hashtable list: {e}")
            return render_template('error.html', error="Failed to load hashtable records"), 500

    @app.route('/web/hashtable/<path:file_path>')
    def web_hashtable_detail(file_path):
        """Display detailed view of a specific hashtable record."""
        logger.debug(f"GET /web/hashtable/{file_path} - HTML hashtable detail request")
        try:
            record = db_instance.get_hash_record(file_path)
            if not record:
                logger.info(f"Path not found: {file_path}")
                return render_template('error.html', error=f"Path not found: {file_path}"), 404
            
            return render_template('hashtable_detail.html', 
                                 record=record,
                                 file_path=file_path)
        except Exception as e:
            logger.error(f"Error rendering hashtable detail: {e}")
            return render_template('error.html', error="Failed to load record details"), 500

    @app.route('/web/priority')
    def web_priority_list():
        """Display priority updates in HTML format."""
        logger.debug("GET /web/priority - HTML priority list request")
        try:
            root_path = request.args.get('root_path', '/')
            percent = request.args.get('percent', 10, type=int)
            
            priority_records = db_instance.get_oldest_updates(root_path, percent)
            
            return render_template('priority_list.html',
                                 priority_records=priority_records,
                                 root_path=root_path,
                                 percent=percent)
        except Exception as e:
            logger.error(f"Error rendering priority list: {e}")
            return render_template('error.html', error="Failed to load priority records"), 500

    # Your existing API routes and error handlers...
    register_error_handlers(app)
    logger.info("API routes registered")
```

## 5. Create HTML template files:

**templates/base.html:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Squishy REST API{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; text-decoration: none; color: #007bff; }
        .nav a:hover { text-decoration: underline; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .error { color: red; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <nav class="nav">
        <a href="/">Dashboard</a>
        <a href="/web/hashtable">Hashtable Records</a>
        <a href="/web/priority">Priority Updates</a>
    </nav>
    
    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

**templates/dashboard.html:**
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
    {% if recent_updates %}
        <table>
            <thead>
                <tr>
                    <th>Path</th>
                    <th>Last Updated</th>
                </tr>
            </thead>
            <tbody>
                {% for update in recent_updates %}
                <tr>
                    <td><a href="/web/hashtable/{{ update.path }}">{{ update.path }}</a></td>
                    <td>{{ update.current_dtg_latest or 'N/A' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <p>No recent updates found.</p>
    {% endif %}
</div>
{% endblock %}
```

**templates/hashtable_list.html:**
```html
{% extends "base.html" %}

{% block title %}Hashtable Records - Squishy REST API{% endblock %}

{% block content %}
<h1>Hashtable Records</h1>

<form method="GET" style="margin-bottom: 20px;">
    <input type="text" name="search" value="{{ search }}" placeholder="Search paths...">
    <button type="submit">Search</button>
    {% if search %}
        <a href="/web/hashtable">Clear Search</a>
    {% endif %}
</form>

{% if records %}
    <table>
        <thead>
            <tr>
                <th>Path</th>
                <th>Hash</th>
                <th>Last Updated</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for record in records %}
            <tr>
                <td>{{ record.path or record.get('path', 'N/A') }}</td>
                <td>{{ (record.current_hash or record.get('current_hash', 'N/A'))[:20] }}...</td>
                <td>{{ record.current_dtg_latest or record.get('current_dtg_latest', 'N/A') }}</td>
                <td>
                    <a href="/web/hashtable/{{ record.path or record.get('path', '') }}">View Details</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="pagination" style="margin-top: 20px;">
        <p>Showing {{ records|length }} of {{ total_count }} records</p>
        <!-- Add pagination controls here if needed -->
    </div>
{% else %}
    <p>No records found.</p>
{% endif %}
{% endblock %}
```

**templates/hashtable_detail.html:**
```html
{% extends "base.html" %}

{% block title %}{{ file_path }} - Hashtable Detail{% endblock %}

{% block content %}
<h1>Hashtable Record Detail</h1>

<div class="record-detail">
    <h2>{{ file_path }}</h2>
    
    <table>
        <tr>
            <th>Field</th>
            <th>Value</th>
        </tr>
        {% for key, value in record.items() %}
        <tr>
            <td><strong>{{ key }}</strong></td>
            <td>{{ value }}</td>
        </tr>
        {% endfor %}
    </table>
</div>

<div style="margin-top: 20px;">
    <a href="/web/hashtable">← Back to List</a>
</div>
{% endblock %}
```

**templates/error.html:**
```html
{% extends "base.html" %}

{% block title %}Error - Squishy REST API{% endblock %}

{% block content %}
<div class="error">
    <h1>Error</h1>
    <p>{{ error }}</p>
    <a href="/">Return to Dashboard</a>
</div>
{% endblock %}
```

## 6. Make sure your Flask app is configured to find templates:

In your app factory or main app file, ensure the template directory is properly set:

```python
app = Flask(__name__, template_folder='../templates')
# or if templates are in the same directory as your app
app = Flask(__name__)
```

This setup gives you:
- A dashboard at `/`
- A list view of hashtable records at `/web/hashtable`
- Detailed views at `/web/hashtable/<path>`
- A priority list view at `/web/priority`
- All with proper error handling and navigation

The routes use your existing `db_instance` methods, so they'll work with your current database setup. You may need to implement additional database methods (like `get_all_hash_records()`, `get_total_record_count()`, etc.) depending on what functionality you want to expose in the web interface.