import { useEffect, useState } from 'react';
import { api } from '../lib/api';

export function MetricsPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');

  useEffect(() => {
    loadMetrics();
  }, [timeRange]);

  async function loadMetrics() {
    setLoading(true);
    try {
      const data = await api.getMetricsSummary(timeRange);
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <div className="px-4 py-8 text-center">Loading metrics...</div>;
  }

  // If metrics endpoint returns placeholder/error, show a basic UI
  if (!metrics || metrics.status === 'placeholder') {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="sm:flex sm:items-center sm:justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">KPI Dashboard</h1>
            <p className="mt-2 text-sm text-gray-700">
              Real-time performance metrics and analytics
            </p>
          </div>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Metrics Not Yet Implemented</h3>
              <p className="mt-2 text-sm text-yellow-700">
                The backend metrics aggregation system is being built. Check back soon for:
              </p>
              <ul className="mt-2 text-sm text-yellow-700 list-disc list-inside">
                <li>Total incidents and dismissed rate</li>
                <li>Time-to-decision statistics</li>
                <li>Escalation rates</li>
                <li>Top cameras and zones</li>
                <li>Alert fatigue scores</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Placeholder cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white shadow rounded-lg p-6">
            <p className="text-sm font-medium text-gray-500">Total Incidents</p>
            <p className="mt-2 text-3xl font-semibold text-gray-900">—</p>
            <p className="mt-1 text-xs text-gray-500">Last {timeRange}</p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <p className="text-sm font-medium text-gray-500">Dismissed Rate</p>
            <p className="mt-2 text-3xl font-semibold text-gray-900">—</p>
            <p className="mt-1 text-xs text-gray-500">False positive %</p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <p className="text-sm font-medium text-gray-500">Avg Response Time</p>
            <p className="mt-2 text-3xl font-semibold text-gray-900">—</p>
            <p className="mt-1 text-xs text-gray-500">Minutes to decision</p>
          </div>
          <div className="bg-white shadow rounded-lg p-6">
            <p className="text-sm font-medium text-gray-500">Escalation Rate</p>
            <p className="mt-2 text-3xl font-semibold text-gray-900">—</p>
            <p className="mt-1 text-xs text-gray-500">% requiring escalation</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">KPI Dashboard</h1>
          <p className="mt-2 text-sm text-gray-700">
            Real-time performance metrics and analytics
          </p>
        </div>
        <div className="mt-4 sm:mt-0">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
          >
            <option value="8h">Last 8 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-sm font-medium text-gray-500">Total Incidents</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{metrics.total_incidents || 0}</p>
          <p className="mt-1 text-xs text-gray-500">Last {timeRange}</p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-sm font-medium text-gray-500">Dismissed Rate</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">
            {((metrics.dismissed_rate || 0) * 100).toFixed(1)}%
          </p>
          <p className="mt-1 text-xs text-gray-500">False positive rate</p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-sm font-medium text-gray-500">Avg Response Time</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">
            {metrics.avg_time_to_decision ? `${metrics.avg_time_to_decision.toFixed(1)}m` : '—'}
          </p>
          <p className="mt-1 text-xs text-gray-500">Minutes to decision</p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <p className="text-sm font-medium text-gray-500">Escalation Rate</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">
            {((metrics.escalation_rate || 0) * 100).toFixed(1)}%
          </p>
          <p className="mt-1 text-xs text-gray-500">% requiring escalation</p>
        </div>
      </div>

      {/* Top Cameras & Zones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Top Cameras</h2>
          {metrics.top_cameras && metrics.top_cameras.length > 0 ? (
            <div className="space-y-3">
              {metrics.top_cameras.map((camera: any, i: number) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{camera.camera_id}</span>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 w-32">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${(camera.count / metrics.top_cameras[0].count) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{camera.count}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No data available</p>
          )}
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Top Zones</h2>
          {metrics.top_zones && metrics.top_zones.length > 0 ? (
            <div className="space-y-3">
              {metrics.top_zones.map((zone: any, i: number) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{zone.zone_id}</span>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 w-32">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${(zone.count / metrics.top_zones[0].count) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-gray-900">{zone.count}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No data available</p>
          )}
        </div>
      </div>

      {/* Alert Fatigue Score */}
      {metrics.alert_fatigue_score !== undefined && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Alert Fatigue Score</h2>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="bg-gray-200 rounded-full h-4">
                <div
                  className={`h-4 rounded-full ${
                    metrics.alert_fatigue_score > 0.7 ? 'bg-red-600' :
                    metrics.alert_fatigue_score > 0.4 ? 'bg-yellow-600' :
                    'bg-green-600'
                  }`}
                  style={{ width: `${metrics.alert_fatigue_score * 100}%` }}
                />
              </div>
            </div>
            <span className="text-2xl font-semibold text-gray-900">
              {(metrics.alert_fatigue_score * 100).toFixed(0)}%
            </span>
          </div>
          <p className="mt-2 text-sm text-gray-600">
            {metrics.alert_fatigue_score > 0.7 ? 'High alert volume may cause operator fatigue' :
             metrics.alert_fatigue_score > 0.4 ? 'Moderate alert volume' :
             'Alert volume is manageable'}
          </p>
        </div>
      )}
    </div>
  );
}
