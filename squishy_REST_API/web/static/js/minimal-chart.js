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
        const innerRadius = radius * 0.3;

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
// export default Chart;