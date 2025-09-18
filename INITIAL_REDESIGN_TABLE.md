# INITIAL_REDESIGN_TABLE.md

## FEATURE:
Transform existing ERP Factory table components from card-based layouts to modern, ERPNext-inspired table designs with grouped headers, expandable row functionality, and responsive mobile support. The system should maintain backward compatibility while providing enhanced user experience through color-coded values, smooth animations, and comprehensive CRUD operations. Implementation requires a reusable CSS framework, template inheritance system, and JavaScript enhancements for interactive features like sorting, filtering, and real-time statistics.

## EXAMPLES:

### Example 1: Material Codes Table Transformation
**Input**: Existing card-based material codes display at `/master-data/materials/cards`
**Expected Output**: Modern table at `/master-data/materials` with:
- Grouped headers: "Basic Information", "Specifications", "Status & Actions"
- Expandable rows showing detailed material specifications
- Color-coded weight values (red for heavy items >50kg, green for light <10kg)
- Grade highlighting (premium grades in gold, standard in blue)
- Mobile-responsive with collapsible columns on screens <768px

### Example 2: Color Codes Table Implementation
**Input**: Basic color code listing with hex values and process details
**Expected Output**: Enhanced table with:
- 4-group headers: "Color Information", "Process Details", "Cost & Quality", "Actions"
- Live color preview circles displaying actual hex colors
- Cost-based classification (red for expensive >$100, yellow for moderate $50-100, green for budget <$50)
- Expandable details revealing process specifications, quality metrics, and usage guidelines
- Print-friendly styling with optimized layouts

### Example 3: Base Template System Usage
**Input**: New table component requirement for inventory management
**Expected Output**: Inherit from `base_table.html` template with:
- Consistent header structure and styling from `erp-table.css`
- Alpine.js integration for reactive data binding
- Built-in CRUD operation handlers (create, edit, delete, view)
- Automatic pagination with 20/50/100 item limits
- Error handling with session management and toast notifications

## DOCUMENTATION:

### Core Technical References:
- **ERPNext Table Design Guidelines**: https://docs.erpnext.com/user/manual/en/setting-up/articles/table-design-standards
- **Alpine.js Documentation**: https://alpinejs.dev/start-here for reactive data binding and component interactivity
- **FastAPI Template System**: https://fastapi.tiangolo.com/advanced/templates/ for Jinja2 template inheritance
- **CSS Grid and Flexbox Guide**: https://css-tricks.com/snippets/css/complete-guide-grid/ for responsive table layouts
- **Accessibility Guidelines**: https://www.w3.org/WAI/ARIA/apg/patterns/table/ for ARIA labels and keyboard navigation

### Project-Specific Files:
- `app/static/css/erp-table.css` - 422-line CSS framework with responsive breakpoints and animation keyframes
- `app/templates/crud/base_table.html` - Reusable table template with block inheritance system
- `PLANNING.md` - Project architecture and coding standards (mandatory reading)
- `TASK.md` - Task tracking and completion status (check before starting work)

## OTHER CONSIDERATIONS:

### Performance Constraints:
- **File Size Limit**: Never create files longer than 500 lines of code - split into modules if approaching this limit
- **Page Load Time**: Target <2 seconds for table rendering with proper loading states
- **Mobile Performance**: Optimize for touch interfaces with appropriately sized buttons (minimum 44px touch targets)
- **Memory Usage**: Use Alpine.js reactivity to minimize DOM manipulation overhead

### Common AI Coding Assistant Mistakes to Avoid:
- **Template Inheritance Errors**: Always extend `base_table.html` properly - missing `{% block %}` declarations cause rendering failures
- **CSS Specificity Issues**: Use consistent class naming from `erp-table.css` - custom styles often break responsive layouts
- **Mobile Responsiveness Oversights**: Test column hiding at 768px and 576px breakpoints - tables often become unusable on mobile
- **Accessibility Violations**: Include ARIA labels for sortable columns and expandable rows - screen readers cannot navigate unlabeled table controls
- **Route Compatibility Breaking**: Always maintain legacy routes with `/cards` suffix for backward compatibility
- **Color Contrast Failures**: Ensure color-coded values meet WCAG 2.1 AA standards (4.5:1 contrast ratio minimum)

### Edge Cases and Error Handling:
- **Empty Data States**: Display appropriate messages when tables have no data instead of blank screens
- **API Failures**: Implement graceful degradation with error messages and retry mechanisms
- **Browser Compatibility**: Test in IE11+ and ensure CSS Grid fallbacks are available
- **Print Functionality**: Verify table layouts remain readable when printed (hidden responsive columns should be restored)
- **Session Timeout**: Handle authentication expiration gracefully with appropriate redirects
- **Large Dataset Performance**: Implement pagination controls and lazy loading for tables with >1000 rows

### Development Environment Requirements:
- Use `venv_linux` virtual environment for all Python commands and testing
- Follow PEP8 standards with type hints and Black formatting
- Create Pytest unit tests in `/tests` folder mirroring app structure
- Update `TASK.md` immediately after completing tasks
- Use `python_dotenv` and `load_env()` for environment variable management