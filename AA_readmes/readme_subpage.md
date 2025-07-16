Here's how to organize this into a separate file and include it in your main page:

## Step 1: Create the JavaScript file

Create a subfolder structure and save the script:

```
your-project/
├── js/
│   └── charts/
│       └── minimal-chart.js
└── index.html (your main page)
```

**File: `js/charts/minimal-chart.js`**
```javascript
// Minimal Chart.js implementation for this dashboard with hover functionality
class Chart {
    constructor(ctx, config) {
        this.ctx = ctx;
        this.config = config;
        this.canvas = ctx.canvas;
        this.hoveredIndex = -1;
        this.tooltip = null;
        this.setupEventListeners();
        this.draw();
    }

    setupEventListeners() {
        // Add mouse move event listener
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            this.handleMouseMove(x, y, e);
        });

        // Add mouse leave event listener
        this.canvas.addEventListener('mouseleave', () => {
            this.hoveredIndex = -1;
            this.hideTooltip();
            this.draw();
        });
    }

    handleMouseMove(x, y, originalEvent) {
        const { type } = this.config;
        let newHoveredIndex = -1;

        if (type === 'doughnut') {
            newHoveredIndex = this.getDoughnutHoveredIndex(x, y);
        } else if (type === 'bar') {
            newHoveredIndex = this.getBarHoveredIndex(x, y);
        }

        if (newHoveredIndex !== this.hoveredIndex) {
            this.hoveredIndex = newHoveredIndex;
            this.draw();
            
            if (this.hoveredIndex >= 0) {
                this.showTooltip(originalEvent, this.hoveredIndex);
            } else {
                this.hideTooltip();
            }
        }
    }

    getDoughnutHoveredIndex(x, y) {
        const width = this.canvas.width;
        const height = this.canvas.height;
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 3;
        const innerRadius = radius * 0.6;

        const dx = x - centerX;
        const dy = y - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Check if mouse is within the doughnut area
        if (distance < innerRadius || distance > radius) {
            return -1;
        }

        // Calculate angle
        let angle = Math.atan2(dy, dx);
        angle += Math.PI / 2; // Adjust for starting at top
        if (angle < 0) angle += 2 * Math.PI;

        // Find which segment the angle falls into
        const data = this.config.data.datasets[0].data;
        const total = data.reduce((a, b) => a + b, 0);
        let currentAngle = 0;

        for (let i = 0; i < data.length; i++) {
            const sliceAngle = (data[i] / total) * 2 * Math.PI;
            if (angle >= currentAngle && angle < currentAngle + sliceAngle) {
                return i;
            }
            currentAngle += sliceAngle;
        }

        return -1;
    }

    getBarHoveredIndex(x, y) {
        const width = this.canvas.width;
        const height = this.canvas.height;
        const padding = 40;
        const data = this.config.data.datasets[0].data;
        const barWidth = (width - padding * 2) / data.length * 0.8;
        const maxValue = Math.max(...data);

        for (let i = 0; i < data.length; i++) {
            const barHeight = (data[i] / maxValue) * (height - padding * 2);
            const barX = padding + i * (width - padding * 2) / data.length + barWidth * 0.1;
            const barY = height - padding - barHeight;

            if (x >= barX && x <= barX + barWidth && y >= barY && y <= barY + barHeight) {
                return i;
            }
        }

        return -1;
    }

    showTooltip(event, index) {
        const data = this.config.data.datasets[0].data[index];
        const label = this.config.data.labels[index];
        
        // Remove existing tooltip
        this.hideTooltip();
        
        // Create tooltip element
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'chart-tooltip';
        this.tooltip.innerHTML = `
            <div style="
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                font-family: Arial, sans-serif;
                position: absolute;
                pointer-events: none;
                z-index: 1000;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            ">
                <strong>${label}</strong><br>
                Count: ${data}
            </div>
        `;
        
        // Position tooltip
        const rect = this.canvas.getBoundingClientRect();
        this.tooltip.style.left = (event.clientX + 10) + 'px';
        this.tooltip.style.top = (event.clientY - 10) + 'px';
        this.tooltip.style.position = 'fixed';
        
        document.body.appendChild(this.tooltip);
    }

    hideTooltip() {
        if (this.tooltip) {
            document.body.removeChild(this.tooltip);
            this.tooltip = null;
        }
    }

    draw() {
        const { type, data, options } = this.config;
        const canvas = this.canvas;
        const ctx = this.ctx;
        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);

        if (type === 'doughnut') {
            this.drawDoughnut(ctx, data, width, height);
        } else if (type === 'bar') {
            this.drawBar(ctx, data, width, height);
        }
    }

    drawDoughnut(ctx, data, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 3;
        const innerRadius = radius * 0.6;

        let total = data.datasets[0].data.reduce((a, b) => a + b, 0);
        let currentAngle = -Math.PI / 2;

        data.datasets[0].data.forEach((value, index) => {
            const sliceAngle = (value / total) * 2 * Math.PI;
            const isHovered = this.hoveredIndex === index;

            ctx.beginPath();
            const currentRadius = isHovered ? radius + 5 : radius; // Expand on hover
            const currentInnerRadius = isHovered ? innerRadius - 2 : innerRadius;
            
            ctx.arc(centerX, centerY, currentRadius, currentAngle, currentAngle + sliceAngle);
            ctx.arc(centerX, centerY, currentInnerRadius, currentAngle + sliceAngle, currentAngle, true);
            ctx.closePath();
            
            // Slightly brighten color on hover
            let fillColor = data.datasets[0].backgroundColor[index];
            if (isHovered) {
                fillColor = this.brightenColor(fillColor, 0.2);
            }
            
            ctx.fillStyle = fillColor;
            ctx.fill();

            // Add subtle stroke on hover
            if (isHovered) {
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            currentAngle += sliceAngle;
        });
    }

    drawBar(ctx, data, width, height) {
        const padding = 40;
        const barWidth = (width - padding * 2) / data.labels.length * 0.8;
        const maxValue = Math.max(...data.datasets[0].data);

        data.datasets[0].data.forEach((value, index) => {
            const isHovered = this.hoveredIndex === index;
            const barHeight = (value / maxValue) * (height - padding * 2);
            const x = padding + index * (width - padding * 2) / data.labels.length + barWidth * 0.1;
            const y = height - padding - barHeight;

            // Slightly brighten color on hover
            let fillColor = data.datasets[0].backgroundColor[index];
            if (isHovered) {
                fillColor = this.brightenColor(fillColor, 0.2);
            }

            ctx.fillStyle = fillColor;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Add subtle stroke on hover
            if (isHovered) {
                ctx.strokeStyle = '#fff';
                ctx.lineWidth = 2;
                ctx.strokeRect(x, y, barWidth, barHeight);
            }
        });
    }

    // Helper function to brighten colors on hover
    brightenColor(color, percent) {
        // Simple color brightening - works with hex colors
        if (color.startsWith('#')) {
            const num = parseInt(color.slice(1), 16);
            const amt = Math.round(2.55 * percent * 100);
            const R = (num >> 16) + amt;
            const G = (num >> 8 & 0x00FF) + amt;
            const B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
                (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
                (B < 255 ? B < 1 ? 0 : B : 255))
                .toString(16).slice(1);
        }
        return color; // Return original color if not hex
    }
}

// Export for use in other files (if using modules)
// export default Chart;
```

## Step 2: Include in your main HTML page

**In your main HTML file (`index.html`):**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Dashboard</title>
</head>
<body>
    <!-- Your existing HTML content -->
    <canvas id="myChart" width="400" height="400"></canvas>
    
    <!-- Include the chart script before your chart initialization -->
    <script src="js/charts/minimal-chart.js"></script>
    
    <!-- Your chart initialization code -->
    <script>
        // Example usage
        const ctx = document.getElementById('myChart').getContext('2d');
        const myChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Red', 'Blue', 'Yellow', 'Green'],
                datasets: [{
                    data: [12, 19, 3, 5],
                    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                }]
            }
        });
    </script>
</body>
</html>
```

## Alternative ways to include the script:

### Option 1: Different folder structure
```
your-project/
├── assets/
│   └── js/
│       └── minimal-chart.js
└── index.html
```
Include with: `<script src="assets/js/minimal-chart.js"></script>`

### Option 2: Using ES6 Modules (modern approach)
**In `minimal-chart.js`, add at the end:**
```javascript
export default Chart;
```

**In your HTML:**
```html
<script type="module">
    import Chart from './js/charts/minimal-chart.js';
    
    const ctx = document.getElementById('myChart').getContext('2d');
    const myChart = new Chart(ctx, {
        // your config here
    });
</script>
```

### Option 3: Multiple chart files
If you want to split functionality further:
```
js/
├── charts/
│   ├── chart-base.js
│   ├── chart-doughnut.js
│   └── chart-bar.js
└── main.js
```

## Important Notes:

1. **Script order matters**: Include the chart script before any code that uses the `Chart` class
2. **Path accuracy**: Make sure the path in the `src` attribute matches your actual file structure
3. **Server requirement**: If using ES6 modules, you'll need to serve your files through a web server (not just open the HTML file directly)
4. **Error checking**: Add error handling if the script fails to load:

```html
<script src="js/charts/minimal-chart.js" onerror="console.error('Failed to load chart script')"></script>
```

This organization keeps your code clean, maintainable, and reusable across different pages!


The issue is that your `dashboard.html` template extends `base.html`, but your navigation bar is in a template that expects to show different pages dynamically using JavaScript. You have a few options to fix this. Here are two approaches:

## Option 1: Separate Route Approach (Recommended)

Create separate Flask routes for each page and update your templates accordingly.

### 1. Update your Flask app:

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/status')
def status():
    return render_template('status.html')

@app.route('/hashtable')
def hashtable():
    return render_template('hashtable.html')

@app.route('/logs')
def logs():
    return render_template('logs.html')

if __name__ == '__main__':
    app.run(debug=True)
```

### 2. Update your `base.html` navigation:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Database Dashboard{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Navigation Bar -->
    <nav class="bg-white shadow-lg border-b-2 border-blue-500">
        <div class="max-w-7xl mx-auto px-4">
            <div class="flex justify-between items-center py-4">
                <!-- Logo -->
                <div class="flex items-center space-x-3">
                    <div class="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center shadow-md">
                        <img src="{{ url_for('static', filename='images/SB.svg') }}" alt="Badger in tupperware container">
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-gray-800">DataBadger</h1>
                        <p class="text-sm text-gray-500">SquishyBadger Status Monitoring</p>
                    </div>
                </div>

                <!-- Navigation Items -->
                <div class="flex space-x-1">
                    <a href="{{ url_for('dashboard') }}" class="nav-item px-4 py-2 rounded-lg {% if request.endpoint == 'dashboard' %}text-white bg-blue-600{% else %}text-gray-700 hover:bg-gray-100{% endif %} transition-all duration-200 font-medium shadow-md">
                        Dashboard
                    </a>
                    <a href="{{ url_for('status') }}" class="nav-item px-4 py-2 rounded-lg {% if request.endpoint == 'status' %}text-white bg-blue-600{% else %}text-gray-700 hover:bg-gray-100{% endif %} transition-all duration-200 font-medium">
                        Site Status
                    </a>
                    <a href="{{ url_for('hashtable') }}" class="nav-item px-4 py-2 rounded-lg {% if request.endpoint == 'hashtable' %}text-white bg-blue-600{% else %}text-gray-700 hover:bg-gray-100{% endif %} transition-all duration-200 font-medium">
                        Hashtable
                    </a>
                    <a href="{{ url_for('logs') }}" class="nav-item px-4 py-2 rounded-lg {% if request.endpoint == 'logs' %}text-white bg-blue-600{% else %}text-gray-700 hover:bg-gray-100{% endif %} transition-all duration-200 font-medium">
                        Logs
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <main>
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

### 3. Update your `dashboard.html`:

```html
{% extends "base.html" %}

{% block title %}Dashboard - Squishy REST API{% endblock %}

{% block content %}
<div class="max-w-7xl mx-auto px-4 py-8">
    <h2 class="text-3xl font-bold text-gray-800 mb-8">Dashboard Overview</h2>

    <!-- Key Metrics Tiles -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="tile bg-gradient-to-r from-red-500 to-red-600 text-white p-6 rounded-xl shadow-lg cursor-pointer transition-all duration-300" onclick="window.location.href='{{ url_for('status') }}'">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-red-100 text-sm font-medium">Inactive Sites</p>
                    <p class="text-3xl font-bold">23</p>
                </div>
                <div class="bg-red-400 p-3 rounded-full">
                    <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clip-rule="evenodd"></path>
                    </svg>
                </div>
            </div>
        </div>
        <!-- Add other tiles similarly -->
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Charts content here -->
    </div>
</div>
{% endblock %}
```

## Option 2: Single Page Application Approach

If you want to keep the JavaScript-based navigation, you'll need to:

### 1. Create templates for each section:

Create separate template files like `status_content.html`, `hashtable_content.html`, etc., containing just the content for each section.

### 2. Add JavaScript to handle the navigation:

```html
<!-- Add this to your base.html before closing </body> tag -->
<script>
function showPage(pageName) {
    // Hide all pages
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.style.display = 'none');
    
    // Show selected page
    const targetPage = document.getElementById(pageName);
    if (targetPage) {
        targetPage.style.display = 'block';
    }
    
    // Update navigation active state
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('text-white', 'bg-blue-600');
        item.classList.add('text-gray-700', 'hover:bg-gray-100');
    });
    
    // Set active nav item
    event.target.classList.remove('text-gray-700', 'hover:bg-gray-100');
    event.target.classList.add('text-white', 'bg-blue-600');
}

// Show dashboard by default
document.addEventListener('DOMContentLoaded', function() {
    showPage('dashboard');
});
</script>
```

**I recommend Option 1** as it's more maintainable, SEO-friendly, and follows Flask best practices. Each page will have its own URL and can be bookmarked or shared directly.