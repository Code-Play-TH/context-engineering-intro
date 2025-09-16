# 🚀 Session Brief Template
## Template สำหรับการเริ่มงานแต่ละครั้ง

---

## 📋 **Template การสั่งงานเริ่ม Session**

```
เริ่มงาน [TASK_NAME] - ช่วย quick context check:

📊 Context Check:
1. อ่าน PLANNING.md และบอกสิ่งที่อาจไม่ตรงปัจจุบัน
2. เช็ค pending tasks ใน TASK.md  
3. แนะนำ minimal updates ที่จำเป็น
4. เริ่มงานด้วย accurate context

🎯 Task Details:
[รายละเอียดงานที่ต้องการ]

📋 Requirements (ถ้ามี):
- [Requirement 1]
- [Requirement 2]
- [Technical constraints]

🧪 Success Criteria:
- [เกณฑ์ความสำเร็จ]
- [Testing requirements]
```

---

## 🎯 **Templates ตามประเภทงาน**

### **🔧 Template: การเพิ่ม Feature ใหม่**
```
เริ่มงาน: เพิ่ม feature [FEATURE_NAME]

📊 Context Check รวดเร็ว:
1. เช็ค PLANNING.md architecture patterns
2. ดู existing similar features
3. ตรวจสอบ database schema requirements

🎯 Feature Requirements:
- [Business requirement]
- [Technical requirement]  
- [UI/UX requirement]
- [Performance requirement]

📋 Implementation Plan:
1. วิเคราะห์ existing code patterns
2. สร้าง API endpoints (ถ้าจำเป็น)
3. สร้าง frontend components
4. เพิ่ม tests และ validation
5. Update documentation

🧪 Testing Strategy:
- API testing ด้วย curl/Postman
- Frontend functionality testing
- Integration testing
- User acceptance criteria
```

### **🐛 Template: การแก้ Bug**
```
แก้ไข Bug: [BUG_DESCRIPTION]

📍 Bug Context:
- Error Message: [EXACT_ERROR]
- Location: [FILE/FUNCTION/LINE]
- When: [CONDITIONS_WHEN_OCCURS]
- Environment: [BROWSER/OS/VERSION]

🔍 Investigation Request:
1. วิเคราะห์สาเหตุหลัก
2. เช็ค related code ที่อาจได้รับผลกระทบ
3. เสนอวิธีแก้ที่ปลอดภัย
4. ป้องกันไม่ให้เกิดซ้ำ

✅ Fix Criteria:
- Bug หายไป
- ไม่ส่งผลกระทบต่อ existing functionality
- เพิ่ม validation ป้องกันในอนาคต
```

### **📊 Template: การปรับปรุง Performance**
```
ปรับปรุง Performance: [AREA_TO_OPTIMIZE]

📊 Current State Check:
1. วัด current performance metrics
2. ระบุ bottlenecks หลัก
3. เช็ค existing optimization attempts

🎯 Optimization Goals:
- Target: [SPECIFIC_METRICS]
- Constraints: [TECHNICAL_LIMITATIONS]
- Priority: [HIGH/MEDIUM/LOW]

📋 Optimization Plan:
1. Profile และวิเคราะห์ performance
2. ระบุ quick wins และ major improvements
3. Implement changes incrementally
4. Measure และ validate improvements
5. Document optimization techniques
```

### **🔄 Template: การ Refactoring**
```
Refactoring: [COMPONENT/MODULE_NAME]

📊 Refactoring Scope:
1. เช็ค current code structure
2. ระบุ pain points และ technical debt
3. วิเคราะห์ผลกระทบต่อ dependent code

🎯 Refactoring Goals:
- [Code quality improvement]
- [Maintainability enhancement]  
- [Performance consideration]
- [Testing improvement]

📋 Refactoring Strategy:
1. สร้าง tests ครอบคลุม existing behavior
2. Refactor incrementally
3. Maintain backward compatibility
4. Update documentation
5. Verify all tests pass

⚠️ Risk Mitigation:
- Backup current working state
- Test thoroughly after each change
- Ready to rollback if needed
```

---

## 🔍 **Quick Reference: เมื่อไหร่ต้อง Context Check**

### **✅ ต้องทำ Full Context Check:**
- [ ] งานใหม่ที่ใช้เวลา > 2 ชั่วโมง
- [ ] เปลี่ยน architecture หรือ database
- [ ] เพิ่ม external dependencies
- [ ] งานที่ส่งผลต่อหลาย modules
- [ ] หลังจากไม่ได้ทำงานโปรเจคนี้ > 1 สัปดาห์

### **⚡ พอใจ Quick Check:**
- [ ] Bug fixes เล็กๆ
- [ ] UI/CSS adjustments
- [ ] Documentation updates
- [ ] Configuration changes
- [ ] งานต่อเนื่องจาก session ก่อน

---

## 📝 **Session End Template**

```
📋 Session Summary:
✅ Completed Tasks:
- [Task 1 with brief description]
- [Task 2 with brief description]

🔄 In Progress:
- [Ongoing task with current status]

📋 Next Session TODO:
- [Priority task 1]
- [Priority task 2]

⚠️ Important Notes:
- [Any critical information for next session]
- [Temporary workarounds that need fixing]
- [Dependencies waiting on external factors]

📊 Documentation Updates Needed:
- [ ] PLANNING.md (ถ้ามี architecture changes)
- [ ] TASK.md (update completed/pending tasks)
- [ ] CLAUDE.md (update important context)
```

---

## 🎯 **Best Practices**

### **⏱️ Time Management:**
- Context check: 3-5 นาทีสำหรับงานเล็ก, 10-15 นาทีสำหรับงานใหญ่
- Documentation update: เฉพาะส่วนที่เปลี่ยนแปลง
- Focus ที่ accuracy มากกว่า completeness

### **🎯 Effective Communication:**
- ใช้ specific error messages และ context
- ระบุ success criteria ชัดเจน
- เสนอ testing strategy
- บอก constraints และ limitations

### **🔄 Continuous Improvement:**
- บันทึก lessons learned ใน session end
- ปรับปรุง templates ตามประสบการณ์
- Share knowledge กับ team members

---

## 📞 **Emergency Templates**

### **🚨 Critical Bug Template:**
```
🚨 CRITICAL BUG: [DESCRIPTION]

⚡ Immediate Action Required:
- Impact: [USER_IMPACT]
- Urgency: [TIMELINE]
- Workaround: [TEMPORARY_SOLUTION]

📍 Skip normal context check - fix immediately:
1. ระบุสาเหตุหลัก
2. Apply emergency fix
3. Test thoroughly
4. Deploy หรือ hotfix
5. Plan proper solution later
```

### **⏰ Quick Fix Template:**
```
⏰ Quick Fix: [ISSUE]

📍 Fast Track:
- Expected time: [DURATION]
- Risk level: [LOW/MEDIUM/HIGH]
- Impact scope: [SPECIFIC_AREA]

✅ Quick resolution plan:
1. [Step 1]
2. [Step 2] 
3. [Step 3]
4. Quick test
5. Done
```

---

**💡 Tip: Copy template ที่เหมาะสมแล้วแก้ไข [PLACEHOLDERS] ตามงานจริง**