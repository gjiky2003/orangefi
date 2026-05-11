'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { adminAuditLogApi, getApiErrorMessage, AuditLogEntry } from '@/src/lib/admin-api';
import type { PaginationMeta } from '@/src/types';
import {
  ScrollText,
  AlertCircle,
  Loader2,
  Search,
  Filter,
  ChevronLeft,
  ChevronsLeft,
  ChevronsRight,
  ChevronRight,
  Activity,
  Calendar,
} from 'lucide-react';

const ACTION_OPTIONS = [
  { value: '', label: 'All Actions' },
  { value: 'login', label: 'Login' },
  { value: 'logout', label: 'Logout' },
  { value: 'create', label: 'Create' },
  { value: 'update', label: 'Update' },
  { value: 'delete', label: 'Delete' },
  { value: 'decision', label: 'Decision' },
  { value: 'approve', label: 'Approve' },
  { value: 'decline', label: 'Decline' },
  { value: 'view', label: 'View' },
  { value: 'export', label: 'Export' },
];

export default function AdminAuditLogPage() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionFilter, setActionFilter] = useState('');
  const [actorFilter, setActorFilter] = useState('');
  const [page, setPage] = useState(1);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { page, page_size: 30 };
      if (actionFilter) params.action = actionFilter;
      if (actorFilter.trim()) params.actor = actorFilter.trim();
      const { data } = await adminAuditLogApi.list(params);
      setEntries(data.data);
      setPagination(data.pagination);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, actionFilter, actorFilter]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);
  useEffect(() => { setPage(1); }, [actionFilter, actorFilter]);

  const formatDateTime = (ts: string) => {
    const d = new Date(ts);
    return d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Audit Log</h1>
        <p className="text-gray-400 mt-1">Track all administrative actions and system events</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={actorFilter}
            onChange={(e) => setActorFilter(e.target.value)}
            placeholder="Search by actor..."
            className="w-full pl-10 pr-4 py-2.5 bg-gray-900 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 transition-all text-sm"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="pl-10 pr-8 py-2.5 bg-gray-900 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 transition-all text-sm appearance-none cursor-pointer min-w-[160px]"
          >
            {ACTION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-gray-900">{opt.label}</option>
            ))}
          </select>
        </div>
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

      {!loading && entries.length === 0 && (
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mx-auto mb-4">
            <ScrollText className="w-8 h-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No audit log entries</h3>
          <p className="text-gray-500">No entries match the current filters.</p>
        </div>
      )}

      {!loading && entries.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Timestamp</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Actor</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Action</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Resource</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Description</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">IP Address</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-4 text-gray-300 text-xs whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3 h-3 text-gray-500" />
                        {formatDateTime(entry.timestamp)}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="font-medium text-white">{entry.actor}</span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                        entry.action === 'login' || entry.action === 'logout' ? 'text-blue-400 bg-blue-500/10' :
                        entry.action === 'create' ? 'text-green-400 bg-green-500/10' :
                        entry.action === 'update' ? 'text-yellow-400 bg-yellow-500/10' :
                        entry.action === 'delete' ? 'text-red-400 bg-red-500/10' :
                        entry.action === 'decision' || entry.action === 'approve' ? 'text-orange-400 bg-orange-500/10' :
                        'text-gray-400 bg-gray-800'
                      }`}>
                        {entry.action}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-gray-300">
                        {entry.resource_type}
                        {entry.resource_id && (
                          <span className="text-gray-500 font-mono text-xs ml-1">({entry.resource_id.slice(0, 8)}...)</span>
                        )}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-gray-400 max-w-xs truncate">{entry.description || '—'}</td>
                    <td className="px-5 py-4 text-gray-500 text-xs font-mono">{entry.ip_address || '—'}</td>
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
