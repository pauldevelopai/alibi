import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { sseManager } from '../lib/sse';
import type { IncidentSummary, SSEEvent } from '../lib/types';
import { DemoPanel } from '../components/DemoPanel';

export function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [filter, setFilter] = useState({ status: '', search: '' });
  const navigate = useNavigate();

  useEffect(() => {
    loadIncidents();
    
    // Connect SSE
    sseManager.connect();
    
    const unsubscribe = sseManager.onEvent((event: SSEEvent) => {
      if (event.type === 'incident_upsert' && event.incident_summary) {
        setIncidents(prev => {
          const existing = prev.findIndex(i => i.incident_id === event.incident_summary!.incident_id);
          if (existing >= 0) {
            const updated = [...prev];
            updated[existing] = event.incident_summary!;
            return updated;
          } else {
            return [event.incident_summary!, ...prev];
          }
        });
      }
    });
    
    return () => {
      unsubscribe();
      sseManager.disconnect();
    };
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return; // Skip if in input
      
      if (e.key === 'j') {
        e.preventDefault();
        setSelectedIndex(i => Math.min(i + 1, filteredIncidents.length - 1));
      } else if (e.key === 'k') {
        e.preventDefault();
        setSelectedIndex(i => Math.max(i - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredIncidents[selectedIndex]) {
          navigate(`/incidents/${filteredIncidents[selectedIndex].incident_id}`);
        }
      } else if (e.key === 'r') {
        e.preventDefault();
        loadIncidents();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedIndex, navigate]);

  async function loadIncidents() {
    setLoading(true);
    try {
      const data = await api.listIncidents({ limit: 100 });
      setIncidents(data);
    } catch (error) {
      console.error('Failed to load incidents:', error);
    } finally {
      setLoading(false);
    }
  }

  const filteredIncidents = incidents.filter(inc => {
    if (filter.status && inc.status !== filter.status) return false;
    if (filter.search) {
      const search = filter.search.toLowerCase();
      return (
        inc.incident_id.toLowerCase().includes(search) ||
        inc.camera_id?.toLowerCase().includes(search) ||
        inc.zone_id?.toLowerCase().includes(search) ||
        inc.event_type?.toLowerCase().includes(search)
      );
    }
    return true;
  });

  if (loading) {
    return <div className="px-4 py-8 text-center">Loading incidents...</div>;
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Live Incidents</h1>
          <p className="mt-2 text-sm text-gray-700">
            Real-time incident monitoring | {filteredIncidents.length} incidents
          </p>
        </div>
        <button
          onClick={loadIncidents}
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          Refresh (r)
        </button>
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-4">
        <input
          type="text"
          placeholder="Search camera, zone, or type..."
          value={filter.search}
          onChange={(e) => setFilter(f => ({ ...f, search: e.target.value }))}
          className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
        />
        <select
          value={filter.status}
          onChange={(e) => setFilter(f => ({ ...f, status: e.target.value }))}
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
        >
          <option value="">All Status</option>
          <option value="new">New</option>
          <option value="triage">Triage</option>
          <option value="dismissed">Dismissed</option>
          <option value="escalated">Escalated</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-lg">
        <table className="min-w-full divide-y divide-gray-300">
          <thead className="bg-gray-50">
            <tr>
              <th className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900">Time</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Incident ID</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Status</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Severity</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Confidence</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Action</th>
              <th className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Events</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {filteredIncidents.map((incident, index) => (
              <tr
                key={incident.incident_id}
                onClick={() => navigate(`/incidents/${incident.incident_id}`)}
                className={`cursor-pointer hover:bg-gray-50 ${
                  index === selectedIndex ? 'bg-blue-50' : ''
                }`}
              >
                <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm text-gray-900">
                  {new Date(incident.created_ts).toLocaleTimeString()}
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                  {incident.incident_id}
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm">
                  <span className={`inline-flex rounded-full px-2 text-xs font-semibold leading-5 ${
                    incident.status === 'new' ? 'bg-green-100 text-green-800' :
                    incident.status === 'triage' ? 'bg-yellow-100 text-yellow-800' :
                    incident.status === 'escalated' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {incident.status}
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm">
                  <span className={`inline-flex rounded px-2 text-xs font-semibold leading-5 ${
                    incident.max_severity >= 4 ? 'bg-red-100 text-red-800' :
                    incident.max_severity >= 3 ? 'bg-orange-100 text-orange-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {incident.max_severity}/5
                  </span>
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                  {(incident.avg_confidence * 100).toFixed(0)}%
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                  {incident.recommended_action}
                  {incident.requires_approval && (
                    <span className="ml-2 inline-flex rounded-full bg-yellow-100 px-2 text-xs font-semibold text-yellow-800">
                      Approval
                    </span>
                  )}
                </td>
                <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                  {incident.event_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Keyboard hints */}
      <div className="mt-4 text-sm text-gray-500">
        Keyboard: <kbd className="px-2 py-1 bg-gray-100 rounded">j/k</kbd> navigate, 
        <kbd className="ml-2 px-2 py-1 bg-gray-100 rounded">Enter</kbd> open, 
        <kbd className="ml-2 px-2 py-1 bg-gray-100 rounded">r</kbd> refresh
      </div>

      {/* Demo Panel */}
      <DemoPanel />
    </div>
  );
}
