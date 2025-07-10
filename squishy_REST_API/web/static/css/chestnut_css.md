Looking at that Chestnut Street Lofts page, I can see it has a clean, modern design with a light color scheme, subtle shadows, and well-organized form elements. Here's a CSS file that captures that aesthetic while maintaining compatibility with your Flask templates:

```css
/* Modern Clean Theme */

/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    min-height: 100vh;
}

/* Utility Classes */
.max-w-7xl {
    max-width: 80rem;
}

.mx-auto {
    margin-left: auto;
    margin-right: auto;
}

.px-4 {
    padding-left: 1rem;
    padding-right: 1rem;
}

.py-8 {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.py-4 {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

.py-3 {
    padding-top: 0.75rem;
    padding-bottom: 0.75rem;
}

.py-2 {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}

.px-3 {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
}

.px-4 {
    padding-left: 1rem;
    padding-right: 1rem;
}

.px-6 {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}

.p-4 {
    padding: 1rem;
}

.p-6 {
    padding: 1.5rem;
}

.mb-8 {
    margin-bottom: 2rem;
}

.mb-4 {
    margin-bottom: 1rem;
}

.mt-8 {
    margin-top: 2rem;
}

.space-x-3 > * + * {
    margin-left: 0.75rem;
}

.space-x-1 > * + * {
    margin-left: 0.25rem;
}

.min-h-screen {
    min-height: 100vh;
}

.bg-gray-300 {
    background-color: #d1d5db;
}

.bg-gray-200 {
    background-color: #e5e7eb;
}

.bg-gray-400 {
    background-color: #9ca3af;
}

.bg-white {
    background-color: white;
}

.text-gray-800 {
    color: #1f2937;
}

.text-gray-700 {
    color: #374151;
}

.text-gray-600 {
    color: #4b5563;
}

.text-gray-400 {
    color: #9ca3af;
}

.text-white {
    color: white;
}

.text-3xl {
    font-size: 1.875rem;
}

.text-xl {
    font-size: 1.25rem;
}

.text-sm {
    font-size: 0.875rem;
}

.text-2xl {
    font-size: 1.5rem;
}

.font-bold {
    font-weight: 700;
}

.font-semibold {
    font-weight: 600;
}

.font-medium {
    font-weight: 500;
}

.font-mono {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
}

.flex {
    display: flex;
}

.items-center {
    align-items: center;
}

.justify-between {
    justify-content: space-between;
}

.w-12 {
    width: 3rem;
}

.h-12 {
    height: 3rem;
}

.w-6 {
    width: 1.5rem;
}

.h-6 {
    height: 1.5rem;
}

.w-full {
    width: 100%;
}

.max-w-md {
    max-width: 28rem;
}

.flex-1 {
    flex: 1 1 0%;
}

.whitespace-nowrap {
    white-space: nowrap;
}

.text-center {
    text-align: center;
}

.cursor-pointer {
    cursor: pointer;
}

.relative {
    position: relative;
}

.h-64 {
    height: 16rem;
}

.gap-6 {
    gap: 1.5rem;
}

.gap-8 {
    gap: 2rem;
}

.gap-4 {
    gap: 1rem;
}

.rounded-lg {
    border-radius: 0.5rem;
}

.rounded-md {
    border-radius: 0.375rem;
}

.rounded-xl {
    border-radius: 0.75rem;
}

.rounded-full {
    border-radius: 9999px;
}

.border {
    border-width: 1px;
}

.border-b {
    border-bottom-width: 1px;
}

.border-b-2 {
    border-bottom-width: 2px;
}

.border-gray-300 {
    border-color: #d1d5db;
}

.border-blue-500 {
    border-color: #3b82f6;
}

.focus\:outline-none:focus {
    outline: 2px solid transparent;
    outline-offset: 2px;
}

.focus\:ring-2:focus {
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.focus\:ring-blue-500:focus {
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.focus\:border-blue-500:focus {
    border-color: #3b82f6;
}

.focus\:ring-offset-2:focus {
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.5);
}

.transition-colors {
    transition-property: color, background-color, border-color, text-decoration-color, fill, stroke;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 150ms;
}

.transition-all {
    transition-property: all;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 150ms;
}

.duration-200 {
    transition-duration: 200ms;
}

.duration-300 {
    transition-duration: 300ms;
}

/* Grid System */
.grid {
    display: grid;
}

.grid-cols-1 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
}

.grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}

.grid-cols-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
}

.grid-cols-5 {
    grid-template-columns: repeat(5, minmax(0, 1fr));
}

@media (min-width: 768px) {
    .md\:grid-cols-2 {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (min-width: 1024px) {
    .lg\:grid-cols-4 {
        grid-template-columns: repeat(4, minmax(0, 1fr));
    }
    
    .lg\:grid-cols-5 {
        grid-template-columns: repeat(5, minmax(0, 1fr));
    }
    
    .lg\:grid-cols-2 {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

/* Navigation Styles */
nav {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.nav-item {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    backdrop-filter: blur(10px);
}

.nav-item:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
}

/* Form Styles */
input[type="text"] {
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
}

input[type="text"]:focus {
    border-color: #4299e1;
    box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: all 0.2s ease;
}

button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Tile Styles */
.tile {
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.tile:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
}

/* Gradient Backgrounds */
.bg-gradient-to-r {
    background-image: linear-gradient(to right, var(--tw-gradient-stops));
}

.from-red-500 {
    --tw-gradient-from: #ef4444;
    --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(239, 68, 68, 0));
}

.to-red-600 {
    --tw-gradient-to: #dc2626;
}

.from-orange-500 {
    --tw-gradient-from: #f97316;
    --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(249, 115, 22, 0));
}

.to-orange-600 {
    --tw-gradient-to: #ea580c;
}

.from-green-500 {
    --tw-gradient-from: #10b981;
    --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(16, 185, 129, 0));
}

.to-green-600 {
    --tw-gradient-to: #059669;
}

.from-blue-500 {
    --tw-gradient-from: #3b82f6;
    --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(59, 130, 246, 0));
}

.to-blue-600 {
    --tw-gradient-to: #2563eb;
}

.from-amber-400 {
    --tw-gradient-from: #fbbf24;
    --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(251, 191, 36, 0));
}

.to-orange-500 {
    --tw-gradient-to: #f97316;
}

.bg-gradient-to-br {
    background-image: linear-gradient(to bottom right, var(--tw-gradient-stops));
}

/* Color classes */
.bg-red-400 {
    background-color: #f87171;
}

.bg-orange-400 {
    background-color: #fb923c;
}

.bg-green-400 {
    background-color: #4ade80;
}

.bg-blue-400 {
    background-color: #60a5fa;
}

.bg-blue-600 {
    background-color: #2563eb;
}

.text-red-100 {
    color: #fee2e2;
}

.text-orange-100 {
    color: #ffedd5;
}

.text-green-100 {
    color: #dcfce7;
}

.text-blue-100 {
    color: #dbeafe;
}

.text-green-600 {
    color: #16a34a;
}

.text-yellow-600 {
    color: #ca8a04;
}

.text-orange-600 {
    color: #ea580c;
}

.text-red-600 {
    color: #dc2626;
}

.hover\:bg-blue-400:hover {
    background-color: #60a5fa;
}

.hover\:bg-blue-700:hover {
    background-color: #1d4ed8;
}

/* Shadow utilities */
.shadow-sm {
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.shadow {
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

.shadow-md {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.shadow-lg {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* Chart Container */
.chart-container {
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.chart-container:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
}

/* Hashtable Detail Styles */
.hashtable-detail-container {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    margin: 20px auto;
    max-width: 1200px;
    padding: 30px;
}

.breadcrumb-nav h1 {
    margin: 0 0 25px 0;
    font-size: 1.5em;
    color: #2d3748;
    font-weight: 600;
}

.breadcrumb-link {
    color: #4299e1;
    text-decoration: none;
    padding: 4px 8px;
    border-radius: 6px;
    transition: all 0.2s ease;
    background: rgba(66, 153, 225, 0.1);
}

.breadcrumb-link:hover {
    background: rgba(66, 153, 225, 0.2);
    transform: translateY(-1px);
}

.breadcrumb-separator {
    margin: 0 8px;
    color: #718096;
}

.record-metadata {
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 25px;
    margin-bottom: 30px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.metadata-section h2 {
    margin-top: 0;
    color: #2d3748;
    font-size: 1.3em;
    font-weight: 600;
    margin-bottom: 20px;
}

.metadata-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
}

.metadata-item {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.metadata-item label {
    font-weight: 600;
    color: #4a5568;
    margin-bottom: 8px;
    display: block;
}

.hash-value {
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
    word-break: break-all;
    padding: 8px 12px;
    background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
    border-radius: 6px;
    border: 1px solid #cbd5e0;
}

.timestamp {
    font-size: 0.95em;
    color: #4a5568;
}

.time-ago {
    color: #718096;
    font-style: italic;
    font-size: 0.9em;
}

.contents-section {
    margin-top: 30px;
}

.content-type-section {
    margin-bottom: 35px;
}

.content-type-section h2 {
    color: #2d3748;
    font-size: 1.3em;
    font-weight: 600;
    border-bottom: 2px solid #4299e1;
    padding-bottom: 12px;
    margin-bottom: 20px;
}

.content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
}

.content-item {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
}

.content-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.content-link {
    display: flex;
    align-items: center;
    padding: 15px;
    text-decoration: none;
    color: #4a5568;
    font-weight: 500;
}

.content-icon {
    margin-right: 12px;
    font-size: 1.3em;
}

.content-name {
    word-break: break-word;
}

.directory-item:hover {
    background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
    border-color: #4299e1;
}

.file-item:hover {
    background: linear-gradient(135deg, #f0fff4 0%, #c6f6d5 100%);
    border-color: #48bb78;
}

.link-item:hover {
    background: linear-gradient(135deg, #fffaf0 0%, #fbd38d 100%);
    border-color: #ed8936;
}

.no-contents, .no-results {
    text-align: center;
    padding: 50px;
    color: #718096;
    font-style: italic;
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .hashtable-detail-container {
        margin: 10px;
        padding: 20px;
    }
    
    .metadata-grid {
        grid-template-columns: 1fr;
    }
    
    .content-grid {
        grid-template-columns: 1fr;
    }
    
    .breadcrumb-nav h1 {
        font-size: 1.2em;
        word-break: break-word;
    }
    
    .grid-cols-1 {
        grid-template-columns: 1fr;
    }
    
    .md\:grid-cols-2 {
        grid-template-columns: 1fr;
    }
    
    .lg\:grid-cols-4 {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .lg\:grid-cols-5 {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 480px) {
    .lg\:grid-cols-4 {
        grid-template-columns: 1fr;
    }
    
    .lg\:grid-cols-5 {
        grid-template-columns: 1fr;
    }
    
    .tile {
        margin-bottom: 15px;
    }
}

/* Error Page Styles */
.error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    min-height: 60vh;
    padding: 2rem;
    max-width: 600px;
    margin: 0 auto;
}

.error-illustration {
    margin-bottom: 2rem;
    animation: wobble 2s infinite;
}

.error-illustration img {
    max-width: 200px;
    height: auto;
}

.error h1 {
    font-size: 2.5rem;
    font-weight: 700;
    color: #2d3748;
    margin-bottom: 1rem;
}

.error-message {
    font-size: 1.25rem;
    color: #4a5568;
    margin-bottom: 1rem;
}

.error-details {
    font-size: 1rem;
    color: #718096;
    margin-bottom: 2rem;
    padding: 1rem;
    background: #f7fafc;
    border-radius: 0.5rem;
    border: 1px solid #e2e8f0;
}

.error-actions {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.error-hint {
    font-size: 0.875rem;
    color: #718096;
    font-style: italic;
    margin-top: 0.5rem;
}

@media (max-width: 768px) {
    .error h1 {
        font-size: 2rem;
    }

    .error-message {
        font-size: 1.125rem;
    }

    .error {
        padding: 1rem;
    }
}

@keyframes wobble {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(-2deg); }
    75% { transform: rotate(2deg); }
}

```

This CSS creates a clean, modern look inspired by the Chestnut Street Lofts page with:

1. **Soft gradients** instead of flat colors for backgrounds
2. **Subtle shadows and depth** with hover effects
3. **Clean typography** with better hierarchy
4. **Smooth transitions** for interactive elements
5. **Better form styling** with modern inputs and buttons
6. **Enhanced cards/tiles** with hover animations
7. **Improved color palette** with softer, more professional tones
8. **Better spacing and layout** for readability

The design maintains all your existing functionality while giving it a more polished, professional appearance similar to the reference site. All styles are defined locally, so it will work on your closed network.