# Quick Start Guide - Production Deployment

## 🚀 Deploy in 5 Minutes

สำหรับการ deploy บนเซิร์ฟเวอร์ที่มีโปรแกรมอื่นอยู่แล้ว โดยใช้ port ที่ไม่ซ้ำกัน

---

## 📋 ข้อกำหนดเบื้องต้น

- ✅ Docker & Docker Compose ติดตั้งแล้ว
- ✅ มี RAM อย่างน้อย 4GB
- ✅ มี Disk Space อย่างน้อย 20GB

---

## ⚡ Deploy แบบเร็ว (5 ขั้นตอน)

### 1️⃣ เตรียม Environment File

```bash
# คัดลอกไฟล์ template
cp .env.production .env.production.local

# แก้ไข passwords (สำคัญมาก!)
nano .env.production.local
```

**เปลี่ยนค่าเหล่านี้:**
```bash
# Database
POSTGRES_PASSWORD=ใส่รหัสผ่านที่แข็งแรง

# Redis
REDIS_PASSWORD=ใส่รหัสผ่าน_Redis

# Security Keys
SECRET_KEY=สุ่มตัวอักษร_อย่างน้อย_32_ตัว
JWT_SECRET_KEY=สุ่มตัวอักษร_อีกชุด_32_ตัว

# Grafana
GRAFANA_ADMIN_PASSWORD=รหัสผ่าน_Grafana
```

**💡 สร้าง Secret Key อัตโนมัติ:**
```bash
# สำหรับ Linux/Mac
openssl rand -base64 32

# หรือใช้ Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 2️⃣ ตั้งค่า Custom Ports (ถ้าต้องการ)

**Ports เริ่มต้นที่กำหนดไว้:**
```bash
API Server:        8765
Nginx Proxy:       8766
PostgreSQL:        5433
Redis:             6382
Celery Flower:     5556
Prometheus:        9091
Grafana:           3001
```

**ถ้าต้องการเปลี่ยน port:**
```bash
nano .env.production.local

# เปลี่ยนค่าตามต้องการ
APP_PORT=8770           # เปลี่ยนจาก 8765
NGINX_PORT=8771         # เปลี่ยนจาก 8766
# ...
```

---

### 3️⃣ ตั้งค่า Firewall

```bash
# อนุญาต ports ที่จำเป็น
sudo ufw allow 8765/tcp    # API
sudo ufw allow 8766/tcp    # Nginx

# (Optional) สำหรับ monitoring - อนุญาตเฉพาะ IP ของคุณ
sudo ufw allow from YOUR_IP to any port 3001  # Grafana
sudo ufw allow from YOUR_IP to any port 9091  # Prometheus
sudo ufw allow from YOUR_IP to any port 5556  # Flower

# เปิดใช้งาน firewall
sudo ufw enable

# ตรวจสอบสถานะ
sudo ufw status
```

---

### 4️⃣ Deploy!

```bash
# ให้สิทธิ์ script
chmod +x deploy.sh

# Deploy ครั้งแรก
./deploy.sh deploy
```

**สิ่งที่จะเกิดขึ้น:**
- ✅ ตรวจสอบความพร้อมของระบบ
- ✅ ตรวจสอบการตั้งค่า security
- ✅ สร้าง directories ที่จำเป็น
- ✅ Build Docker images
- ✅ เริ่ม services ทั้งหมด
- ✅ รัน database migrations
- ✅ แสดงสถานะ services

---

### 5️⃣ ตรวจสอบว่า Deploy สำเร็จ

```bash
# ตรวจสอบสถานะ services
./deploy.sh status

# ทดสอบ API
curl http://localhost:8765/health

# ควรได้ผลลัพธ์:
# {"status":"healthy","version":"1.0.0",...}
```

---

## 🎯 เข้าถึง Application

### API & Documentation
```
API:                http://YOUR_SERVER_IP:8765
API Docs:           http://YOUR_SERVER_IP:8765/docs
Nginx Proxy:        http://YOUR_SERVER_IP:8766
```

### Monitoring (ถ้าเปิดไว้)
```
Celery Flower:      http://YOUR_SERVER_IP:5556
Grafana:            http://YOUR_SERVER_IP:3001
Prometheus:         http://YOUR_SERVER_IP:9091
```

**Username/Password:**
- Flower: admin/admin (ตั้งใน .env)
- Grafana: admin/(ที่ตั้งใน GRAFANA_ADMIN_PASSWORD)

---

## 📝 คำสั่งที่ใช้บ่อย

```bash
# ดู logs
./deploy.sh logs

# ดูสถานะ
./deploy.sh status

# Restart services
./deploy.sh restart

# Stop services
./deploy.sh stop

# Start services
./deploy.sh start

# Backup database
./deploy.sh backup

# Update deployment
./deploy.sh update

# ดู help
./deploy.sh help
```

---

## 🔍 ตรวจสอบ Ports ที่กำลังใช้งาน

```bash
# ดู ports ทั้งหมดที่กำลังใช้
docker ps --format "table {{.Names}}\t{{.Ports}}"

# หรือใช้ netstat
netstat -tuln | grep -E '8765|8766|5433|6382|5556|9091|3001'
```

---

## 🐛 แก้ไขปัญหาเบื้องต้น

### Port ชนกัน
```bash
# ตรวจสอบว่า port ถูกใช้โดยโปรแกรมอื่นหรือไม่
sudo lsof -i :8765

# วิธีแก้: เปลี่ยน port ใน .env.production.local
nano .env.production.local
APP_PORT=8770  # เปลี่ยนเป็น port อื่น

# Deploy ใหม่
./deploy.sh restart
```

### Services ไม่สามารถเริ่มได้
```bash
# ดู logs เพื่อหาสาเหตุ
./deploy.sh logs

# หรือดู logs ของ service เฉพาะ
docker-compose -f docker-compose.production.yml logs api
```

### Database connection error
```bash
# ตรวจสอบว่า PostgreSQL ทำงานหรือไม่
docker ps | grep postgres

# ตรวจสอบ logs
docker-compose -f docker-compose.production.yml logs postgres

# Restart database
docker-compose -f docker-compose.production.yml restart postgres
```

---

## 📊 ตัวอย่างการใช้งาน API

### 1. สร้าง User (Admin)
```bash
curl -X POST http://localhost:8765/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "strongpassword123",
    "role": "admin"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8765/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=strongpassword123"

# จะได้ access_token กลับมา
```

### 3. ดูข้อมูล KOLs
```bash
curl http://localhost:8765/api/v1/kols/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🔒 Security Checklist

หลัง deploy ให้ตรวจสอบ:

- [ ] เปลี่ยน passwords ทั้งหมดจาก template แล้ว
- [ ] ตั้งค่า firewall เรียบร้อย
- [ ] ปิด ports ที่ไม่จำเป็นต่อภายนอก
- [ ] Database และ Redis ไม่เปิดให้เข้าถึงจากภายนอก
- [ ] Monitoring tools อนุญาตเฉพาะ IP ที่เชื่อถือ
- [ ] ตั้งค่า SSL/TLS สำหรับ production (ถ้ามี domain)

---

## 📚 เอกสารเพิ่มเติม

- **Deployment Guide**: `DEPLOYMENT_GUIDE.md` - คู่มือ deploy แบบละเอียด
- **Port Configuration**: `PORT_CONFIGURATION.md` - การตั้งค่า port
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md` - รายละเอียดทางเทคนิค
- **API Documentation**: http://localhost:8765/docs - เอกสาร API อัตโนมัติ

---

## 🆘 ขอความช่วยเหลือ

หากมีปัญหา:

1. ตรวจสอบ logs: `./deploy.sh logs`
2. ดูสถานะ services: `./deploy.sh status`
3. อ่าน `DEPLOYMENT_GUIDE.md` สำหรับรายละเอียด
4. ตรวจสอบ firewall: `sudo ufw status`
5. ตรวจสอบ ports: `netstat -tuln | grep LISTEN`

---

## ✅ Checklist หลัง Deploy

- [ ] API ตอบสนอง: `curl http://localhost:8765/health`
- [ ] API Docs เข้าได้: http://localhost:8765/docs
- [ ] Nginx proxy ทำงาน: http://localhost:8766/health
- [ ] Database เชื่อมต่อได้
- [ ] Redis ทำงานปกติ
- [ ] Celery workers ทำงาน
- [ ] Monitoring tools เข้าได้ (ถ้าต้องการ)
- [ ] Backups อัตโนมัติตั้งค่าแล้ว
- [ ] Firewall ตั้งค่าถูกต้อง

---

**🎉 Deploy สำเร็จ!**

ระบบ KOL Management ของคุณพร้อมใช้งานบน custom ports แล้ว!

สำหรับคำถามหรือปัญหา กรุณาอ่าน `DEPLOYMENT_GUIDE.md` หรือตรวจสอบ logs
