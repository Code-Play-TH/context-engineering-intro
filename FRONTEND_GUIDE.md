# 🎨 Frontend Setup Guide

## ✅ สิ่งที่สร้างเสร็จแล้ว

### หน้าที่มี:

1. **Login Page** (`/login`) - เข้าสู่ระบบด้วย JWT
2. **Dashboard** (`/dashboard`) - ภาพรวมระบบ + สถิติ
3. **KOL List** (`/kols`) - รายการ KOLs พร้อม search
4. **Add KOL** (`/kols/new`) - เพิ่ม KOL ใหม่พร้อม social handles

### Features:

-   ✅ JWT Authentication with auto-refresh
-   ✅ Protected routes
-   ✅ Responsive sidebar navigation
-   ✅ Beautiful UI with Tailwind CSS
-   ✅ Form validation with React Hook Form
-   ✅ API integration with axios
-   ✅ State management with Zustand
-   ✅ Data fetching with TanStack Query

---

## 🚀 วิธีเริ่มใช้งาน

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Development Server

```bash
npm run dev
```

### 3. Open Browser

เปิด: **http://localhost:3000**

คุณจะถูก redirect ไปหน้า login อัตโนมัติ

---

## 🔐 Login

ใช้ account ใดก็ได้จาก:

```
Admin: admin@kolmanagement.com / Admin@123
Manager: manager@kolmanagement.com / Manager@123
AE: ae@kolmanagement.com / AccountExec@123
Viewer: viewer@kolmanagement.com / Viewer@123
```

---

## 📱 หน้าที่ใช้งานได้

### 1. Dashboard (`/dashboard`)

-   แสดงสถิติ: Total KOLs, Campaigns, Active, Reach
-   Quick actions: Add KOL, Create Campaign
-   Recent activity

### 2. KOL List (`/kols`)

-   รายการ KOLs ทั้งหมด
-   Search by name, email, handle
-   แสดง tier (nano, micro, mid, macro, mega)
-   แสดง social handles + follower count
-   Pagination (20 items/page)
-   Click เพื่อดูรายละเอียด

### 3. Add KOL (`/kols/new`)

-   Form สำหรับเพิ่ม KOL ใหม่
-   Basic info: name, email, phone, location
-   Niche & tags (comma-separated)
-   Social handles (multiple platforms)
-   Follower count + verified status
-   Auto tier calculation

---

## 🎨 UI Components

### ใช้ได้แล้ว:

-   ✅ Button (variants: default, outline, ghost, destructive)
-   ✅ Input (text, email, number, password)
-   ✅ Label
-   ✅ Card (with header, title, description, content)
-   ✅ Dashboard Layout (with sidebar)

### Styling:

-   Tailwind CSS
-   Custom color scheme (primary blue)
-   Responsive design
-   Dark mode ready (variables defined)

---

## 🔧 Configuration

### Environment Variables (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### API Integration

-   Base URL: `http://localhost:8000/api/v1`
-   Auto token refresh on 401
-   Axios interceptors configured
-   localStorage for token storage

---

## 📂 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Root (redirects)
│   │   ├── login/page.tsx        # Login page
│   │   ├── dashboard/page.tsx    # Dashboard
│   │   ├── kols/
│   │   │   ├── page.tsx          # KOL list
│   │   │   └── new/page.tsx      # Add KOL
│   │   ├── layout.tsx            # Root layout
│   │   └── globals.css           # Global styles
│   ├── components/
│   │   ├── ui/                   # UI components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   └── card.tsx
│   │   ├── layout/
│   │   │   └── dashboard-layout.tsx
│   │   └── providers.tsx         # React Query provider
│   ├── lib/
│   │   ├── api.ts                # Axios instance
│   │   ├── auth.ts               # Auth functions
│   │   └── utils.ts              # Utilities
│   └── store/
│       └── auth.ts               # Zustand auth store
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

---

## 🎯 Next Steps (ที่ยังไม่ได้ทำ)

### หน้าที่ควรเพิ่ม:

1. **KOL Detail Page** (`/kols/[id]`)

    - ดูรายละเอียด KOL
    - แก้ไขข้อมูล
    - ดู social handles
    - ดู campaigns ที่เกี่ยวข้อง

2. **Campaign List** (`/campaigns`)

    - รายการ campaigns
    - Filter by status
    - Search

3. **Campaign Detail** (`/campaigns/[id]`)

    - ดูรายละเอียด campaign
    - KPIs & deliverables
    - Assigned KOLs

4. **Add Campaign** (`/campaigns/new`)

    - สร้าง campaign ใหม่
    - เพิ่ม KPIs
    - เพิ่ม deliverables

5. **User Management** (`/settings/users`) - Admin only
    - จัดการ users
    - เปลี่ยน roles

---

## 💡 Tips

### Development

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

### Debugging

-   Check browser console for errors
-   Check Network tab for API calls
-   Check localStorage for tokens
-   Backend must be running on port 8000

### Common Issues

**1. API Connection Error**

-   ตรวจสอบ backend running: `http://localhost:8000`
-   ตรวจสอบ CORS settings

**2. Login Failed**

-   ตรวจสอบ credentials
-   ตรวจสอบ backend database seeded

**3. Token Expired**

-   Refresh page (auto-refresh should work)
-   Logout and login again

---

## 🎨 Customization

### Colors

แก้ไขใน `src/app/globals.css`:

```css
:root {
    --primary: 221.2 83.2% 53.3%; /* Blue */
    --secondary: 210 40% 96.1%; /* Light gray */
    --destructive: 0 84.2% 60.2%; /* Red */
    /* ... */
}
```

### Layout

แก้ไขใน `src/components/layout/dashboard-layout.tsx`:

-   Sidebar width
-   Navigation items
-   User menu

---

## 📊 Performance

-   Server-side rendering (SSR) ready
-   Client-side navigation
-   Optimistic updates
-   Automatic code splitting
-   Image optimization (Next.js)

---

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

---

## 📝 Summary

**คุณมี Frontend ที่:**

-   ✅ ใช้งานได้จริง (Login, Dashboard, KOL Management)
-   ✅ สวยงาม (Tailwind CSS + Custom components)
-   ✅ Type-safe (TypeScript)
-   ✅ Modern stack (Next.js 14, React Query, Zustand)
-   ✅ Production-ready architecture

**เริ่มใช้งานได้ทันทีด้วย:**

```bash
cd frontend
npm install
npm run dev
```

**เปิด:** http://localhost:3000

**Login:** admin@kolmanagement.com / Admin@123

---

**Happy Coding! 🎉**
