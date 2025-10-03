# PDPA/GDPR Compliance Guide
# KOL Influencer Management System

**Version:** 1.0
**Last Updated:** 2025-10-01
**Status:** Active
**Compliance Framework**: PDPA (Thailand) & GDPR (EU)

---

## 📋 Executive Summary

This document outlines the Personal Data Protection Act (PDPA) and General Data Protection Regulation (GDPR) compliance requirements for the KOL Influencer Management System. The system processes personal data of KOLs (influencers), campaign managers, and end users, requiring strict adherence to data protection regulations.

---

## 🎯 Scope of Personal Data

### 1. Data Subject Categories

#### KOLs (Key Opinion Leaders)
- **Identity Data**: Full name, date of birth, gender, nationality
- **Contact Data**: Email, phone number, physical address
- **Professional Data**: Social media handles, platform accounts, content portfolio
- **Financial Data**: Bank account details, tax ID, payment history
- **Performance Data**: Engagement metrics, follower demographics, earnings
- **Contract Data**: Agreement terms, rates, collaboration history

#### System Users (Internal Staff)
- **Identity Data**: Full name, employee ID, role
- **Contact Data**: Work email, phone number
- **Authentication Data**: Login credentials, access logs, IP addresses
- **Activity Data**: System usage, actions performed, audit trails

#### End Users (Campaign Audiences) - Indirect Collection
- **Engagement Data**: Likes, comments, shares (aggregated from social platforms)
- **Demographic Data**: Age range, location, interests (anonymized)

### 2. Lawful Basis for Processing

| Data Category | PDPA Basis | GDPR Basis | Purpose |
|---------------|-----------|------------|----------|
| KOL Identity & Contact | Consent + Contract | Contract Performance | Campaign management, communication |
| Financial Data | Consent + Legal Obligation | Contract + Legal Obligation | Payment processing, tax compliance |
| Performance Data | Consent + Legitimate Interest | Legitimate Interest | Analytics, reporting |
| User Authentication | Consent + Legal Obligation | Legal Obligation | Security, access control |
| Audit Logs | Legal Obligation | Legal Obligation | Compliance, incident response |

---

## 🔒 Data Protection Principles

### 1. Lawfulness, Fairness, and Transparency
- **Requirement**: Process data only with valid legal basis
- **Implementation**:
  - Clear privacy policy accessible during registration
  - Explicit consent checkboxes for optional data processing
  - Layered privacy notices (summary + full policy)
  - Annual privacy policy review and updates

### 2. Purpose Limitation
- **Requirement**: Collect data only for specified purposes
- **Implementation**:
  - Document data processing purposes in data inventory
  - Restrict internal access based on purpose
  - Prohibit repurposing data without new consent
  - Purpose-specific data retention policies

### 3. Data Minimization
- **Requirement**: Collect only necessary data
- **Implementation**:
  - Required vs. optional fields clearly marked
  - Regular data inventory audits
  - Remove unused data fields
  - Justified business need for each data point

### 4. Accuracy
- **Requirement**: Ensure data is accurate and up-to-date
- **Implementation**:
  - User self-service data update portal
  - Annual data accuracy verification emails
  - Automated data validation rules
  - Correction workflow for disputed data

### 5. Storage Limitation
- **Requirement**: Retain data only as long as necessary
- **Implementation**:
  - Defined retention periods per data category
  - Automated data deletion after retention expiry
  - Legal hold mechanism for litigation
  - Regular retention policy reviews

### 6. Integrity and Confidentiality
- **Requirement**: Secure data against unauthorized access
- **Implementation**:
  - Encryption at rest (AES-256) and in transit (TLS 1.3)
  - Role-based access control (RBAC)
  - Multi-factor authentication (MFA) for sensitive access
  - Regular security audits and penetration testing

---

## 📊 Data Inventory & Mapping

### Personal Data Register

| Data Field | Category | Source | Purpose | Retention | Legal Basis |
|------------|----------|--------|---------|-----------|-------------|
| KOL Full Name | Identity | User Input | Identification, Contracts | 7 years after last activity | Contract |
| KOL Email | Contact | User Input | Communication, Notifications | 7 years after last activity | Contract |
| KOL Phone | Contact | User Input | Communication | 7 years after last activity | Consent |
| KOL Bank Account | Financial | User Input | Payment Processing | 10 years (tax law) | Legal Obligation |
| Social Media Handles | Professional | User Input | Platform Integration | Duration of relationship + 2 years | Contract |
| Follower Count | Performance | Social Media APIs | Analytics, Campaign Planning | Duration of relationship + 2 years | Legitimate Interest |
| Engagement Rate | Performance | Social Media APIs | Analytics, Reporting | Duration of relationship + 2 years | Legitimate Interest |
| Content Posts | Professional | Social Media APIs | Campaign Tracking | Duration of campaign + 3 years | Legitimate Interest |
| User Login Credentials | Authentication | User Registration | Access Control | Duration of account + 30 days | Legal Obligation |
| System Access Logs | Audit | Automated | Security, Compliance | 2 years | Legal Obligation |

### Data Flow Mapping

```
┌─────────────────┐
│   Data Subject  │
│  (KOL/User)     │
└────────┬────────┘
         │ Consent/Contract
         ▼
┌─────────────────┐
│  KOL Platform   │
│  (Web/Mobile)   │
└────────┬────────┘
         │ HTTPS/TLS
         ▼
┌─────────────────┐
│   API Gateway   │
│  (FastAPI)      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│  App   │ │ Database │
│ Server │ │(Postgres)│
└───┬────┘ └────┬─────┘
    │           │
    │    ┌──────┴──────┐
    │    │ Encryption  │
    │    │  at Rest    │
    │    └─────────────┘
    │
    ▼
┌─────────────────┐
│ Third Parties   │
│ - Payment       │
│ - Email         │
│ - Social Media  │
└─────────────────┘
```

---

## 👤 Data Subject Rights

### 1. Right to Access (GDPR Art. 15, PDPA Sec. 30)
**What**: Data subjects can request copies of their personal data

**Implementation**:
- Self-service data export in user dashboard
- JSON/CSV export of all personal data
- Response timeline: 30 days (GDPR), 30 days (PDPA)
- Identity verification required

**API Endpoint**: `GET /api/v1/data-export/me`

**Process**:
1. User submits access request via dashboard
2. System verifies identity (MFA)
3. System generates data package
4. User downloads encrypted archive

### 2. Right to Rectification (GDPR Art. 16, PDPA Sec. 31)
**What**: Data subjects can correct inaccurate data

**Implementation**:
- Self-service data update in profile settings
- Automated validation for data format
- Manual review for critical fields (financial data)
- Audit trail of all corrections

**API Endpoint**: `PATCH /api/v1/profile/me`

### 3. Right to Erasure / Right to be Forgotten (GDPR Art. 17, PDPA Sec. 32)
**What**: Data subjects can request deletion of their data

**Implementation**:
- Account deletion button in settings
- 30-day grace period before permanent deletion
- Anonymization where deletion impossible (legal holds)
- Cascade deletion of related non-essential data

**API Endpoint**: `DELETE /api/v1/account/me`

**Exceptions**:
- Legal obligations (tax records: 10 years)
- Contract enforcement (active disputes)
- Legitimate interests (fraud prevention)

**Process**:
1. User requests account deletion
2. System confirms via email (prevents unauthorized deletion)
3. 30-day soft delete period (data hidden, recovery possible)
4. Hard delete after 30 days (data permanently removed)
5. Audit log retained for compliance

### 4. Right to Data Portability (GDPR Art. 20, PDPA Sec. 33)
**What**: Data subjects can receive data in machine-readable format

**Implementation**:
- JSON export with standardized schema
- CSV export for compatibility
- API integration for third-party platforms
- Includes all provided and generated data

**API Endpoint**: `GET /api/v1/data-export/portable`

**Data Format**:
```json
{
  "export_date": "2025-10-01T00:00:00Z",
  "data_subject": {
    "id": "uuid",
    "name": "string",
    "email": "string"
  },
  "personal_data": {
    "profile": {...},
    "social_accounts": [...],
    "campaigns": [...],
    "performance": [...]
  },
  "format_version": "1.0"
}
```

### 5. Right to Restriction of Processing (GDPR Art. 18, PDPA Sec. 34)
**What**: Data subjects can limit how their data is used

**Implementation**:
- "Pause Account" feature (retain but don't process)
- Granular consent management (opt-out of analytics)
- Restriction flag in database
- Automated enforcement in processing pipelines

**API Endpoint**: `POST /api/v1/account/restrict`

### 6. Right to Object (GDPR Art. 21, PDPA Sec. 35)
**What**: Data subjects can object to processing for direct marketing or legitimate interests

**Implementation**:
- Marketing opt-out checkboxes
- "Do not contact" flag
- Separate consent for each marketing channel
- Immediate effect (no grace period)

**API Endpoint**: `POST /api/v1/consent/object`

### 7. Right to Withdraw Consent (GDPR Art. 7, PDPA Sec. 19)
**What**: Data subjects can revoke consent at any time

**Implementation**:
- Consent management dashboard
- Easy opt-out (as easy as opt-in)
- Granular consent per purpose
- Automatic processing cessation upon withdrawal

**API Endpoint**: `DELETE /api/v1/consent/{consent_id}`

---

## 🔔 Consent Management

### Consent Requirements

**Valid Consent Must Be:**
- **Freely Given**: No coercion, bundled consent prohibited
- **Specific**: Separate consent for each purpose
- **Informed**: Clear explanation of data use
- **Unambiguous**: Affirmative action required (no pre-checked boxes)
- **Withdrawable**: Easy opt-out mechanism

### Consent Types

#### Essential Consent (Required)
- Account creation and authentication
- Contract performance (campaign management)
- Legal compliance (tax, anti-fraud)

#### Optional Consent
- Marketing communications
- Analytics and performance tracking
- Third-party data sharing
- Automated decision-making

### Consent Implementation

**Database Schema**:
```python
class Consent(Base):
    id: UUID
    user_id: UUID
    purpose: str  # e.g., "marketing_email", "analytics"
    status: bool  # True = granted, False = withdrawn
    granted_at: datetime
    withdrawn_at: Optional[datetime]
    consent_text: str  # Exact text shown to user
    version: int  # Privacy policy version
    ip_address: str  # Audit trail
    user_agent: str  # Audit trail
```

**Consent Audit Log**:
- All consent actions logged
- Timestamp, IP, user agent recorded
- Immutable audit trail
- 7-year retention

---

## 🔐 Security Measures

### 1. Encryption

**At Rest**:
- Database: PostgreSQL with encryption (AES-256)
- Files: Encrypted file storage with KMS
- Backups: Encrypted with separate keys

**In Transit**:
- TLS 1.3 for all communications
- Certificate pinning for mobile apps
- No plaintext data transmission

**Key Management**:
- AWS KMS or equivalent
- Key rotation every 90 days
- Separate keys per environment
- Hardware Security Module (HSM) for production

### 2. Access Control

**Authentication**:
- Multi-factor authentication (MFA) required for admin access
- Password complexity requirements (min 12 chars, mixed case, symbols)
- Account lockout after 5 failed attempts
- Session timeout: 15 minutes inactivity, 8 hours maximum

**Authorization**:
- Role-based access control (RBAC)
- Principle of least privilege
- Just-in-time access for sensitive operations
- Access reviews quarterly

**Audit Logging**:
- All data access logged
- Immutable audit trail
- Real-time alerting for anomalous access
- 2-year retention

### 3. Network Security

- Firewall rules (allowlist approach)
- DDoS protection
- Intrusion detection system (IDS)
- Regular penetration testing

### 4. Application Security

- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS protection (Content Security Policy)
- CSRF protection
- Security headers (HSTS, X-Frame-Options)

---

## 🌍 International Data Transfers

### GDPR Adequacy & Transfer Mechanisms

**Scenario 1: EU to EU**
- No special requirements (within EU/EEA)

**Scenario 2: EU to Thailand**
- Standard Contractual Clauses (SCCs)
- Transfer Impact Assessment (TIA)
- Additional safeguards (encryption, access controls)

**Scenario 3: EU to USA**
- EU-US Data Privacy Framework (if applicable)
- Standard Contractual Clauses (SCCs)
- Supplementary measures

**Implementation**:
- Data Processing Agreements (DPAs) with all third parties
- Regular review of adequacy decisions
- Data localization options for high-risk jurisdictions
- User notification of transfer destinations

---

## 📋 Data Protection Impact Assessment (DPIA)

### When DPIA is Required

- New technologies or processing methods
- Large-scale processing of sensitive data
- Systematic monitoring of publicly accessible areas
- Automated decision-making with legal effects
- Processing special categories of data (racial, health, etc.)

### DPIA Process

1. **Describe Processing**: Purpose, data, recipients, retention
2. **Assess Necessity**: Is processing necessary and proportionate?
3. **Identify Risks**: Privacy risks to data subjects
4. **Mitigation Measures**: Security controls, safeguards
5. **DPO Review**: Data Protection Officer approval
6. **Supervisory Authority Consultation**: If high risk remains

### DPIA for KOL System

**Status**: Completed 2025-09-30

**Key Findings**:
- **High Risk**: Social media data scraping could violate platform ToS
- **Mitigation**: Use only official APIs with proper OAuth consent
- **Residual Risk**: Low (acceptable with mitigations)

---

## 👨‍💼 Data Protection Officer (DPO)

### DPO Responsibilities

- Monitor compliance with PDPA/GDPR
- Advise on data protection obligations
- Conduct DPIAs
- Cooperate with supervisory authorities
- Act as point of contact for data subjects

### DPO Contact

**Name**: [To be appointed]
**Email**: dpo@kolsystem.com
**Phone**: +66-XXX-XXX-XXXX
**Address**: [Company Address]

**Availability**: Business hours (9 AM - 6 PM ICT, Mon-Fri)

---

## 🚨 Data Breach Response

### Breach Detection

- Real-time monitoring and alerting
- Automated anomaly detection
- Regular security audits
- User-reported incidents

### Breach Response Plan

**Phase 1: Detection & Containment (0-1 hour)**
1. Confirm breach
2. Activate incident response team
3. Contain breach (isolate systems, revoke access)
4. Preserve evidence

**Phase 2: Assessment (1-4 hours)**
1. Determine scope (affected data, individuals)
2. Assess severity (high/medium/low risk to data subjects)
3. Identify root cause

**Phase 3: Notification (4-72 hours)**
1. **Supervisory Authority**: Within 72 hours (GDPR), without undue delay (PDPA)
2. **Data Subjects**: Without undue delay if high risk to rights/freedoms
3. **DPO**: Immediately

**Notification Content**:
- Nature of breach
- Data categories affected
- Approximate number of data subjects
- Likely consequences
- Mitigation measures taken
- Contact point for inquiries

**Phase 4: Remediation**
1. Fix root cause
2. Implement additional controls
3. Update policies/procedures
4. Staff training

**Phase 5: Post-Incident Review**
1. Lessons learned
2. Update incident response plan
3. Implement preventive measures

### Breach Notification Templates

See: `templates/breach_notification_authority.md`
See: `templates/breach_notification_data_subject.md`

---

## 📄 Privacy Policy & Notices

### Privacy Policy Requirements

**Must Include**:
- Identity of data controller
- Contact details of DPO
- Purposes of processing
- Legal basis for processing
- Recipients of data (third parties)
- International data transfers
- Retention periods
- Data subject rights
- Right to lodge complaint with supervisory authority

**Accessibility**:
- Clear, plain language
- Layered approach (summary + full policy)
- Available in English, Thai (PDPA)
- Prominently displayed during registration
- Version history maintained

### Cookie Notice

**Required for**:
- Analytics cookies
- Marketing cookies
- Third-party cookies

**Implementation**:
- Cookie banner on first visit
- Granular consent options
- Easy to withdraw consent
- Cookie policy page

---

## 🏢 Third-Party Data Processing

### Vendor Management

**Due Diligence**:
- Security assessment questionnaire
- Certifications review (ISO 27001, SOC 2)
- Data protection clauses in contracts
- Regular audits and assessments

### Data Processing Agreements (DPAs)

**Required Clauses**:
- Processing instructions
- Confidentiality obligations
- Security measures
- Sub-processor approval process
- Data subject rights assistance
- Breach notification obligations
- Post-termination data handling
- Audit rights

### Current Third-Party Processors

| Vendor | Purpose | Data Processed | DPA Status | Location |
|--------|---------|----------------|------------|----------|
| AWS | Hosting | All data | ✅ Signed | Ireland (EU) |
| SendGrid | Email | Email addresses, names | ✅ Signed | USA (SCC) |
| Stripe | Payments | Payment details | ✅ Signed | USA (SCC) |
| OpenAI | AI Analysis | Content data (anonymized) | ✅ Signed | USA (SCC) |

---

## 📚 Training & Awareness

### Staff Training Program

**Initial Training** (within 30 days of hire):
- PDPA/GDPR overview
- Data handling procedures
- Security best practices
- Incident reporting

**Annual Refresher**:
- Updates to regulations
- New threats and risks
- Case studies and lessons learned

**Role-Specific Training**:
- Engineers: Secure development, privacy by design
- Support: Handling data subject requests
- Marketers: Consent requirements
- Executives: Legal liabilities, business impact

### Training Records

- Attendance tracked
- Completion certificates
- Assessment scores
- 3-year retention

---

## 📊 Compliance Monitoring

### Quarterly Audits

- Data inventory review
- Consent records audit
- Access control review
- Third-party compliance check

### Annual Assessments

- Full data protection audit
- DPIA reviews
- Privacy policy updates
- Security posture assessment

### Continuous Monitoring

- Automated compliance checks
- Real-time alerting for violations
- Data retention enforcement
- Consent status validation

---

## 📞 Supervisory Authorities

### Thailand (PDPA)

**Personal Data Protection Committee (PDPC)**
- Website: https://www.pdpc.or.th
- Email: pdpc@mdes.go.th
- Phone: +66-2-141-5555

### European Union (GDPR)

**Lead Supervisory Authority** (based on main establishment)
- For companies in Ireland: Data Protection Commission (DPC)
- Website: https://www.dataprotection.ie
- Email: info@dataprotection.ie

**Local Supervisory Authorities**:
- Each EU member state has its own authority
- Data subjects can complain to their local authority

---

## 📝 Documentation & Record-Keeping

### Required Records

1. **Record of Processing Activities (ROPA)**
   - All processing operations documented
   - Updated quarterly
   - Available for supervisory authority inspection

2. **Consent Records**
   - All consent actions logged
   - 7-year retention

3. **Data Subject Requests Log**
   - All DSR requests and responses
   - 7-year retention

4. **Data Breach Log**
   - All breaches (notifiable and non-notifiable)
   - Permanent retention

5. **DPIA Register**
   - All completed DPIAs
   - Reviewed annually

6. **Third-Party DPAs**
   - All signed agreements
   - Contract duration + 7 years

---

## 🔄 Policy Review & Updates

### Review Schedule
- **Quarterly**: Operational compliance checks
- **Annually**: Full policy review
- **Ad-hoc**: Upon regulatory changes or incidents

### Version Control
- All policy changes documented
- Stakeholder approval required
- Staff notified of changes
- Historical versions archived

### Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-01 | Initial PDPA/GDPR compliance document | Legal & Compliance Team |

---

## ✅ Compliance Checklist

### Technical Implementation
- [x] Encryption at rest and in transit
- [x] Role-based access control (RBAC)
- [x] Multi-factor authentication (MFA)
- [x] Audit logging
- [x] Automated data deletion
- [ ] Consent management system (In Progress)
- [ ] Data export/portability API (Planned)
- [ ] Cookie management tool (Planned)

### Documentation
- [x] Privacy policy drafted
- [x] Data inventory completed
- [x] DPIA conducted
- [ ] Cookie policy (Planned)
- [ ] Data retention schedule (Planned)
- [ ] Breach response plan tested (Scheduled Q4 2025)

### Organizational
- [ ] DPO appointed (In recruitment)
- [x] Staff training program established
- [ ] Vendor DPAs signed (In progress - 3/5 complete)
- [ ] Supervisory authority registration (Pending DPO)

---

## 📞 Contact

**Data Protection Officer**: dpo@kolsystem.com
**Privacy Inquiries**: privacy@kolsystem.com
**Security Incidents**: security@kolsystem.com

**For Data Subject Requests**: https://kolsystem.com/privacy/request

---

**Document Owner**: Chief Privacy Officer / DPO
**Approved By**: Legal Counsel, CTO
**Next Review**: 2026-01-01
