'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { adminApplicationsApi, getApiErrorMessage } from '@/src/lib/admin-api';
import type { ApplicationListItem, PaginationMeta } from '@/src/types';
import {
  FileText,
  ChevronRight,
  AlertCircle,
  Loader2,
  Search,
  Filter,
  ChevronLeft,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100/10 text-gray-400',
  submitted: 'bg-blue-500/10 text-blue-400',
  prequal_submitted: 'bg-blue-500/10 text-blue-400',
  prequal_completed: 'bg-cyan-500/10 text-cyan-400',
  application_started: 'bg-gray-100/10 text-gray-400',
  processing: 'bg-yellow-500/10 text-yellow-400',
  manual_review: 'bg-orange-500/10 text-orange-400',
  approved: 'bg-green-500/10 text-green-400',
  declined: 'bg-red-500/10 text-red-400',
  funded: 'bg-emerald-500/10 text-emerald-400',
  cancelled: 'bg-gray-500/10 text-gray-500',
};

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'processing', label: 'Processing' },
  { value: 'manual_review', label: 'Manual Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'declined', label: 'Declined' },
  { value: 'funded', label: 'Funded' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'draft', label: 'Draft' },
];

export default function AdminApplicationsPage() {
  const searchParams = useSearchParams();
  const [apps, setApps] = useState<ApplicationListItem[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || '');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  const fetchApps = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { page, page_size: 20 };
      if (statusFilter) params.status = statusFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      const { data } = await adminApplicationsApi.list(params);
      setApps(data.data);
      setPagination(data.pagination);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, searchQuery]);

  useEffect(() => {
    fetchApps();
  }, [fetchApps]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [statusFilter, searchQuery]);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Applications</h1>
          <p className="text-gray-400 mt-1">Review and process loan applications</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or ID..."
            className="w-full pl-10 pr-4 py-2.5 bg-gray-900 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 transition-all text-sm"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-10 pr-8 py-2.5 bg-gray-900 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 transition-all text-sm appearance-none cursor-pointer min-w-[160px]"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-gray-900">
                {opt.label}
              </option>
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

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
        </div>
      )}

      {/* Empty state */}
      {!loading && apps.length === 0 && (
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-8 h-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No applications found</h3>
          <p className="text-gray-500 mb-6 max-w-sm mx-auto">
            {statusFilter ? 'No applications match the current filter.' : 'No applications have been submitted yet.'}
          </p>
        </div>
      )}

      {/* Table */}
      {!loading && apps.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Application ID</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Borrower</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Amount</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Purpose</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Status</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Created</th>
                  <th className="text-right px-5 py-3.5 font-semibold text-gray-300">Action</th>
                </tr>
              </thead>
              <tbody>
                {apps.map((app) => (
                  <tr key={app.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-4">
                      <span className="font-mono text-xs text-gray-500">{app.id.slice(0, 8)}...</span>
                    </td>
                    <td className="px-5 py-4 font-medium text-white">{app.borrower_name}</td>
                    <td className="px-5 py-4 text-gray-300">{formatCurrency(app.requested_amount)}</td>
                    <td className="px-5 py-4 text-gray-400 capitalize max-w-[150px] truncate">
                      {app.loan_purpose?.replace(/_/g, ' ') || 'Personal'}
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize ${STATUS_COLORS[app.status] || 'bg-gray-100/10 text-gray-400'}`}>
                        {app.status?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-gray-500 text-xs">{formatDate(app.created_at)}</td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        href={`/admin/applications/${app.id}`}
                        className="inline-flex items-center gap-1 text-orange-400 hover:text-orange-300 font-medium"
                      >
                        Review <ChevronRight className="w-4 h-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-white/5">
              <p className="text-sm text-gray-500">
                Page {pagination.page} of {pagination.total_pages} ({pagination.total_items} total)
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(1)}
                  disabled={!pagination.has_previous}
                  className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronsLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={!pagination.has_previous}
                  className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-gray-400 px-2">{pagination.page}</span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={!pagination.has_next}
                  className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPage(pagination.total_pages)}
                  disabled={!pagination.has_next}
                  className="p-2 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
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
