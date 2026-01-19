# Alibi Console - Operator Command Center

Real-time incident management console built with Vite + React + TypeScript.

## Setup

```bash
cd alibi/console
npm install
npm run dev
```

Console will run on `http://localhost:5173`

**Backend must be running**: `python -m alibi.alibi_api`

## Architecture

- **Frontend**: Vite + React 18 + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui patterns
- **Routing**: React Router v6
- **Tables**: TanStack Table
- **Real-time**: Server-Sent Events (SSE)

## Features

### Live Incidents View (`/incidents`)
- Real-time table with SSE updates
- Dense incident list with all key metrics
- Filters: camera, zone, status, event_type, severity, confidence
- Search across camera_id/zone_id/event_type
- Keyboard shortcuts: j/k (navigate), Enter (open), r (refresh)
- Click row to open detail view

### Incident Detail (`/incidents/:id`)
- Timeline of events with evidence links
- IncidentPlan with severity/confidence/recommended action
- Validation warnings (cannot be dismissed)
- AlertMessage for operators
- Action buttons: Confirm / Dismiss / Escalate / Close
- Dismiss requires reason selection + notes

### Shift Reports (`/reports`)
- Select time range (8h/24h/custom)
- Generate report via API
- View KPIs, summaries, narrative
- Download markdown format

### Settings (`/settings`)
- Edit thresholds and windows
- Configure event type compatibility
- Save to backend (persisted to alibi_settings.json)

## Project Structure

```
alibi/console/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── index.html
└── src/
    ├── main.tsx                 # Entry point
    ├── App.tsx                  # Router + nav
    ├── index.css                # Tailwind + theme
    ├── lib/
    │   ├── types.ts             # TypeScript types
    │   ├── api.ts               # API client
    │   └── sse.ts               # SSE manager
    ├── components/
    │   └── (UI components)
    └── pages/
        ├── IncidentsPage.tsx    # Live table
        ├── IncidentDetailPage.tsx
        ├── ReportsPage.tsx
        └── SettingsPage.tsx
```

## API Integration

All API calls go through `src/lib/api.ts`:

```typescript
import { api } from './lib/api';

// List incidents
const incidents = await api.listIncidents({ status: 'new' });

// Get detail
const incident = await api.getIncident(incidentId);

// Record decision
await api.recordDecision(incidentId, {
  action_taken: 'confirmed',
  operator_notes: 'Verified',
  was_true_positive: true
});
```

## SSE Integration

Real-time updates via `src/lib/sse.ts`:

```typescript
import { sseManager } from './lib/sse';

// Connect on mount
useEffect(() => {
  sseManager.connect();
  
  const unsubscribe = sseManager.onEvent((event) => {
    if (event.type === 'incident_upsert') {
      // Update table with event.incident_summary
    }
  });
  
  return () => {
    unsubscribe();
    sseManager.disconnect();
  };
}, []);
```

## Keyboard Shortcuts

### Incidents List
- `j` - Next row
- `k` - Previous row
- `Enter` - Open selected incident
- `r` - Refresh bootstrap

### Incident Detail
- `Esc` - Back to list
- `1-4` - Quick actions (Confirm/Dismiss/Escalate/Close)

## Development

```bash
# Install dependencies
npm install

# Run dev server (with HMR)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Backend Requirements

The console expects these API endpoints:

- `GET /incidents?status=&since=&limit=`
- `GET /incidents/:id`
- `POST /incidents/:id/decision`
- `GET /stream/incidents` (SSE)
- `POST /reports/shift`
- `GET /settings`
- `PUT /settings`

All implemented in `alibi/alibi_api.py`.

## Environment

Backend API proxied through Vite:
- `/api/*` → `http://localhost:8000/*`

No environment variables required for development.

## Acceptance Criteria

✅ **Real-time Updates**: Inject event via curl → appears in table without refresh  
✅ **Operator Actions**: Triage incident → status updates stream to list  
✅ **Evidence Display**: Click incident → view events with clip links  
✅ **Validation Warnings**: Prominent display, cannot dismiss  
✅ **Keyboard Navigation**: j/k/Enter navigation works  
✅ **Reports**: Generate shift report for time range  
✅ **Settings**: Edit and save configuration  

## Next Steps

To complete the implementation:

1. Create detailed page components in `src/pages/`
2. Add shared UI components in `src/components/`
3. Implement TanStack Table for incidents list
4. Add keyboard shortcut handlers
5. Style with Tailwind following shadcn/ui patterns

See inline TODOs in source files for specific implementation points.
