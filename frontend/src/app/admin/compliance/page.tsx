'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { adminComplianceApi, getApiErrorMessage, ComplianceEvent } from '@/src/lib/admin-api';
import type { PaginationMeta } from '@/src/types';
import {
  Shield,
  AlertCircle,
  Loader2,
  ChevronRight,
  ChevronLeft,
  ChevronsLeft,
  ChevronsRight,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Info,
} from 'lucide-react';

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'text-red-400 bg-red-500/10 border-red-500/20',
  high: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  low: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  info: 'text-gray-400 bg-gray-800 border-white/5',
};

const STATUS_STYLES: Record<string, string> = {
  open: 'text-red-400 bg-red-500/10',
  in_progress: 'text-yellow-400 bg-yellow-500/10',
  resolved: 'text-green-400 bg-green-500/10',
  closed: 'text-gray-400 bg-gray-800',
};

export default function AdminCompliancePage() {
  const [events, setEvents] = useState<ComplianceEvent[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState({ total: 0, open: 0, resolvedToday: 0 });

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await adminComplianceApi.list({ page, page_size: 20 });
      setEvents(data.data);
      setPagination(data.pagination);
      // Calculate stats from response
      setStats({
        total: data.pagination.total_items,
        open: data.data.filter((e) => e.status === 'open' || e.status === 'in_progress').length,
        resolvedToday: data.data.filter(
          (e) => e.status === 'resolved' && e.resolved_at &&
            new Date(e.resolved_at).toDateString() === new Date().toDateString()
        ).length,
      });
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const StatBox = ({ label, value, icon: Icon, color }: { label: string; value: number; icon: any; color: string }) => (
    <div className="bg-gray-900/80 rounded-xl border border-white/5 p-5">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm text-gray-400">{label}</p>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
          color === 'red' ? 'bg-red-500/10 text-red-400' :
          color === 'yellow' ? 'bg-yellow-500/10 text-yellow-400' :
          color === 'green' ? 'bg-green-500/10 text-green-400' :
          'bg-blue-500/10 text-blue-400'
        }`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Compliance</h1>
        <p className="text-gray-400 mt-1">Compliance events and risk monitoring</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatBox label="Total Events" value={stats.total} icon={Shield} color="blue" />
        <StatBox label="Open Issues" value={stats.open} icon={AlertTriangle} color="red" />
        <StatBox label="Resolved Today" value={stats.resolvedToday} icon={CheckCircle} color="green" />
      </div>

      {error && (
        <div className="flex items-start gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-xl mb-6 text-sm text-red-300">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
        </div>
      )}

      {!loading && events.length === 0 && (
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No compliance events</h3>
          <p className="text-gray-500">All clear — no compliance events to review.</p>
        </div>
      )}

      {!loading && events.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Type</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Description</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Borrower</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Severity</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Status</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Created</th>
                  <th className="text-right px-5 py-3.5 font-semibold text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-4">
                      <span className="inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize bg-gray-800 text-gray-300">
                        {event.event_type?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-gray-300 max-w-xs truncate">{event.description}</td>
                    <td className="px-5 py-4 text-gray-400">
                      {event.borrower_name || <span className="text-gray-600">—</span>}
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize border ${SEVERITY_STYLES[event.severity] || SEVERITY_STYLES.info}`}>
                        {event.severity || 'info'}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize ${STATUS_STYLES[event.status] || 'text-gray-400 bg-gray-800'}`}>
                        {event.status?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-gray-500 text-xs">{formatDate(event.created_at)}</td>
                    <td className="px-5 py-4 text-right">
                      <span className="text-gray-500 text-xs">
                        {event.resolved_at ? `Resolved ${formatDate(event.resolved_at)}` : '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-white/5">
              <p className="text-sm text-gray-500">Page {pagination.page} of {pagination.total_pages} ({pagination.total_items} total)</p>
              <div className="flex items-center gap-2">
                <button onClick={() => setPage(1)} disabled={!pagination.has_previous} className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                  <ChevronsLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage(page - 1)} disabled={!pagination.has_previous} className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-gray-400 px-2">{pagination.page}</span>
                <button onClick={() => setPage(page + 1)} disabled={!pagination.has_next} className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                  <ChevronRight className="w-4 h-4" />
                </button>
                <button onClick={() => setPage(pagination.total_pages)} disabled={!pagination.has_next} className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all">
                  <ChevronsRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
