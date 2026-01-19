# Alibi Pilot Hardening - Implementation Status

## Overview

Hardening Alibi for 3-month pilot deployment with enterprise-grade security, audit, and reporting features.

## ✅ Completed

### Authentication & Authorization (75% Complete)

1. ✅ **User Management** (`alibi/auth.py`)
   - User storage in `alibi/data/users.json`
   - Bcrypt password hashing
   - Roles: operator, supervisor, admin
   - Default users created with warnings to change passwords

2. ✅ **JWT Authentication**
   - `POST /auth/login` → returns JWT token
   - Token-based authentication middleware
   - Secure token generation (HS256)
   - 8-hour token expiration

3. ✅ **Auth API Endpoints**
   - `POST /auth/login` - Login and get token
   - `GET /auth/me` - Get current user info
   - `POST /auth/change-password` - Change password
   - `GET /auth/users` - List users (admin only)
   - `POST /auth/users` - Create user (admin only)
   - `DELETE /auth/users/{username}` - Disable user (admin only)

4. ✅ **Role-Based Authorization**
   - `require_role()` dependency for endpoint protection
   - Role hierarchy: operator < supervisor < admin
   - Ready to apply to existing endpoints

5. ✅ **Dependencies Added**
   - `python-jose[cryptography]>=3.3.0` (JWT)
   - `bcrypt>=4.0.0` (password hashing)
   - `python-multipart>=0.0.6` (form data)

### Audit Logging (Partial)

1. ✅ **Login Auditing**
   - Failed login attempts logged
   - Successful logins logged with role
   - User creation/disable logged

## 🔄 In Progress / TODO

### Backend (Critical Path)

1. **Protect Existing Endpoints** ⚠️ URGENT
   ```python
   # Apply to all incident endpoints
   current_user: User = Depends(get_current_user)
   
   # Examples:
   @app.get("/incidents")
   async def list_incidents(current_user: User = Depends(get_current_user)):
       ...
   
   @app.post("/incidents/{id}/decision")
   async def record_decision(
       current_user: User = Depends(require_role([Role.OPERATOR, Role.SUPERVISOR])):
   ):
       ...
   ```

2. **Approval Workflow** ⚠️ CRITICAL
   ```python
   @app.post("/incidents/{id}/approve")
   async def approve_incident(
       incident_id: str,
       current_user: User = Depends(require_role([Role.SUPERVISOR, Role.ADMIN]))
   ):
       # Convert status:
       # dispatch_pending_review → dispatch_authorized
       # Log approval in audit.jsonl
       ...
   ```

3. **Enhanced Decision Endpoint**
   - Add `dismiss_reason` enum:
     - `false_positive_motion`
     - `normal_behavior`
     - `camera_fault`
     - `weather`
     - `unknown`
   - Validate dismiss_reason required if action='dismissed'
   - Enhanced audit logging with before/after state

4. **Weekly Metrics Aggregation**
   - Cron job or periodic task
   - Aggregate to `alibi/data/weekly_metrics.json`:
     ```json
     {
       "week_ending": "2026-01-25",
       "total_incidents": 127,
       "dismissed_count": 45,
       "dismissed_rate": 0.35,
       "avg_time_to_decision_seconds": 180,
       "top_cameras": [...],
       "top_zones": [...],
       "dismiss_reasons": {
         "false_positive_motion": 25,
         "normal_behavior": 15,
         ...
       }
     }
     ```

5. **KPI Endpoints** ⚠️ CRITICAL
   ```python
   @app.get("/metrics/summary")
   async def get_metrics_summary(
       range: str = "7d",  # 7d, 30d, all
       current_user: User = Depends(get_current_user)
   ):
       return {
           "total_incidents": 127,
           "dismissed_rate": 0.35,
           "escalation_rate": 0.12,
           "avg_time_to_decision": 180,
           "alert_fatigue_score": 0.42,  # 0-1, higher is worse
           "top_cameras": [...],
           "top_zones": [...],
           "time_series": [...]
       }
   ```

6. **Evidence Pack Export** ⚠️ CRITICAL
   ```python
   @app.post("/incidents/{id}/export")
   async def export_evidence_pack(
       incident_id: str,
       current_user: User = Depends(get_current_user)
   ):
       # Create ZIP file:
       # - incident.json (full incident data)
       # - events/ (event JSONs)
       # - snapshots/ (downloaded or placeholders)
       # - report.md (human-readable summary)
       # - audit.json (all audit entries for this incident)
       
       pack_path = f"alibi/data/evidence_packs/{incident_id}.zip"
       # ... create ZIP ...
       
       return {"pack_path": pack_path, "download_url": f"/evidence/{incident_id}.zip"}
   ```

7. **Tighten Validator** ⚠️ SAFETY
   ```python
   # In alibi/validator.py
   
   def validate_incident_plan(plan, incident, config):
       violations = []
       
       # STRICT: No identity claims without watchlist + supervisor
       if contains_identity_language(plan.summary_1line):
           if not incident.metadata.get('watchlist_match'):
               violations.append("Identity claim without watchlist match")
           # TODO: Check if supervisor approval exists
       
       # STRICT: Confidence threshold
       if plan.confidence < config.min_confidence_for_notify:
           if plan.recommended_next_step != "monitor":
               violations.append("Low confidence must recommend monitor only")
       
       # ... existing validation ...
   ```

### Frontend (Critical Path)

1. **Login Page** ⚠️ URGENT
   - Create `/login` route
   - Form with username/password
   - Store token in localStorage
   - Redirect to `/incidents` on success

2. **Token Management**
   - Update `api.ts` to include Authorization header:
     ```typescript
     const token = localStorage.getItem('auth_token');
     headers: {
       'Authorization': `Bearer ${token}`,
       ...
     }
     ```
   - Handle 401 responses → redirect to login
   - Token refresh logic

3. **Role-Aware UI**
   - Hide/disable actions based on user role
   - Example:
     ```tsx
     {user.role === 'supervisor' && (
       <button onClick={handleApprove}>Approve</button>
     )}
     ```
   - Show role badge in header

4. **Approve Button**
   - On incident detail page
   - Only for incidents with `status=dispatch_pending_review`
   - Only for supervisor/admin roles
   - Confirmation modal

5. **Metrics Dashboard** (`/metrics` route)
   - KPI cards (total, dismissed rate, escalation rate)
   - Time series charts
   - Top cameras/zones tables
   - Dismiss reasons pie chart

6. **Evidence Export Button**
   - On incident detail page
   - Shows loading state
   - Downloads ZIP or shows link

### Documentation

1. **Deployment Checklist**
   - Change default passwords
   - Set up HTTPS reverse proxy (nginx/caddy)
   - Configure firewall
   - Secure JWT secret key
   - Backup procedures

2. **Security Checklist**
   - HTTPS required
   - Strong password policy
   - Rate limiting on login endpoint
   - Token rotation policy
   - Audit log retention

## Implementation Priority

### Phase 1 (Today) - Critical Security
1. Protect all existing endpoints with auth ⚠️
2. Approval workflow endpoint ⚠️
3. Enhanced decision with dismiss reasons ⚠️
4. Tighten validator safety rules ⚠️

### Phase 2 (Today) - Frontend Auth
1. Login page
2. Token management in API client
3. Role-aware UI components
4. Approve button

### Phase 3 (Tomorrow) - Reporting
1. KPI calculation logic
2. KPI endpoints
3. Metrics dashboard page
4. Evidence export

### Phase 4 (Tomorrow) - Polish
1. Weekly metrics aggregation
2. Comprehensive testing
3. Documentation
4. Deployment guides

## Files to Create/Modify

### New Files
- [x] `alibi/auth.py` (user management, JWT)
- [ ] `alibi/metrics.py` (KPI calculation)
- [ ] `alibi/evidence_export.py` (ZIP creation)
- [ ] `alibi/data/users.json` (auto-created)
- [ ] `alibi/data/weekly_metrics.json` (auto-created)
- [ ] `alibi/data/evidence_packs/` (directory)
- [ ] `alibi/console/src/pages/LoginPage.tsx`
- [ ] `alibi/console/src/pages/MetricsPage.tsx`
- [ ] `alibi/console/src/contexts/AuthContext.tsx`
- [ ] `DEPLOYMENT_CHECKLIST.md`
- [ ] `SECURITY_CHECKLIST.md`

### Modified Files
- [x] `requirements.txt` (added auth dependencies)
- [x] `alibi/alibi_api.py` (added auth endpoints)
- [ ] `alibi/alibi_api.py` (protect endpoints, add approval/kpi/export)
- [ ] `alibi/validator.py` (tighten safety rules)
- [ ] `alibi/schemas.py` (add dismiss_reason enum)
- [ ] `alibi/console/src/lib/api.ts` (add auth header)
- [ ] `alibi/console/src/App.tsx` (add login route, auth context)
- [ ] `alibi/console/src/pages/IncidentDetailPage.tsx` (add approve button)

## Testing Strategy

1. **Auth Testing**
   - Login with valid/invalid credentials
   - Token expiration handling
   - Role-based endpoint access

2. **Approval Workflow**
   - Operator cannot approve
   - Supervisor can approve
   - Status transitions correctly

3. **Evidence Export**
   - ZIP file created successfully
   - Contains all required files
   - Human-readable report

4. **Metrics**
   - KPI calculations accurate
   - Time series data correct
   - Dashboard renders properly

## Risk Mitigation

1. **Authentication Bypass**: All endpoints must have `Depends(get_current_user)`
2. **Privilege Escalation**: Carefully check role requirements
3. **Audit Trail**: Every action must be logged
4. **Data Export**: Ensure no sensitive data leaks

## Next Steps

I've completed the authentication foundation. To continue with the full hardening:

1. Should I continue implementing the remaining backend features (approval, KPI, export)?
2. Should I implement the frontend login and role-aware UI?
3. Should I focus on documentation and deployment guides?

**Recommendation**: Continue with Phase 1 (protect endpoints, approval workflow, enhanced decisions, validator) as these are critical security features.
