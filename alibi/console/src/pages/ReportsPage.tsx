import { useState } from 'react';
import { api } from '../lib/api';
import type { ShiftReport } from '../lib/types';

export function ReportsPage() {
  const [timeRange, setTimeRange] = useState<'8h' | '24h' | 'custom'>('8h');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [report, setReport] = useState<ShiftReport | null>(null);
  const [loading, setLoading] = useState(false);

  async function generateReport() {
    setLoading(true);
    try {
      const now = new Date();
      let start_ts: string;
      let end_ts = now.toISOString();

      if (timeRange === 'custom') {
        start_ts = new Date(customStart).toISOString();
        end_ts = new Date(customEnd).toISOString();
      } else {
        const hours = timeRange === '8h' ? 8 : 24;
        const startDate = new Date(now.getTime() - hours * 60 * 60 * 1000);
        start_ts = startDate.toISOString();
      }

      const data = await api.generateShiftReport(start_ts, end_ts);
      setReport(data);
    } catch (error) {
      console.error('Failed to generate report:', error);
      alert('Failed to generate report');
    } finally {
      setLoading(false);
    }
  }

  function downloadMarkdown() {
    if (!report) return;

    const markdown = `# Shift Report

**Period**: ${new Date(report.start_ts).toLocaleString()} - ${new Date(report.end_ts).toLocaleString()}

## Summary

${report.incidents_summary}

## Key Performance Indicators

- **Total Incidents**: ${report.total_incidents}
- **False Positives**: ${report.false_positive_count}
- **Precision**: ${(report.kpis.precision * 100).toFixed(1)}%

## By Severity

${Object.entries(report.by_severity).map(([sev, count]) => `- Level ${sev}: ${count} incidents`).join('\n')}

## By Action

${Object.entries(report.by_action).map(([action, count]) => `- ${action}: ${count}`).join('\n')}

## Narrative

${report.narrative}

## False Positive Notes

${report.false_positive_notes}
`;

    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `shift-report-${new Date().toISOString().split('T')[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Shift Reports</h1>
          <p className="mt-2 text-sm text-gray-700">
            Generate comprehensive shift summaries with KPIs and narrative
          </p>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Select Time Range</h2>
        
        <div className="space-y-4">
          <div className="flex gap-4">
            <button
              onClick={() => setTimeRange('8h')}
              className={`px-4 py-2 rounded-md ${
                timeRange === '8h'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Last 8 Hours
            </button>
            <button
              onClick={() => setTimeRange('24h')}
              className={`px-4 py-2 rounded-md ${
                timeRange === '24h'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Last 24 Hours
            </button>
            <button
              onClick={() => setTimeRange('custom')}
              className={`px-4 py-2 rounded-md ${
                timeRange === 'custom'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Custom Range
            </button>
          </div>

          {timeRange === 'custom' && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Time
                </label>
                <input
                  type="datetime-local"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  End Time
                </label>
                <input
                  type="datetime-local"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          )}

          <button
            onClick={generateReport}
            disabled={loading || (timeRange === 'custom' && (!customStart || !customEnd))}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      </div>

      {/* Report Display */}
      {report && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Shift Report</h2>
              <p className="text-sm text-gray-500 mt-1">
                {new Date(report.start_ts).toLocaleString()} - {new Date(report.end_ts).toLocaleString()}
              </p>
            </div>
            <button
              onClick={downloadMarkdown}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Download Markdown
            </button>
          </div>

          {/* KPIs Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-500">Total Incidents</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">{report.total_incidents}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-500">Precision</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">
                {(report.kpis.precision * 100).toFixed(1)}%
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-500">True Positives</p>
              <p className="mt-1 text-2xl font-semibold text-green-600">{report.kpis.true_positives}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm font-medium text-gray-500">False Positives</p>
              <p className="mt-1 text-2xl font-semibold text-red-600">{report.false_positive_count}</p>
            </div>
          </div>

          {/* Summary */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Summary</h3>
            <p className="text-sm text-gray-700">{report.incidents_summary}</p>
          </div>

          {/* Severity Breakdown */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-2">By Severity</h3>
            <div className="space-y-2">
              {Object.entries(report.by_severity).map(([sev, count]) => (
                <div key={sev} className="flex items-center">
                  <span className="text-sm text-gray-600 w-24">Level {sev}:</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        parseInt(sev) >= 4 ? 'bg-red-600' :
                        parseInt(sev) >= 3 ? 'bg-orange-500' :
                        'bg-gray-400'
                      }`}
                      style={{ width: `${(count / report.total_incidents) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-600 w-16 text-right">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Actions Breakdown */}
          {Object.keys(report.by_action).length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Actions Taken</h3>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(report.by_action).map(([action, count]) => (
                  <div key={action} className="flex justify-between items-center bg-gray-50 rounded p-3">
                    <span className="text-sm text-gray-700 capitalize">{action}</span>
                    <span className="text-sm font-semibold text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Narrative */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Narrative</h3>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{report.narrative}</p>
          </div>

          {/* False Positive Notes */}
          {report.false_positive_notes && report.false_positive_notes !== 'None reported' && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-2">False Positive Notes</h3>
              <p className="text-sm text-gray-700">{report.false_positive_notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
