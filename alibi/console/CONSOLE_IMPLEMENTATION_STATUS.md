# Alibi Console Implementation Status

## ✅ COMPLETED

### Backend API (FastAPI)
- ✅ SSE endpoint `/stream/incidents` with heartbeat
- ✅ Enhanced `/incidents` endpoint with `since` parameter
- ✅ Shift report generation `/reports/shift`
- ✅ Settings GET/PUT endpoints
- ✅ CORS middleware for frontend
- ✅ All original endpoints from Prompt 2

### Frontend Foundation
- ✅ Vite + React + TypeScript project setup
- ✅ Package.json with all dependencies
- ✅ TypeScript configuration
- ✅ Tailwind CSS + shadcn/ui theme
- ✅ Vite config with API proxy
- ✅ Project structure (src/, components/, pages/, lib/)

### Core Libraries
- ✅ Type definitions (`src/lib/types.ts`)
- ✅ API client (`src/lib/api.ts`)
- ✅ SSE manager (`src/lib/sse.ts`)
- ✅ Main app with routing (`src/App.tsx`)
- ✅ CSS with Tailwind + theme variables

## 📝 IMPLEMENTATION NEEDED

To complete the console, create these page components:

### 1. `/incidents` - IncidentsPage.tsx
**Priority: HIGH**

```typescript
// Key features:
- TanStack Table for dense incident list
- Real-time updates via SSE (sseManager.onEvent)
- Filters: camera, zone, status, event_type, severity range, confidence min
- Search bar for camera_id/zone_id/event_type
- Keyboard shortcuts: j/k/Enter/r
- Row click → navigate to /incidents/:id
- Badges for severity, confidence, requires_approval
- Auto-refresh on SSE events
```

Columns:
- Time (created_ts)
- Camera (camera_id)
- Zone (zone_id)
- Type (event_type)
- Severity (1-5 badge)
- Confidence (percentage)
- Status (new/triage/dismissed/escalated/closed)
- Approval Required (badge if true)

### 2. `/incidents/:id` - IncidentDetailPage.tsx
**Priority: HIGH**

```typescript
// Key features:
- Fetch incident detail on mount
- Timeline of events (sorted by ts)
- Evidence section with clip/snapshot links
- IncidentPlan display (summary, severity, confidence, recommended action)
- Validation warnings block (prominent, cannot dismiss)
- AlertMessage display (title, body, operator actions)
- Action buttons: Confirm / Dismiss / Escalate / Close
- Dismiss modal with reason dropdown + notes field
- Submit → api.recordDecision → navigate back
```

Layout:
- Header: incident_id, status badge, timestamps
- Events timeline: event_type, time, confidence, severity, evidence links
- Plan section: summary, recommended action, risk flags
- Validation warnings: violations (red), warnings (yellow)
- Alert section: title, body, actions
- Action buttons footer

### 3. `/reports` - ReportsPage.tsx
**Priority: MEDIUM**

```typescript
// Key features:
- Time range selector (8h/24h/custom)
- Generate button → api.generateShiftReport
- Display report: incidents_summary, KPIs, narrative
- By severity/action breakdowns
- False positive notes
- Download as markdown button
```

Layout:
- Time range controls
- Generate button
- Report display: KPIs grid, summaries, narrative
- Download button

### 4. `/settings` - SettingsPage.tsx
**Priority: MEDIUM**

```typescript
// Key features:
- Fetch settings on mount
- Form for editing:
  - Thresholds (min_confidence_for_notify, high_severity_threshold)
  - Windows (merge_window_seconds, dedup_window_seconds)
  - Compatible event types (list editor)
- Save button → api.updateSettings
- Success/error notifications
```

Layout:
- Sections: Thresholds, Grouping Windows, Event Type Compatibility
- Input fields with labels and help text
- Save/Reset buttons
- Success banner on save

## Implementation Guide

### Step 1: Install Dependencies
```bash
cd alibi/console
npm install
```

### Step 2: Create IncidentsPage.tsx
Focus on:
1. TanStack Table setup
2. SSE connection and event handling
3. Filter/search UI
4. Keyboard shortcuts (useEffect with event listeners)

### Step 3: Create IncidentDetailPage.tsx
Focus on:
1. useParams to get incident ID
2. Fetch detail on mount
3. Display all sections
4. Action buttons with modal for dismiss
5. api.recordDecision on submit

### Step 4: Create ReportsPage.tsx & SettingsPage.tsx
Simpler pages, straightforward forms and API calls.

### Step 5: Test End-to-End
```bash
# Terminal 1: Start backend
python -m alibi.alibi_api

# Terminal 2: Start console
cd alibi/console && npm run dev

# Terminal 3: Inject event
curl -X POST http://localhost:8000/webhook/camera-event \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_test",
    "camera_id": "cam_01",
    "ts": "2026-01-18T16:00:00",
    "zone_id": "zone_a",
    "event_type": "person_detected",
    "confidence": 0.85,
    "severity": 3,
    "clip_url": "https://example.com/clip.mp4"
  }'

# Expected: Incident appears in console table via SSE
```

## Quick Start Template

Each page should follow this pattern:

```typescript
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { IncidentSummary } from '../lib/types';

export function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIncidents();
  }, []);

  async function loadIncidents() {
    setLoading(true);
    try {
      const data = await api.listIncidents();
      setIncidents(data);
    } catch (error) {
      console.error('Failed to load incidents:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-semibold text-gray-900">Live Incidents</h1>
      {/* Table implementation */}
    </div>
  );
}
```

## Resources

- TanStack Table: https://tanstack.com/table/v8/docs/guide/introduction
- React Router: https://reactrouter.com/en/main
- Tailwind CSS: https://tailwindcss.com/docs
- shadcn/ui examples: https://ui.shadcn.com

## Status Summary

**Backend**: 100% complete ✅  
**Frontend Foundation**: 100% complete ✅  
**Page Components**: 0% complete 🔨  

**Next Action**: Implement IncidentsPage.tsx with TanStack Table and SSE

---

The system architecture and API are fully operational. Page components need implementation following the patterns established in the foundation.
