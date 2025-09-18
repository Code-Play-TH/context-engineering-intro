name: "Table Redesign Implementation - ERPNext-Inspired Modern Tables"
description: |

## Purpose
Transform existing ERP Factory table components from card-based layouts to modern, ERPNext-inspired table designs with grouped headers, expandable row functionality, and responsive mobile support while maintaining backward compatibility.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Implement a modern table redesign system that transforms existing card-based table displays into ERPNext-inspired tables with:
- Grouped headers with semantic organization
- Expandable rows for detailed information
- Color-coded values based on business logic
- Full responsive design with mobile optimization
- Comprehensive CRUD operations with Alpine.js reactivity
- Template inheritance system for reusable components
- Accessibility compliance with ARIA standards

## Why
- **Business Value**: Improved data density and user experience for ERP operations
- **Integration**: Leverages existing FastAPI backend and template system
- **User Impact**: Faster data scanning, better mobile experience, ERPNext familiarity
- **Problems Solved**: Card layouts waste space, difficult mobile navigation, inconsistent UX

## What
Transform Material Codes and Color Codes tables from card-based to modern table layout while maintaining all existing functionality.

### Success Criteria
- [ ] Material Codes table displays with 3-group headers: "Basic Information", "Specifications", "Status & Actions"  
- [ ] Color Codes table displays with 4-group headers: "Color Information", "Process Details", "Cost & Quality", "Actions"
- [ ] Weight values color-coded: red >50kg, green <10kg, yellow 10-50kg
- [ ] Cost values color-coded: red >$100, yellow $50-100, green <$50
- [ ] Grade highlighting: premium grades in gold, standard in blue
- [ ] Expandable rows with smooth animations showing detailed specifications
- [ ] Responsive design: columns collapse at 768px, touch-friendly mobile controls
- [ ] All CRUD operations functional with proper error handling
- [ ] Backward compatibility: `/cards` routes still functional
- [ ] Print-friendly styling with optimized layouts
- [ ] WCAG 2.1 AA accessibility compliance

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://alpinejs.dev/start-here
  why: Reactive data binding patterns, x-data, x-model, x-text, x-show, x-for with templates
  critical: Use template-based rendering for performance with large datasets
  
- url: https://fastapi.tiangolo.com/advanced/templates/
  why: Jinja2 template inheritance, block system, context passing, url_for usage
  critical: Proper block inheritance prevents rendering failures
  
- url: https://css-tricks.com/snippets/css/complete-guide-grid/
  why: CSS Grid responsive patterns, repeat(), minmax(), auto-fill/auto-fit, fr units
  critical: Use CSS Grid for responsive table layouts without media queries
  
- url: https://www.w3.org/WAI/ARIA/apg/patterns/table/
  why: ARIA table attributes, screen reader compatibility, sortable table accessibility
  critical: Use semantic HTML with proper ARIA labels for accessibility
  
- file: app/templates/crud/base_table.html
  why: Master template with 343 lines showing complete table implementation pattern
  critical: Always extend this template - missing {% block %} declarations cause failures
  
- file: app/static/css/erp-table.css
  why: 441-line CSS framework with responsive breakpoints, animations, color coding
  critical: Use existing classes - custom styles often break responsive layouts
  
- file: app/templates/master_data/material_codes_table.html
  why: Working example of template inheritance with Alpine.js integration
  critical: Follow exact pattern for search filters, stats, and CRUD operations
  
- file: app/templates/master_data/color_codes_table.html  
  why: Advanced example with color previews and cost-based classification
  critical: Shows proper color preview implementation and custom CSS integration
  
- file: app/templates/crud/form_macros.html
  why: 199 lines of reusable form components with Alpine.js binding
  critical: Use existing macros - don't recreate form elements
  
- file: app/static/css/crud-template.css
  why: 752-line design system with CSS custom properties and utilities
  critical: Follow existing design tokens and color variables
```

### Current Codebase tree
```bash
app/
├── templates/
│   ├── crud/
│   │   ├── base_table.html           # Master template (343 lines)
│   │   ├── form_macros.html          # Reusable components (199 lines)
│   │   ├── base_form.html            # Form template
│   │   └── base_list.html            # List template
│   ├── master_data/
│   │   ├── material_codes_table.html # Working example (514 lines)
│   │   ├── color_codes_table.html    # Advanced example (698 lines)
│   │   ├── material_codes.html       # Card-based version (legacy)
│   │   └── color_codes.html          # Card-based version (legacy)
│   └── base.html                     # Root template
├── static/css/
│   ├── erp-table.css                # Table framework (441 lines)
│   ├── crud-template.css            # Design system (752 lines)
│   └── custom.css                   # Utilities (360 lines)
└── routers/
    ├── material_codes.py            # API endpoints
    └── color_codes.py               # API endpoints
```

### Desired Codebase tree with files to be added
```bash
# No new files needed - transformation of existing templates
app/templates/master_data/
├── material_codes_table.html        # ENHANCE: Add color-coded values, grouped headers
├── color_codes_table.html           # ENHANCE: Add cost classification, live color previews  
├── material_codes.html              # MODIFY: Add table view toggle
└── color_codes.html                 # MODIFY: Add table view toggle

# Potential new additions:
app/static/css/
└── table-enhancements.css          # CREATE: Additional color coding and animations

examples/
└── table_implementation_guide.md   # CREATE: Documentation for future table implementations
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: Alpine.js requires proper x-data initialization
# Example: Component functions must return object with all properties
function materialList() {
    return {
        items: [],           # MUST initialize arrays
        loading: false,      # MUST initialize booleans
        expanded: false      # State for each item
    }
}

# CRITICAL: Template inheritance requires exact block names
# Example: {% block table_group_headers %} must match base template
# Missing blocks cause rendering failures

# CRITICAL: CSS specificity with erp-table.css
# Example: Custom styles must be more specific than existing classes
# Use .erp-table .custom-class instead of just .custom-class

# CRITICAL: Mobile breakpoints at 768px and 576px
# Example: Columns hide automatically, ensure actions column always visible
@media (max-width: 576px) {
    .erp-table th:last-child,
    .erp-table td:last-child {
        display: table-cell !important;  # Actions always visible
    }
}

# CRITICAL: Color contrast for accessibility (WCAG 2.1 AA: 4.5:1 ratio)
# Example: Use provided CSS classes, test color combinations
.erp-table-value-positive { color: var(--erp-success); }  # Safe green
.erp-table-value-negative { color: var(--erp-danger); }   # Safe red

# CRITICAL: FastAPI context requires request object
# Example: return templates.TemplateResponse("template.html", {"request": request})

# CRITICAL: Use venv_linux for all Python testing commands
# Example: Run tests with source venv_linux/bin/activate first
```

## Implementation Blueprint

### Data models and structure
No new data models needed - using existing Material Code and Color Code models with enhanced presentation layer.

### List of tasks to be completed in order

```yaml
Task 1 - Enhance Material Codes Table:
MODIFY app/templates/master_data/material_codes_table.html:
  - FIND pattern: "{% block table_group_headers %}"
  - ENHANCE with semantic 3-group headers
  - ADD color-coded weight values with business logic
  - ADD grade highlighting (premium/standard classification)
  - PRESERVE existing Alpine.js functionality

Task 2 - Enhance Color Codes Table:
MODIFY app/templates/master_data/color_codes_table.html:
  - FIND pattern: "{% block table_group_headers %}"
  - ENHANCE with semantic 4-group headers  
  - ADD cost-based classification with color coding
  - ADD live hex color preview circles
  - PRESERVE existing process information display

Task 3 - Add Color Coding CSS:
CREATE app/static/css/table-enhancements.css:
  - MIRROR pattern from: app/static/css/erp-table.css
  - ADD weight-based color classes (.weight-light, .weight-heavy, .weight-medium)
  - ADD cost-based color classes (.cost-budget, .cost-moderate, .cost-expensive)  
  - ADD grade highlighting classes (.grade-premium, .grade-standard)
  - ENSURE WCAG 2.1 AA contrast compliance

Task 4 - Implement JavaScript Enhancements:
MODIFY JavaScript sections in both table templates:
  - ADD color classification logic in Alpine.js components
  - ADD weight categorization helper functions
  - ADD cost classification helper functions
  - PRESERVE existing API integration and error handling

Task 5 - Add Responsive Enhancements:
MODIFY CSS in both table templates:
  - ADD mobile-specific column hiding
  - ADD touch-friendly action buttons  
  - ADD collapsible column behavior at breakpoints
  - ENSURE print-friendly styling

Task 6 - Implement Backward Compatibility:
MODIFY app/templates/master_data/material_codes.html:
  - ADD table view toggle button
  - PRESERVE existing card layout as default
  - ADD route handling for /materials vs /materials/table

MODIFY app/templates/master_data/color_codes.html:
  - ADD table view toggle button
  - PRESERVE existing card layout as default  
  - ADD route handling for /colors vs /colors/table

Task 7 - Create Documentation:
CREATE examples/table_implementation_guide.md:
  - DOCUMENT color coding business rules
  - DOCUMENT responsive behavior patterns
  - DOCUMENT accessibility requirements
  - PROVIDE implementation examples for future tables
```

### Per task pseudocode 

```python
# Task 1: Material Codes Enhancement
# Pseudocode for grouped headers and color coding

# In template {% block table_group_headers %}:
<tr>
    <th class="erp-table-group-header" colspan="3">Basic Information</th>
    <th class="erp-table-group-header" colspan="2">Specifications</th>  
    <th class="erp-table-group-header" colspan="2">Status & Actions</th>
</tr>

# In Alpine.js component:
function getWeightClass(weight) {
    # BUSINESS LOGIC: Weight classification
    if (!weight) return 'erp-table-value-neutral';
    const weightValue = parseFloat(weight);
    if (weightValue > 50) return 'weight-heavy';      # Red
    if (weightValue < 10) return 'weight-light';     # Green  
    return 'weight-medium';                           # Yellow
}

function getGradeClass(grade) {
    # BUSINESS LOGIC: Grade highlighting
    const premiumGrades = ['6061 T6', '7075'];
    if (premiumGrades.includes(grade)) return 'grade-premium';  # Gold
    return 'grade-standard';                                     # Blue
}

# Task 2: Color Codes Enhancement  
# Pseudocode for cost classification and color previews

function getCostClass(cost) {
    # BUSINESS LOGIC: Cost-based classification 
    if (!cost) return 'erp-table-value-neutral';
    const costValue = parseFloat(cost);
    if (costValue >= 100) return 'cost-expensive';   # Red
    if (costValue >= 50) return 'cost-moderate';     # Yellow
    return 'cost-budget';                             # Green
}

function getColorPreview(colorName, hexValue) {
    # PATTERN: Live color preview implementation
    const colorMap = {
        'BLACK': '#000000', 'WHITE': '#FFFFFF', 
        'CHROME': '#C0C0C0', 'GOLD': '#FFD700'
    };
    return hexValue ? `#${hexValue}` : colorMap[colorName] || '#CCCCCC';
}

# Task 3: CSS Color Classes
.weight-heavy { 
    color: var(--erp-danger);      # Red for >50kg
    font-weight: 600; 
}
.weight-light { 
    color: var(--erp-success);     # Green for <10kg  
    font-weight: 600;
}
.weight-medium { 
    color: var(--erp-warning);     # Yellow for 10-50kg
    font-weight: 600; 
}

.grade-premium {
    background: linear-gradient(135deg, #FFD700, #FFA500);  # Gold gradient
    color: #8B4513;
    padding: 0.25rem 0.5rem;
    border-radius: var(--erp-radius-sm);
}

.grade-standard {
    background: var(--erp-info);   # Blue background
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: var(--erp-radius-sm);
}
```

### Integration Points
```yaml
TEMPLATES:
  - inherit from: app/templates/crud/base_table.html
  - use macros: app/templates/crud/form_macros.html
  - follow pattern: existing material_codes_table.html structure
  
CSS:
  - extend: app/static/css/erp-table.css
  - follow: app/static/css/crud-template.css design system
  - new file: app/static/css/table-enhancements.css
  
JAVASCRIPT:
  - pattern: Alpine.js components in existing templates
  - follow: baseTableFunctions() from base_table.html
  - preserve: existing API integration patterns
  
ROUTES:
  - maintain: existing /api/atp/material-codes endpoints
  - maintain: existing /api/atp/color-codes endpoints  
  - add: table view toggles without breaking existing functionality
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
# CRITICAL: Use venv_linux environment
source venv_linux/bin/activate

# Template validation - check for syntax errors
python -c "from jinja2 import Template; Template(open('app/templates/master_data/material_codes_table.html').read())"
python -c "from jinja2 import Template; Template(open('app/templates/master_data/color_codes_table.html').read())"

# CSS validation - check for syntax errors  
css-tree-validator app/static/css/table-enhancements.css

# Expected: No syntax errors. If errors, READ the error and fix.
```

### Level 2: Visual & Functional Tests
```python
# Manual testing checklist - run in browser with dev tools
def test_material_table_layout():
    """Test Material Codes table layout and functionality"""
    # 1. Navigate to /master-data/materials
    # 2. Verify 3-group headers displayed correctly
    # 3. Check weight color coding: red >50kg, green <10kg, yellow 10-50kg
    # 4. Verify grade highlighting: premium in gold, standard in blue
    # 5. Test expandable rows with smooth animation
    # 6. Verify responsive behavior at 768px and 576px breakpoints
    # 7. Test all CRUD operations (view, edit, delete)

def test_color_table_layout():
    """Test Color Codes table layout and functionality"""  
    # 1. Navigate to /master-data/colors
    # 2. Verify 4-group headers displayed correctly
    # 3. Check cost color coding: red >$100, yellow $50-100, green <$50
    # 4. Verify live color preview circles display correctly
    # 5. Test process information in expandable details
    # 6. Verify responsive behavior and touch-friendly controls
    # 7. Test all CRUD operations

def test_accessibility_compliance():
    """Test WCAG 2.1 AA accessibility compliance"""
    # 1. Run axe-core accessibility scanner
    # 2. Verify color contrast ratios ≥4.5:1
    # 3. Test keyboard navigation through table elements
    # 4. Verify ARIA labels and screen reader compatibility
    # 5. Test sortable column accessibility
```

```bash
# Browser testing commands:
# Open in browser and test responsive design
python -m app.main --dev
# Navigate to http://localhost:8000/master-data/materials
# Use browser dev tools to test breakpoints: 768px, 576px
# Test color coding with various weight/cost values
# Verify print preview functionality
```

### Level 3: Integration Test
```bash
# Start the FastAPI service
source venv_linux/bin/activate
python -m app.main --dev

# Test Material Codes API integration
curl -X GET "http://localhost:8000/api/atp/material-codes?limit=20" \
  -H "Authorization: Bearer $TOKEN"

# Expected: JSON array with material codes
# Verify: weight_per_line values for color coding test cases

# Test Color Codes API integration  
curl -X GET "http://localhost:8000/api/atp/color-codes?limit=20" \
  -H "Authorization: Bearer $TOKEN"

# Expected: JSON array with color codes
# Verify: cost_per_sqm values for cost classification test cases

# Test responsive table rendering
curl -X GET "http://localhost:8000/master-data/materials" \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"

# Expected: Mobile-optimized table layout with collapsed columns
```

## Final validation Checklist
- [ ] All templates render without Jinja2 errors
- [ ] No CSS syntax errors: `css-tree-validator app/static/css/table-enhancements.css`
- [ ] Material table shows 3-group headers correctly
- [ ] Color table shows 4-group headers correctly  
- [ ] Weight color coding works: red >50kg, green <10kg, yellow 10-50kg
- [ ] Cost color coding works: red >$100, yellow $50-100, green <$50
- [ ] Grade highlighting works: premium gold, standard blue
- [ ] Live color previews display correctly
- [ ] Expandable rows animate smoothly
- [ ] Responsive design works at 768px and 576px breakpoints
- [ ] All CRUD operations functional (create, read, update, delete)
- [ ] Print styling optimized and readable
- [ ] WCAG 2.1 AA accessibility compliance verified
- [ ] Backward compatibility: card views still accessible
- [ ] Error handling works gracefully
- [ ] Loading states display correctly
- [ ] Empty states show appropriate messages

---

## Anti-Patterns to Avoid
- ❌ Don't create new CSS classes when existing erp-table.css classes work
- ❌ Don't break template inheritance - always extend base_table.html properly
- ❌ Don't ignore responsive breakpoints - test mobile layouts thoroughly  
- ❌ Don't hardcode color values - use CSS custom properties from design system
- ❌ Don't skip accessibility testing - verify ARIA labels and contrast ratios
- ❌ Don't override Alpine.js patterns - follow existing component structure
- ❌ Don't break backward compatibility - preserve /cards routes
- ❌ Don't ignore print styles - tables must remain readable when printed
- ❌ Don't create files longer than 500 lines - split into modules if needed
- ❌ Don't skip color contrast verification - use online tools to verify WCAG compliance