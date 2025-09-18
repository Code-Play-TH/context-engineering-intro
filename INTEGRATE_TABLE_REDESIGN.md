# Integration Task: Table Redesign to Main Web Frontend

## ภารกิจ (Task Overview)
นำ table_redesign_test.html ที่ทดสอบแล้วมาผนวกเข้ากับ frontend template หลักของเว็บ ERP Factory โดยแทนที่ table templates เดิมและปรับปรุงให้เข้ากับระบบ routing และ API เดิม

## เป้าหมาย (Goals)
1. **แทนที่ templates เดิม** - อัพเดต material_codes_table.html และ color_codes_table.html
2. **รักษา backward compatibility** - ให้ card views เดิมทำงานได้ปกติ
3. **ผนวก CSS และ JavaScript** - ใส่ business logic และ responsive design
4. **ทดสอบ integration** - ให้แน่ใจว่าทำงานกับ FastAPI backend

## สิ่งที่ต้องทำ (Implementation Tasks)

### 1. อัพเดต Template Files
```yaml
ไฟล์ที่ต้องแก้:
  - app/templates/master_data/material_codes_table.html
  - app/templates/master_data/color_codes_table.html
  - app/templates/master_data/material_codes.html  
  - app/templates/master_data/color_codes.html

การแก้ไข:
  - นำ HTML structure จาก test file มาใส่
  - เปลี่ยน mockup data เป็น API calls
  - รักษา template inheritance กับ base_table.html
  - เพิ่ม view toggle buttons
```

### 2. อัพเดต CSS Framework
```yaml
ไฟล์ CSS ที่ต้องอัพเดต:
  - app/static/css/table-enhancements.css (มีอยู่แล้ว)
  - app/static/css/erp-table.css (อัพเดตให้เข้ากัน)

สิ่งที่ต้องเพิ่ม:
  - Color classification classes
  - Responsive breakpoints
  - Premium grade styling
  - Enhanced color preview components
```

### 3. อัพเดต JavaScript Components
```yaml
Alpine.js Components ที่ต้องอัพเดต:
  - materialList() - เพิ่ม getWeightClass(), getGradeClass()
  - colorList() - อัพเดต getCostClass(), getColorPreview()

Business Logic Functions:
  - Weight classification (>50kg=red, <10kg=green, 10-50kg=yellow)
  - Grade highlighting (premium=gold, standard=blue)
  - Cost classification (≥$100=red, $50-100=yellow, <$50=green)
  - Color preview with hex value support
```

### 4. อัพเดต API Endpoints (ถ้าจำเป็น)
```yaml
ตรวจสอบ API endpoints:
  - /api/atp/material-codes
  - /api/atp/color-codes

เพิ่ม fields ถ้าขาดหาย:
  - weight_per_line (สำหรับ weight classification)
  - grade (สำหรับ grade highlighting)
  - cost_per_sqm (สำหรับ cost classification)
  - hex_value (สำหรับ enhanced color preview)
```

### 5. อัพเดต Routing (ถ้าจำเป็น)
```yaml
Routes ที่ต้องตรวจสอบ:
  - /master-data/materials (card view)
  - /master-data/materials/table (table view)
  - /master-data/colors (card view)
  - /master-data/colors/table (table view)

Backward Compatibility:
  - Default route ไปที่ card view
  - Table view เป็น optional
  - View toggle buttons ในทุก template
```

## ข้อมูลสำคัญจาก Test File (Key Components)

### HTML Structure Pattern
```html
<!-- Group Headers (Material Codes) -->
<tr>
    <th class="erp-table-group-header" colspan="3">Basic Information</th>
    <th class="erp-table-group-header" colspan="2">Specifications</th>
    <th class="erp-table-group-header" colspan="2">Status & Actions</th>
</tr>

<!-- Group Headers (Color Codes) -->
<tr>
    <th class="erp-table-group-header" colspan="3">Color Information</th>
    <th class="erp-table-group-header" colspan="2">Process Details</th>
    <th class="erp-table-group-header" colspan="2">Cost & Quality</th>
    <th class="erp-table-group-header" colspan="1">Actions</th>
</tr>
```

### CSS Classes ที่สำคัญ
```css
/* Weight Classification */
.weight-heavy   /* Red for >50kg */
.weight-medium  /* Yellow for 10-50kg */  
.weight-light   /* Green for <10kg */

/* Grade Classification */
.grade-premium   /* Gold gradient for premium grades */
.grade-standard  /* Blue for standard grades */

/* Cost Classification */
.cost-expensive  /* Red for ≥$100 */
.cost-moderate   /* Yellow for $50-100 */
.cost-budget     /* Green for <$50 */

/* Enhanced Color Preview */
.enhanced-color-preview /* Improved color circles */
```

### JavaScript Functions ที่สำคัญ
```javascript
// Weight-based color classification
getWeightClass(weight) {
    if (!weight) return 'erp-table-value-neutral';
    const weightValue = parseFloat(weight);
    if (weightValue > 50) return 'weight-heavy';
    if (weightValue < 10) return 'weight-light';
    return 'weight-medium';
}

// Grade highlighting
getGradeClass(grade) {
    const premiumGrades = ['6061 T6', '7075'];
    if (premiumGrades.includes(grade)) return 'grade-premium';
    return 'grade-standard';
}

// Cost-based classification
getCostClass(cost) {
    if (!cost) return 'erp-table-value-neutral';
    const costValue = parseFloat(cost);
    if (costValue >= 100) return 'cost-expensive';
    if (costValue >= 50) return 'cost-moderate';
    return 'cost-budget';
}

// Enhanced color preview
getColorPreview(colorName, hexValue) {
    if (hexValue) {
        return hexValue.startsWith('#') ? hexValue : `#${hexValue}`;
    }
    // Fallback to color mapping...
}
```

## ขั้นตอนการทำงาน (Implementation Steps)

### ขั้นที่ 1: เตรียมงาน
- [ ] สำรอง templates เดิม
- [ ] ตรวจสอบ API responses ว่ามี fields ครบหรือไม่
- [ ] ดู current routing structure

### ขั้นที่ 2: อัพเดต CSS
- [ ] คัดลอก CSS จาก test file ไป app/static/css/table-enhancements.css
- [ ] ตรวจสอบ CSS conflicts กับ existing styles
- [ ] ทดสอบ responsive design

### ขั้นที่ 3: อัพเดต Templates
- [ ] อัพเดต material_codes_table.html
- [ ] อัพเดต color_codes_table.html  
- [ ] เพิ่ม view toggle buttons
- [ ] ทดสอบ template rendering

### ขั้นที่ 4: อัพเดต JavaScript
- [ ] เพิ่ม business logic functions
- [ ] อัพเดต Alpine.js components
- [ ] ทดสอบ API integration

### ขั้นที่ 5: ทดสอบและ Debug
- [ ] ทดสอบ table views
- [ ] ทดสอบ card views (backward compatibility)
- [ ] ทดสอบ responsive design
- [ ] ทดสอบ color coding logic

### ขั้นที่ 6: Production Deployment
- [ ] Code review
- [ ] Integration testing
- [ ] User acceptance testing
- [ ] Deploy to production

## การทดสอบ (Testing Checklist)

### Functional Testing
- [ ] Material codes table แสดง 3-group headers
- [ ] Color codes table แสดง 4-group headers
- [ ] Weight color coding ทำงานถูกต้อง (red >50kg, green <10kg, yellow 10-50kg)
- [ ] Cost color coding ทำงานถูกต้อง (red ≥$100, yellow $50-100, green <$50)
- [ ] Grade highlighting ทำงานถูกต้อง (premium=gold, standard=blue)
- [ ] Color previews แสดงสีถูกต้อง
- [ ] View toggle buttons ทำงาน
- [ ] CRUD operations ทำงานปกติ

### Responsive Testing
- [ ] Desktop (>768px): แสดงทุก column
- [ ] Tablet (768px): condensed display
- [ ] Mobile (≤576px): priority columns only
- [ ] Touch targets ≥44px
- [ ] Action buttons accessible บน mobile

### Accessibility Testing  
- [ ] ARIA labels ครบถ้วน
- [ ] Color contrast ≥4.5:1 ratio
- [ ] Keyboard navigation ทำงาน
- [ ] Screen reader compatibility

### Performance Testing
- [ ] Page load time
- [ ] JavaScript execution time
- [ ] Responsive layout shifts
- [ ] Memory usage

## ไฟล์อ้างอิง (Reference Files)

```
Source Files:
├── table_redesign_test.html (ไฟล์ต้นแบบ)
├── INITIAL_REDESIGN_TABLE.md (requirements)
├── PRPs/table-redesign-implementation.md (technical spec)
└── examples/table_implementation_guide.md (documentation)

Target Files:
├── app/templates/master_data/
│   ├── material_codes_table.html
│   ├── color_codes_table.html
│   ├── material_codes.html
│   └── color_codes.html
├── app/static/css/
│   ├── table-enhancements.css
│   └── erp-table.css
└── app/routers/
    ├── material_codes.py
    └── color_codes.py
```

## หมายเหตุสำคัญ (Important Notes)

⚠️ **Backward Compatibility**: ห้ามทำลาย card views เดิม - ต้องทำงานได้ทั้งสองแบบ

🎨 **Design Consistency**: ใช้ design system เดิม (CSS custom properties)

📱 **Mobile First**: ทดสอบ mobile ก่อนเสมอ

♿ **Accessibility**: ต้องผ่าน WCAG 2.1 AA

🧪 **Testing**: ทดสอบทุก business rule ด้วย real data

## คำสั่งการทำงาน (Commands)

```bash
# สำรอง templates เดิม
cp -r app/templates/master_data app/templates/master_data_backup

# ตรวจสอบ CSS syntax
css-validator app/static/css/table-enhancements.css

# ทดสอบ template rendering
python -c "from jinja2 import Template; Template(open('app/templates/master_data/material_codes_table.html').read())"

# รัน development server
./venv_linux/Scripts/python -m app.main --dev

# ทดสอบ API endpoints
curl -X GET "http://localhost:8000/api/atp/material-codes?limit=10"
curl -X GET "http://localhost:8000/api/atp/color-codes?limit=10"
```

---

**เริ่มงานได้เลย!** ใช้ไฟล์นี้เป็น roadmap ในการนำ table redesign มาใช้จริงในระบบหลัก