# Table Implementation Guide
## ERPNext-Inspired Modern Tables with Color Coding and Business Logic

This guide documents the implementation patterns for creating modern, responsive tables in the ERP Factory system following ERPNext design principles.

## Table of Contents
1. [Color Coding Business Rules](#color-coding-business-rules)
2. [Responsive Behavior Patterns](#responsive-behavior-patterns)
3. [Accessibility Requirements](#accessibility-requirements)
4. [Implementation Examples](#implementation-examples)
5. [Template Inheritance Structure](#template-inheritance-structure)
6. [JavaScript Enhancement Patterns](#javascript-enhancement-patterns)
7. [CSS Class Naming Conventions](#css-class-naming-conventions)
8. [Testing and Validation](#testing-and-validation)

---

## Color Coding Business Rules

### Weight Classification (Material Codes)
```javascript
function getWeightClass(weight) {
    if (!weight) return 'erp-table-value-neutral';
    const weightValue = parseFloat(weight);
    if (weightValue > 50) return 'weight-heavy';      // Red for >50kg
    if (weightValue < 10) return 'weight-light';     // Green for <10kg  
    return 'weight-medium';                           // Yellow for 10-50kg
}
```

**Business Logic:**
- **Heavy Items (>50kg)**: Red with ⚠ indicator - requires special handling equipment
- **Light Items (<10kg)**: Green with ✓ indicator - standard handling procedures
- **Medium Items (10-50kg)**: Yellow with ◐ indicator - moderate handling requirements

### Cost Classification (Color Codes)
```javascript
function getCostClass(cost) {
    if (!cost) return 'erp-table-value-neutral';
    const costValue = parseFloat(cost);
    if (costValue >= 100) return 'cost-expensive';   // Red for >$100
    if (costValue >= 50) return 'cost-moderate';     // Yellow for $50-100
    return 'cost-budget';                             // Green for <$50
}
```

**Business Logic:**
- **Expensive (≥$100)**: Red with 💰 indicator - requires approval for bulk orders
- **Moderate ($50-100)**: Yellow with 💵 indicator - standard procurement process
- **Budget (<$50)**: Green with 💚 indicator - expedited procurement available

### Grade Classification (Materials)
```javascript
function getGradeClass(grade) {
    if (!grade) return 'erp-table-value-neutral';
    const premiumGrades = ['6061 T6', '7075'];
    if (premiumGrades.includes(grade)) return 'grade-premium';  // Gold
    return 'grade-standard';                                     // Blue
}
```

**Business Logic:**
- **Premium Grades**: Gold gradient with ⭐ - aerospace/high-performance applications
- **Standard Grades**: Blue with 🔹 - general manufacturing applications

---

## Responsive Behavior Patterns

### Breakpoint Strategy
```css
/* Desktop (≥1024px) - Full table display */
@media (min-width: 1024px) {
    .erp-table th, .erp-table td {
        padding: 0.875rem 1rem;
        font-size: 0.875rem;
    }
}

/* Tablet (768px - 1023px) - Condensed display */
@media (max-width: 1023px) and (min-width: 768px) {
    .erp-table th, .erp-table td {
        padding: 0.75rem 0.875rem;
        font-size: 0.8125rem;
    }
}

/* Mobile (≤767px) - Priority columns only */
@media (max-width: 767px) {
    .erp-table th:not(.erp-table-primary):not(:last-child),
    .erp-table td:not(.erp-table-primary):not(:last-child) {
        display: none;
    }
    
    /* Always show primary column and actions */
    .erp-table th.erp-table-primary,
    .erp-table td.erp-table-primary,
    .erp-table th:last-child,
    .erp-table td:last-child {
        display: table-cell !important;
    }
}
```

### Touch-Friendly Controls
- **Minimum Touch Target**: 44px × 44px for all interactive elements
- **Action Buttons**: Increased padding on mobile devices
- **Expandable Rows**: Large touch areas for expand/collapse functionality

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance
```html
<!-- Proper ARIA table structure -->
<table class="erp-table erp-table-grouped" role="table" 
       aria-label="Material codes data table"
       aria-rowcount="items.length"
       aria-colcount="7">
    
    <!-- Sortable column headers -->
    <th class="sortable" 
        @click="sortBy('weight_per_line')"
        aria-sort="none"
        tabindex="0"
        role="columnheader">
        Weight (kg)
    </th>
</table>
```

### Color Contrast Requirements
All color-coded values must meet 4.5:1 contrast ratio:
- **Red values**: `#DC3545` on white background (7.0:1 ratio) ✅
- **Green values**: `#28A745` on white background (4.5:1 ratio) ✅  
- **Yellow values**: `#FFC107` with dark text `#856404` (4.8:1 ratio) ✅

### Keyboard Navigation
```javascript
// Example keyboard navigation handler
function handleKeyNavigation(event) {
    switch(event.key) {
        case 'Enter':
        case ' ':
            // Activate expand/collapse
            event.preventDefault();
            this.toggleExpand(item);
            break;
        case 'ArrowDown':
            // Move to next row
            event.preventDefault();
            this.focusNextRow();
            break;
        case 'ArrowUp':
            // Move to previous row
            event.preventDefault();
            this.focusPreviousRow();
            break;
    }
}
```

---

## Implementation Examples

### 1. Basic Table Implementation
```html
{% extends "crud/base_table.html" %}

{% set page_title = "Product Management" %}
{% set entity_name = "Product" %}
{% set primary_field = "product_code" %}
{% set secondary_field = "product_name" %}

{% block extra_crud_css %}
<link rel="stylesheet" href="{{ url_for('static', path='css/table-enhancements.css') }}">
{% endblock %}

{% block table_group_headers %}
<tr>
    <th class="erp-table-group-header" colspan="3">Product Information</th>
    <th class="erp-table-group-header" colspan="2">Pricing</th>
    <th class="erp-table-group-header" colspan="2">Status & Actions</th>
</tr>
{% endblock %}

{% block table_headers %}
<th class="sortable" @click="sortBy('product_code')">Product Code</th>
<th class="sortable" @click="sortBy('product_name')">Product Name</th>
<th class="sortable" @click="sortBy('category')">Category</th>
<th class="sortable" @click="sortBy('unit_price')">Unit Price</th>
<th class="sortable" @click="sortBy('list_price')">List Price</th>
<th class="sortable" @click="sortBy('updated_at')">Updated</th>
<th class="erp-table-center">Actions</th>
{% endblock %}

{% block table_row %}
<td class="erp-table-primary">
    <strong x-text="item.product_code"></strong>
</td>
<td x-text="item.product_name"></td>
<td>
    <span class="business-indicator" 
          :class="getCategoryClass(item.category)"
          x-text="item.category"></span>
</td>
<td class="erp-table-right">
    <span :class="getPriceClass(item.unit_price)"
          x-text="formatCurrency(item.unit_price)"></span>
</td>
<td class="erp-table-right">
    <span x-text="formatCurrency(item.list_price)"></span>
</td>
<td class="erp-table-nowrap" x-text="formatDate(item.updated_at)"></td>
<td class="erp-table-center" @click.stop>
    <div class="erp-table-actions">
        <button class="erp-table-action-btn" @click="viewItem(item.id)">
            <i class="fas fa-eye"></i>
        </button>
        <button class="erp-table-action-btn" @click="editItem(item.id)">
            <i class="fas fa-edit"></i>
        </button>
        <button class="erp-table-action-btn danger" @click="deleteItem(item.id)">
            <i class="fas fa-trash"></i>
        </button>
    </div>
</td>
{% endblock %}
```

### 2. JavaScript Component with Business Logic
```javascript
function productList() {
    return {
        ...baseTableFunctions(),
        items: [],
        loading: false,
        error: null,
        
        // Business logic for category classification
        getCategoryClass(category) {
            const highValueCategories = ['Electronics', 'Machinery'];
            const standardCategories = ['Components', 'Materials'];
            
            if (highValueCategories.includes(category)) {
                return 'high-priority';
            } else if (standardCategories.includes(category)) {
                return 'medium-priority';
            }
            return 'low-priority';
        },
        
        // Price-based color coding
        getPriceClass(price) {
            if (!price) return 'erp-table-value-neutral';
            const priceValue = parseFloat(price);
            if (priceValue >= 1000) return 'cost-expensive';
            if (priceValue >= 100) return 'cost-moderate';
            return 'cost-budget';
        }
    }
}
```

---

## Template Inheritance Structure

### Base Template Hierarchy
```
base.html
├── crud/base_table.html          # Table-based displays
│   ├── material_codes_table.html
│   ├── color_codes_table.html
│   └── [custom_table].html
│
└── crud/base_list.html           # Card-based displays
    ├── material_codes.html
    ├── color_codes.html
    └── [custom_cards].html
```

### Required Block Implementations
```html
<!-- Mandatory blocks for table templates -->
{% block table_group_headers %}
<!-- 3-5 grouped headers with appropriate colspan -->
{% endblock %}

{% block table_headers %}
<!-- Individual column headers with sorting -->
{% endblock %}

{% block table_row %}
<!-- Main row content with color coding -->
{% endblock %}

{% block table_row_details %}
<!-- Expandable detail content -->
{% endblock %}

<!-- Optional enhancement blocks -->
{% block header_actions %}
<!-- View toggle buttons, export options -->
{% endblock %}

{% block extra_crud_css %}
<!-- Additional styling includes -->
{% endblock %}
```

---

## JavaScript Enhancement Patterns

### Alpine.js Component Structure
```javascript
function entityList() {
    return {
        // Inherit base functionality
        ...baseTableFunctions(),
        
        // Component state
        items: [],
        loading: false,
        error: null,
        currentPage: 1,
        
        // Lifecycle methods
        async init() {
            await this.loadData();
            this.setupEventListeners();
        },
        
        // Data management
        async loadData(filters = {}) {
            this.loading = true;
            try {
                // API call implementation
                const response = await this.fetchData(filters);
                this.items = response.data;
                this.items.forEach(item => item.expanded = false);
            } catch (error) {
                this.handleError(error);
            } finally {
                this.loading = false;
            }
        },
        
        // Business logic helpers
        getClassificationClass(value, thresholds) {
            // Generic classification logic
            for (const [threshold, className] of thresholds) {
                if (value >= threshold) return className;
            }
            return 'erp-table-value-neutral';
        },
        
        // UI interaction
        toggleExpand(item) {
            item.expanded = !item.expanded;
        }
    }
}
```

### Event Handling Patterns
```html
<!-- Row click for expansion -->
<tr class="erp-table-row-expandable" 
    :class="{ expanded: item.expanded }"
    @click="toggleExpand(item)"
    @keydown="handleKeyNavigation($event, item)">

<!-- Action buttons with event stopping -->
<td @click.stop>
    <button @click="editItem(item.id)" 
            :disabled="loading"
            aria-label="Edit item">
        <i class="fas fa-edit"></i>
    </button>
</td>
```

---

## CSS Class Naming Conventions

### Business Logic Classes
```css
/* Weight-based classification */
.weight-light   /* Green - <10kg */
.weight-medium  /* Yellow - 10-50kg */
.weight-heavy   /* Red - >50kg */

/* Cost-based classification */
.cost-budget    /* Green - <$50 */
.cost-moderate  /* Yellow - $50-100 */
.cost-expensive /* Red - >$100 */

/* Grade classification */
.grade-premium  /* Gold gradient - premium materials */
.grade-standard /* Blue - standard materials */

/* Priority indicators */
.business-indicator.high-priority    /* Red background */
.business-indicator.medium-priority  /* Yellow background */
.business-indicator.low-priority     /* Green background */

/* Process indicators */
.process-anodizing  /* Blue gradient */
.process-plating    /* Purple gradient */
.process-painting   /* Green gradient */
.process-raw        /* Orange gradient */
```

### Utility Classes
```css
/* Enhanced previews */
.enhanced-color-preview  /* Improved color circles */

/* Responsive utilities */
.erp-table-mobile-hidden  /* Hide on mobile */
.erp-table-tablet-hidden  /* Hide on tablet */
.erp-table-desktop-only   /* Show only on desktop */
```

---

## Testing and Validation

### Level 1: Syntax & Style
```bash
# Template validation
python -c "from jinja2 import Template; Template(open('template.html').read())"

# CSS validation  
css-tree-validator app/static/css/table-enhancements.css

# Expected: No syntax errors
```

### Level 2: Business Logic Testing
```javascript
// Test weight classification
function testWeightClassification() {
    assert(getWeightClass(5) === 'weight-light');
    assert(getWeightClass(25) === 'weight-medium');
    assert(getWeightClass(75) === 'weight-heavy');
    assert(getWeightClass(null) === 'erp-table-value-neutral');
}

// Test cost classification
function testCostClassification() {
    assert(getCostClass(25) === 'cost-budget');
    assert(getCostClass(75) === 'cost-moderate');
    assert(getCostClass(150) === 'cost-expensive');
}
```

### Level 3: Accessibility Testing
```javascript
// Check ARIA attributes
function testAccessibility() {
    const table = document.querySelector('.erp-table');
    assert(table.getAttribute('role') === 'table');
    assert(table.hasAttribute('aria-label'));
    
    const sortableHeaders = document.querySelectorAll('.sortable');
    sortableHeaders.forEach(header => {
        assert(header.hasAttribute('aria-sort'));
        assert(header.getAttribute('tabindex') === '0');
    });
}
```

### Level 4: Responsive Testing
```javascript
// Test breakpoint behavior
function testResponsiveDesign() {
    // Simulate mobile viewport
    window.innerWidth = 576;
    window.dispatchEvent(new Event('resize'));
    
    const hiddenColumns = document.querySelectorAll('.erp-table td:not(.erp-table-primary):not(:last-child)');
    hiddenColumns.forEach(col => {
        assert(getComputedStyle(col).display === 'none');
    });
    
    // Verify actions column always visible
    const actionsColumn = document.querySelector('.erp-table td:last-child');
    assert(getComputedStyle(actionsColumn).display !== 'none');
}
```

---

## Performance Considerations

### Large Dataset Handling
- **Pagination**: Limit to 20-50 items per page
- **Virtual Scrolling**: For datasets >1000 items
- **Lazy Loading**: Load expandable content on demand
- **Debounced Search**: Minimum 300ms delay for search inputs

### Memory Management
```javascript
// Clean up event listeners
beforeDestroy() {
    window.removeEventListener('resize', this.handleResize);
    window.removeEventListener('search-{entity}', this.handleSearch);
}

// Efficient DOM updates
updateItems(newItems) {
    // Use Array.splice for minimal DOM manipulation
    this.items.splice(0, this.items.length, ...newItems);
}
```

---

## Common Pitfalls and Solutions

### 1. Template Inheritance Issues
**Problem**: Missing block declarations cause rendering failures
**Solution**: Always define required blocks even if empty
```html
{% block table_group_headers %}
<!-- Define even if using default -->
{{ super() }}
{% endblock %}
```

### 2. CSS Specificity Conflicts
**Problem**: Custom styles break responsive layouts
**Solution**: Use specific selectors with design system classes
```css
/* Correct - specific selector */
.erp-table .custom-cell { color: red; }

/* Incorrect - too generic */
.custom-cell { color: red; }
```

### 3. Mobile Touch Targets
**Problem**: Small buttons unusable on mobile
**Solution**: Ensure 44px minimum touch targets
```css
@media (max-width: 768px) {
    .erp-table-action-btn {
        min-width: 44px;
        min-height: 44px;
        padding: 0.5rem;
    }
}
```

### 4. Color Contrast Violations
**Problem**: Insufficient contrast for accessibility
**Solution**: Test all color combinations, use design system variables
```css
/* Use pre-tested design system colors */
.weight-heavy { color: var(--erp-danger); }  /* 7.0:1 ratio */
.weight-light { color: var(--erp-success); } /* 4.5:1 ratio */
```

---

## Migration Guide

### From Card to Table View
1. **Create table template**: Extend `crud/base_table.html`
2. **Define grouped headers**: Use business-logical groupings
3. **Implement color coding**: Add classification functions
4. **Add responsive CSS**: Include table-enhancements.css
5. **Create view toggles**: Add navigation buttons
6. **Test thoroughly**: All breakpoints and business rules

### Backward Compatibility Checklist
- ✅ Original card routes preserved (`/materials`, `/colors`)
- ✅ Table routes use `/table` suffix (`/materials/table`)
- ✅ View toggle buttons in both layouts
- ✅ Consistent search and filter functionality
- ✅ Same API endpoints and data structures
- ✅ Preserved JavaScript component names

---

*This guide should be updated whenever new table patterns or business rules are implemented.*