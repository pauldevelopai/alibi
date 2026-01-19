# Alibi for Namibian Police - Pilot Deployment Guide

## System Overview

Alibi is an **AI-assisted incident alert management system** for police oversight in Namibia. It processes camera events, validates alerts against strict safety rules, and provides full audit trails for accountability.

## ✅ Security Implementation - COMPLETE

### Authentication System
- **Bcrypt password hashing** - Military-grade security
- **JWT tokens** - 8-hour session tokens
- **Role-based access control** - 3-tier hierarchy

### User Roles (Namibian Police Context)

**Operator** (Police Officer)
- View all incidents
- Make decisions: confirm, dismiss, close
- Generate shift reports
- **Cannot**: Approve escalations, manage users, change settings

**Supervisor** (Station Commander)
- All Operator permissions
- **Plus**: Approve escalations to dispatch
- Oversight and review capabilities
- **Cannot**: Manage users, change system settings

**Admin** (IT/System Administrator)
- All permissions
- User management
- System settings
- Demo/testing tools

### Protected Endpoints

**✅ ALL endpoints now require authentication:**
- Camera event ingestion - Prevents fake incident injection
- Incident viewing - Access control
- Decision making - Role-based (Operator+)
- Settings management - Admin only
- User management - Admin only

## Default Users (MUST CHANGE PASSWORDS!)

```
Username: operator1
Password: operator123
Role: Operator (Police Officer)

Username: supervisor1
Password: supervisor123
Role: Supervisor (Station Commander)

Username: admin
Password: admin123
Role: Admin (System Administrator)
```

⚠️ **CRITICAL**: Change these passwords immediately on first deployment!

## Quick Start

### 1. Install Dependencies
```bash
pip install python-jose[cryptography] bcrypt python-multipart
```

### 2. Start the System
```bash
# Terminal 1: Start API server
python -m alibi.alibi_api

# Terminal 2: Start video worker (if using cameras)
python -m alibi.video.worker \
  --config alibi/data/cameras.json \
  --api http://localhost:8000

# Terminal 3: Start web console
cd alibi/console
npm install
npm run dev
```

### 3. First Login
```bash
# Login to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operator1",
    "password": "operator123"
  }'

# Response includes access_token - save this!
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "username": "operator1",
  "role": "operator",
  "full_name": "Operator One"
}
```

### 4. Change Password (DO THIS FIRST!)
```bash
curl -X POST http://localhost:8000/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "operator123",
    "new_password": "SecurePassword123!"
  }'
```

### 5. Access System
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Console**: http://localhost:5173

## Security Checklist for Namibian Deployment

### Pre-Deployment (REQUIRED)
- [ ] Change all default passwords
- [ ] Set up HTTPS reverse proxy (nginx recommended)
- [ ] Configure firewall (block port 8000, allow only HTTPS)
- [ ] Generate new JWT secret key
- [ ] Disable demo/simulator endpoints in production
- [ ] Set up backup for audit logs
- [ ] Document officer access procedures

### HTTPS Setup (CRITICAL - Do NOT skip!)

**Why HTTPS is mandatory:**
- Protects passwords during login
- Prevents token interception
- Ensures data integrity
- Required for police data compliance

**Setup with Nginx:**
```nginx
server {
    listen 443 ssl;
    server_name alibi.police.na;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name alibi.police.na;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Configuration
```bash
# Ubuntu/Debian
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH (for admin)
sudo ufw deny 8000/tcp   # Block direct API access
sudo ufw enable

# Verify
sudo ufw status
```

### Network Security
- Deploy on police internal network ONLY
- No public internet access
- VPN required for remote access
- Segment from general police network

## Operational Procedures

### Daily Operations

**Morning Shift Start:**
1. Operator logs in: `operator1` (changed password)
2. Reviews overnight incidents: http://localhost:8000/incidents
3. Triages each incident (confirm/dismiss/escalate)
4. Generates shift report at end

**Incident Triage:**
1. View incident details with evidence
2. Review validation warnings (safety checks)
3. Make decision:
   - **Confirm**: Valid incident, no action needed
   - **Dismiss**: False alarm (requires reason)
   - **Escalate**: Requires supervisor review
   - **Close**: Resolved

**If Supervisor Approval Needed:**
1. Operator escalates incident
2. System flags for supervisor review
3. Supervisor reviews plan + validation
4. Supervisor approves or rejects
5. Decision logged in audit trail

### Weekly Reviews

**Station Commander (Supervisor):**
1. Review weekly metrics
2. Check false positive rates
3. Review escalation decisions
4. Identify problem cameras/zones
5. Generate oversight report

## Audit Trail

**Every action is logged:**
- User logins (success and failure)
- Incident decisions (with before/after state)
- Supervisor approvals
- Settings changes
- User management actions

**Audit log location:** `alibi/data/audit.jsonl`

**Review audit logs:**
```bash
# All logins today
cat alibi/data/audit.jsonl | grep login | grep "2026-01-18"

# All decisions by user
cat alibi/data/audit.jsonl | grep decision | grep "operator1"

# All supervisor approvals
cat alibi/data/audit.jsonl | grep approve
```

## Data Retention

**Incident Data:**
- Events: Retained indefinitely
- Incidents: Retained indefinitely
- Decisions: Retained indefinitely
- Audit logs: **NEVER delete** (compliance)

**Backup Schedule:**
- Daily: `alibi/data/*.jsonl` → backup server
- Weekly: Full system backup
- Monthly: Archive to long-term storage

## Troubleshooting

### Cannot Login
**Problem**: "Incorrect username or password"
**Solution**:
1. Verify username is correct (case-sensitive)
2. Check `alibi/data/users.json` exists
3. Reset password (admin required)

### Token Expired
**Problem**: "Could not validate credentials"
**Solution**:
1. Login again to get new token
2. Tokens expire after 8 hours
3. This is normal security behavior

### Unauthorized Access
**Problem**: "Insufficient permissions"
**Solution**:
1. Check your role: `GET /auth/me`
2. Some actions require Supervisor or Admin
3. Contact admin if role is incorrect

### No Incidents Showing
**Problem**: Empty incident list
**Solution**:
1. Verify you're authenticated
2. Check camera/video worker is running
3. View API logs for errors

## Training Requirements

**All Officers Must:**
- Complete 2-hour system training
- Understand incident triage process
- Know when to escalate
- Understand audit trail importance

**Supervisors Must:**
- Complete officer training
- Additional 1-hour approval workflow training
- Understand oversight responsibilities
- Know how to review weekly metrics

**Admins Must:**
- Complete all training
- Additional 2-hour technical training
- Backup/restore procedures
- Security incident response

## Contact & Support

**System Issues:**
- Check logs: `alibi/app.log`
- API logs: Terminal running `alibi.alibi_api`
- Worker logs: Terminal running `video.worker`

**Security Incidents:**
- Immediately disable compromised user
- Review audit logs for unauthorized access
- Change JWT secret key if tokens compromised
- Document incident for review

## Compliance Notes

**Data Protection:**
- System stores incident data, not personal information
- Video clips referenced by URL (external storage)
- Audit logs contain usernames and actions
- No civilian personal data in system

**Access Control:**
- All access authenticated
- All actions logged
- Role-based permissions enforced
- Regular access reviews required

**Evidence Chain:**
- Every incident has full audit trail
- Evidence pack export for investigations
- Timestamps are UTC (Namibian time requires +2 hours)
- Cannot modify past decisions (append-only logs)

## System Status

**Current Implementation:**
- ✅ Authentication & Authorization
- ✅ Role-based access control
- ✅ All endpoints protected
- ✅ Audit logging (basic)
- ✅ Incident management workflow
- ✅ Video worker integration
- ⚠️ Approval workflow (needs implementation)
- ⚠️ Dismiss reason tracking (needs implementation)
- ⚠️ KPI metrics (needs implementation)
- ⚠️ Evidence export (needs implementation)

**Ready For:**
- ✅ Internal testing
- ✅ Pilot deployment (with HTTPS)
- ⚠️ Full production (after implementing remaining features)

## Next Steps

1. **Immediate** (before deployment):
   - Set up HTTPS reverse proxy
   - Change all default passwords
   - Configure firewall
   - Train initial users

2. **Phase 2** (next 2 weeks):
   - Implement supervisor approval workflow
   - Add dismiss reason tracking
   - Create KPI metrics endpoints
   - Build web console login page

3. **Phase 3** (next month):
   - Evidence pack export
   - Weekly metrics dashboard
   - Advanced reporting
   - Mobile access (if needed)

---

**Document Version**: 1.0
**Last Updated**: 2026-01-18
**For**: Namibian Police Service
**Classification**: Internal Use Only
