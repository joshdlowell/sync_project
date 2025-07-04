/* ==========================================================================
   TABLE OF CONTENTS
   ==========================================================================
   1. CSS VARIABLES & CONFIGURATION
   2. RESET & BASE STYLES
   3. UTILITY CLASSES
      3.1 Layout & Display
      3.2 Spacing (Margin & Padding)
      3.3 Sizing
      3.4 Flexbox & Grid
      3.5 Typography
      3.6 Colors & Backgrounds
      3.7 Borders & Shadows
      3.8 Transitions & Animations
   4. INTERACTIVE STATES
   5. COMPONENT STYLES
      5.1 Buttons
      5.2 Forms
      5.3 Tables
      5.4 Badges & Status Indicators
      5.5 Navigation
   6. PAGE-SPECIFIC STYLES
      6.1 Logs Page
      6.2 Liveness Page
      6.3 Hash Status Page
      6.4 Error Page
   7. RESPONSIVE DESIGN
   ========================================================================== */

/* ==========================================================================
   1. CSS VARIABLES & CONFIGURATION
   ========================================================================== */

:root {
    /* Colors */
    --color-primary: #3b82f6;
    --color-primary-dark: #2563eb;
    --color-secondary: #6c757d;
    --color-success: #28a745;
    --color-warning: #ffc107;
    --color-danger: #dc3545;
    --color-info: #17a2b8;

    /* Status Colors */
    --status-current: #28a745;
    --status-1-behind: #17a2b8;
    --status-warning: #ffc107;
    --status-critical: #fd7e14;
    --status-inactive: #dc3545;
    --status-unknown: #6c757d;

    /* Grays */
    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-200: #e5e7eb;
    --gray-300: #d1d5db;
    --gray-400: #9ca3af;
    --gray-500: #6b7280;
    --gray-600: #4b5563;
    --gray-700: #374151;
    --gray-800: #1f2937;
    --gray-900: #111827;

    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;

    /* Border Radius */
    --radius-sm: 0.25rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
    --radius-full: 9999px;

    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);

    /* Transitions */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 200ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ==========================================================================
   2. RESET & BASE STYLES
   ========================================================================== */

/* Reset */
*, ::before, ::after {
    box-sizing: border-box;
    border-width: 0;
    border-style: solid;
    border-color: var(--gray-200);
}

/* Base HTML & Body */
html {
    line-height: 1.5;
    -webkit-text-size-adjust: 100%;
    font-family: ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
}

body {
    margin: 0;
    line-height: inherit;
    background-color: #e0f2fe;
    min-height: 100vh;
    color: var(--gray-900);
}

/* ==========================================================================
   3. UTILITY CLASSES
   ========================================================================== */

/* 3.1 Layout & Display */
.relative { position: relative; }
.block { display: block; }
.flex { display: flex; }
.table-row { display: table-row; }
.grid { display: grid; }
.hidden { display: none; }
.overflow-hidden { overflow: hidden; }
.overflow-x-auto { overflow-x: auto; }
.whitespace-nowrap { white-space: nowrap; }

/* 3.2 Spacing - Margin */
.mx-auto { margin-left: auto; margin-right: auto; }
.mb-2 { margin-bottom: var(--spacing-sm); }
.mb-4 { margin-bottom: var(--spacing-md); }
.mb-6 { margin-bottom: var(--spacing-lg); }
.mb-8 { margin-bottom: var(--spacing-xl); }
.mt-4 { margin-top: var(--spacing-md); }

/* 3.3 Spacing - Padding */
.p-3 { padding: 0.75rem; }
.p-6 { padding: var(--spacing-lg); }
.px-2 { padding-left: var(--spacing-sm); padding-right: var(--spacing-sm); }
.px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
.px-4 { padding-left: var(--spacing-md); padding-right: var(--spacing-md); }
.px-6 { padding-left: var(--spacing-lg); padding-right: var(--spacing-lg); }
.py-1 { padding-top: var(--spacing-xs); padding-bottom: var(--spacing-xs); }
.py-2 { padding-top: var(--spacing-sm); padding-bottom: var(--spacing-sm); }
.py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.py-4 { padding-top: var(--spacing-md); padding-bottom: var(--spacing-md); }
.py-8 { padding-top: var(--spacing-xl); padding-bottom: var(--spacing-xl); }

/* 3.4 Sizing */
.h-6 { height: 1.5rem; }
.h-10 { height: 2.5rem; }
.h-12 { height: 3rem; }
.h-64 { height: 16rem; }
.min-h-screen { min-height: 100vh; }
.w-6 { width: 1.5rem; }
.w-10 { width: 2.5rem; }
.w-12 { width: 3rem; }
.w-full { width: 100%; }
.max-w-7xl { max-width: 80rem; }

/* 3.5 Flexbox & Grid */
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.flex-wrap { flex-wrap: wrap; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: var(--spacing-sm); }
.gap-4 { gap: var(--spacing-md); }
.gap-6 { gap: var(--spacing-lg); }
.gap-8 { gap: var(--spacing-xl); }

/* 3.6 Spacing Between Elements */
.space-x-1 > :not([hidden]) ~ :not([hidden]) { margin-right: var(--spacing-xs); margin-left: var(--spacing-xs); }
.space-x-3 > :not([hidden]) ~ :not([hidden]) { margin-right: 0.75rem; margin-left: 0.75rem; }
.divide-y > :not([hidden]) ~ :not([hidden]) { border-top-width: 1px; }
.divide-gray-200 > :not([hidden]) ~ :not([hidden]) { border-color: var(--gray-200); }

/* 3.7 Typography */
.text-left { text-align: left; }
.text-center { text-align: center; }
.text-xs { font-size: 0.75rem; line-height: 1rem; }
.text-sm { font-size: 0.875rem; line-height: 1.25rem; }
.text-lg { font-size: 1.125rem; line-height: 1.75rem; }
.text-xl { font-size: 1.25rem; line-height: 1.75rem; }
.text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
.uppercase { text-transform: uppercase; }
.tracking-wider { letter-spacing: 0.05em; }

/* 3.8 Colors & Backgrounds */
.bg-white { background-color: #ffffff; }
.bg-gray-50 { background-color: var(--gray-50); }
.bg-gray-100 { background-color: var(--gray-100); }
.bg-gray-300 { background-color: var(--gray-300); }
.bg-gray-400 { background-color: var(--gray-400); }
.bg-gray-500 { background-color: var(--gray-500); }
.bg-blue-400 { background-color: #60a5fa; }
.bg-blue-600 { background-color: var(--color-primary-dark); }
.bg-green-100 { background-color: #dcfce7; }
.bg-green-400 { background-color: #4ade80; }
.bg-orange-400 { background-color: #fb923c; }
.bg-red-100 { background-color: #fee2e2; }
.bg-red-400 { background-color: #f87171; }
.bg-yellow-100 { background-color: #fef3c7; }

/* Text Colors */
.text-white { color: #ffffff; }
.text-gray-500 { color: var(--gray-500); }
.text-gray-700 { color: var(--gray-700); }
.text-gray-800 { color: var(--gray-800); }
.text-gray-900 { color: var(--gray-900); }
.text-blue-100 { color: #dbeafe; }
.text-blue-600 { color: var(--color-primary-dark); }
.text-green-100 { color: #dcfce7; }
.text-green-800 { color: #166534; }
.text-orange-100 { color: #fed7aa; }
.text-red-100 { color: #fee2e2; }
.text-red-800 { color: #991b1b; }
.text-yellow-800 { color: #854d0e; }

/* 3.9 Borders & Shadows */
.rounded-full { border-radius: var(--radius-full); }
.rounded-lg { border-radius: var(--radius-md); }
.rounded-xl { border-radius: var(--radius-lg); }
.border { border-width: 1px; }
.border-b-2 { border-bottom-width: 2px; }
.border-blue-500 { border-color: var(--color-primary); }
.border-gray-300 { border-color: var(--gray-300); }
.shadow-sm { box-shadow: var(--shadow-sm); }
.shadow-md { box-shadow: var(--shadow-md); }
.shadow-lg { box-shadow: var(--shadow-lg); }

/* 3.10 Transitions & Animations */
.transition-all { transition: all var(--transition-fast); }
.transition-colors { transition: color var(--transition-fast), background-color var(--transition-fast), border-color var(--transition-fast); }
.duration-200 { transition-duration: var(--transition-normal); }
.duration-300 { transition-duration: var(--transition-slow); }
.cursor-pointer { cursor: pointer; }

/* Gradients */
.bg-gradient-to-br { background-image: linear-gradient(to bottom right, var(--tw-gradient-stops)); }
.bg-gradient-to-r { background-image: linear-gradient(to right, var(--tw-gradient-stops)); }
.from-amber-400 { --tw-gradient-from: #fbbf24; --tw-gradient-stops: var(--tw-gradient-from), transparent; }
.from-blue-500 { --tw-gradient-from: var(--color-primary); --tw-gradient-stops: var(--tw-gradient-from), transparent; }
.from-green-500 { --tw-gradient-from: #22c55e; --tw-gradient-stops: var(--tw-gradient-from), transparent; }
.from-orange-500 { --tw-gradient-from: #f97316; --tw-gradient-stops: var(--tw-gradient-from), transparent; }
.from-red-500 { --tw-gradient-from: #ef4444; --tw-gradient-stops: var(--tw-gradient-from), transparent; }
.to-blue-600 { --tw-gradient-to: var(--color-primary-dark); }
.to-green-600 { --tw-gradient-to: #16a34a; }
.to-orange-500 { --tw-gradient-to: #f97316; }
.to-orange-600 { --tw-gradient-to: #ea580c; }
.to-red-600 { --tw-gradient-to: #dc2626; }

/* ==========================================================================
   4. INTERACTIVE STATES
   ========================================================================== */

/* Hover States */
.hover\:bg-blue-700:hover { background-color: #1d4ed8; }
.hover\:bg-gray-100:hover { background-color: var(--gray-100); }
.hover\:bg-gray-600:hover { background-color: var(--gray-600); }
.hover\:text-blue-900:hover { color: #1e3a8a; }

/* Focus States */
.focus\:border-blue-500:focus { border-color: var(--color-primary); }
.focus\:ring-2:focus { box-shadow: 0 0 0 2px rgb(59 130 246 / 0.5); }

/* ==========================================================================
   5. COMPONENT STYLES
   ========================================================================== */

/* 5.1 Buttons */
.btn {
    padding: var(--spacing-sm) var(--spacing-md);
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    font-size: 0.875rem;
    font-weight: 500;
    transition: all var(--transition-normal);
    line-height: 1.25;
}

.btn-primary {
    background-color: var(--color-primary);
    color: white;
}

.btn-primary:hover {
    background-color: var(--color-primary-dark);
    transform: translateY(-1px);
}

.btn-secondary {
    background-color: var(--color-secondary);
    color: white;
}

.btn-secondary:hover {
    background-color: #545b62;
}

/* 5.2 Forms */
.filter-form {
    background: var(--gray-50);
    padding: var(--spacing-xl);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-xl);
    box-shadow: var(--shadow-sm);
}

.filters {
    display: flex;
    gap: var(--spacing-xl);
    align-items: end;
    flex-wrap: wrap;
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

.filter-group label {
    font-weight: 600;
    color: var(--gray-700);
    font-size: 0.875rem;
}

.filter-group select {
    padding: var(--spacing-sm) 0.75rem;
    border: 1px solid var(--gray-300);
    border-radius: var(--radius-sm);
    background: white;
    min-width: 150px;
    font-size: 0.875rem;
    transition: border-color var(--transition-fast);
}

.filter-group select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 2px rgb(59 130 246 / 0.1);
}

.filter-actions {
    display: flex;
    gap: var(--spacing-md);
}

/* 5.3 Tables */
.table-container {
    background: white;
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--gray-200);
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

.data-table th {
    background: var(--gray-50);
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
    color: var(--gray-700);
    border-bottom: 2px solid var(--gray-200);
    font-size: 0.875rem;
}

.data-table td {
    padding: 0.75rem;
    border-bottom: 1px solid var(--gray-200);
    vertical-align: top;
}

.data-table tr:hover {
    background-color: var(--gray-50);
}

.data-table tr:last-child td {
    border-bottom: none;
}

/* 5.4 Badges & Status Indicators */
.badge {
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.025em;
    display: inline-block;
}

/* Log Level Badges */
.log-level-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.level-error { background: var(--color-danger); color: white; }
.level-warning { background: var(--color-warning); color: var(--gray-900); }
.level-info { background: var(--color-info); color: white; }
.level-debug { background: var(--color-secondary); color: white; }
.level-critical { background: #721c24; color: white; }

/* Status Badges */
.status-badge {
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
}

.status-live-current { background-color: var(--status-current); color: white; }
.status-live-1-behind { background-color: var(--status-warning); color: var(--gray-900); }
.status-live-l24-behind { background-color: var(--status-critical); color: white; }
.status-live-inactive { background-color: var(--status-inactive); color: white; }
.status-marked-inactive { background-color: var(--status-unknown); color: white; }

/* Sync Status Badges */
.sync-badge {
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
}

.sync-current { background-color: var(--status-current); color: white; }
.sync-1-behind { background-color: var(--status-1-behind); color: white; }
.sync-l24-behind { background-color: var(--status-warning); color: var(--gray-900); }
.sync-g24-behind { background-color: var(--status-critical); color: white; }
.sync-unknown { background-color: var(--status-unknown); color: white; }

/* 5.5 Navigation */
.nav-item:hover {
    transform: translateY(-2px);
    transition: transform var(--transition-fast);
}

/* ==========================================================================
   6. PAGE-SPECIFIC STYLES
   ========================================================================== */

/* 6.1 Logs Page */
.logs-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--spacing-xl);
}

.results-summary {
    margin-bottom: var(--spacing-md);
    color: var(--gray-700);
    font-size: 0.875rem;
}

.logs-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

.logs-table th {
    background: var(--gray-50);
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
    color: var(--gray-700);
    border-bottom: 2px solid var(--gray-200);
}

.logs-table td {
    padding: 0.75rem;
    border-bottom: 1px solid var(--gray-200);
    vertical-align: top;
}

.log-row:hover {
    background-color: var(--gray-50);
}

/* Log Table Column Specific Styles */
.site-cell {
    font-weight: 500;
    min-width: 100px;
}

.level-cell {
    min-width: 80px;
}

.timestamp-cell {
    font-family: monospace;
    min-width: 170px;
    color: var(--gray-600);
}

.message-cell {
    max-width: 400px;
}

.message-wrapper {
    position: relative;
    cursor: help;
    word-wrap: break-word;
}

.detail-indicator {
    color: var(--color-primary);
    font-weight: 600;
    margin-left: var(--spacing-sm);
}

.message-wrapper[title]:hover {
    background-color: #e3f2fd;
    border-radius: var(--radius-sm);
    padding: 2px 4px;
    margin: -2px -4px;
}

.no-results {
    text-align: center;
    padding: var(--spacing-2xl);
    color: var(--gray-600);
    background: var(--gray-50);
    border-radius: var(--radius-md);
}

/* 6.2 Liveness Page */
.liveness-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--spacing-xl);
}

.liveness-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

.liveness-table th {
    background: var(--gray-50);
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
    color: var(--gray-700);
    border-bottom: 2px solid var(--gray-200);
}

.liveness-table td {
    padding: 0.75rem;
    border-bottom: 1px solid var(--gray-200);
    vertical-align: top;
}

.liveness-table tr:hover {
    background-color: var(--gray-50);
}

/* 6.3 Hash Status Page */
.hash-status-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: var(--spacing-xl);
}

.hash-status-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    table-layout: fixed;
}

.hash-status-table th {
    background: var(--gray-50);
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
    color: var(--gray-700);
    border-bottom: 2px solid var(--gray-200);
    position: sticky;
    top: 0;
    z-index: 10;
}

.hash-status-table td {
    padding: 0.75rem;
    border-bottom: 1px solid var(--gray-200);
    vertical-align: top;
    word-wrap: break-word;
}

.hash-status-table tr:hover {
    background-color: var(--gray-50);
}

.hash-status-table tr:last-child td {
    border-bottom: none;
}

/* Hash Status Column Widths */
.hash-status-table .site-column {
    width: 15%;
    min-width: 120px;
}

.hash-status-table .sync-column {
    width: 12%;
    min-width: 100px;
}

.hash-status-table .hash-column {
    width: 25%;
    min-width: 200px;
}

.hash-status-table .details-column {
    width: 20%;
    min-width: 150px;
}

.hash-status-table .timestamp-column {
    width: 15%;
    min-width: 140px;
}

.hash-status-table .actions-column {
    width: 13%;
    min-width: 100px;
}

.hash-value {
    font-family: monospace;
    font-size: 0.8rem;
    cursor: pointer;
    word-break: break-all;
    line-height: 1.4;
    color: var(--gray-700);
}

.hash-value:hover {
    background-color: var(--gray-100);
    border-radius: var(--radius-sm);
    padding: 2px 4px;
    margin: -2px -4px;
}

.no-hash {
    color: var(--gray-500);
    font-style: italic;
    font-size: 0.875rem;
}

.hash-details {
    font-size: 0.875rem;
    color: var(--gray-600);
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
}

.hash-timestamp {
    font-family: monospace;
    font-size: 0.8rem;
    color: var(--gray-600);
    white-space: nowrap;
}

/* 6.4 Error Page */
.error {
    text-align: center;
    padding: var(--spacing-xl);
    max-width: 600px;
    margin: 0 auto;
}

.error-illustration {
    margin: var(--spacing-xl) 0;
    animation: wobble 2s infinite;
}

.error h1 {
    color: var(--color-danger);
    font-size: 2rem;
    margin: var(--spacing-md) 0;
}

.error-message {
    font-size: 1.125rem;
    color: var(--gray-500);
    margin: var(--spacing-md) 0;
    font-style: italic;
}

.error-details {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    margin: var(--spacing-lg) 0;
    color: var(--color-danger);
    font-family: monospace;
    font-size: 0.875rem;
}

.error-actions {
    margin-top: var(--spacing-xl);
}

.error-hint {
    margin-top: var(--spacing-md);
    font-size: 0.875rem;
    color: var(--gray-400);
    font-style: italic;
}

/* ==========================================================================
   7. ANIMATIONS
   ========================================================================== */

.chart-container {
    transition: all var(--transition-slow);
}

.chart-container:hover {
    transform: scale(1.02);
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.tile:hover {
    transform: translateY(-4px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.15);
}

.filter-tag {
    animation: fadeIn var(--transition-slow);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes wobble {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-2deg); }
    75% { transform: rotate(2deg); }
}

/* ==========================================================================
   8. RESPONSIVE DESIGN
   ========================================================================== */

/* Mobile First Approach */
@media (max-width: 768px) {
    .filters {
        flex-direction: column;
        align-items: stretch;
    }

    .filter-group select {
        min-width: auto;
    }

    .table-container {
        overflow-x: auto;
    }

    .data-table {
        min-width: 600px;
    }

    .hash-status-table {
        min-width: 800px;
    }

    .hash-status-container {
        padding: var(--spacing-md);
    }
}

/* Tablet */
@media (min-width: 768px) {
    .md\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .md\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}

/* Desktop */
@media (min-width: 1024px) {
    .lg\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .lg\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }

    .hash-status-table {
        table-layout: auto;
    }
}

/* Large Desktop */
@media (min-width: 1280px) {
    .hash-status-container {
        max-width: 1600px;
    }
}

/* TIME STUFF on hash detail */
.time-display {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.utc-time {
    font-weight: bold;
}

.local-time {
    font-size: 0.9em;
    color: #6c757d;
}

.clock-container {
    background-color: #f8f9fa;
    padding: 10px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    border-left: 4px solid #007bff;
}

.clock-section {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
}

.clock-label {
    font-weight: bold;
    color: #495057;
    font-size: 0.9em;
}

.clock-display {
    font-family: monospace;
    font-size: 1em;
    font-weight: bold;
    color: #212529;
    background-color: #ffffff;
    padding: 5px 10px;
    border-radius: 4px;
    border: 1px solid #dee2e6;
    min-width: 160px;
    text-align: center;
}

.clock-separator {
    color: #6c757d;
    font-weight: bold;
}

@media (max-width: 768px) {
    .clock-section {
        flex-wrap: wrap;
        gap: 10px;
    }
}