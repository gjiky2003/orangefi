'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { adminLoansApi, getApiErrorMessage } from '@/src/lib/admin-api';
import type { LoanListItem, PaginationMeta } from '@/src/types';
import {
  CreditCard,
  ChevronRight,
  AlertCircle,
  Loader2,
  Search,
  Filter,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react';

const LOAN_STATUS_STYLES: Record<string, { color: string; icon: any; label: string }> = {
  active: { color: 'text-green-400 bg-green-500/10', icon: TrendingUp, label: 'Active' },
  current: { color: 'text-green-400 bg-green-500/10', icon: TrendingUp, label: 'Current' },
  delinquent: { color: 'text-red-400 bg-red-500/10', icon: AlertTriangle, label: 'Delinquent' },
  paid_off: { color: 'text-emerald-400 bg-emerald-500/10', icon: CheckCircle, label: 'Paid Off' },
  charged_off: { color: 'text-gray-400 bg-gray-800', icon: XCircle, label: 'Charged Off' },
  defaulted: { color: 'text-red-400 bg-red-500/10', icon: XCircle, label: 'Defaulted' },
  processing: { color: 'text-blue-400 bg-blue-500/10', icon: Loader2, label: 'Processing' },
};

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'active', label: 'Active' },
  { value: 'delinquent', label: 'Delinquent' },
  { value: 'paid_off', label: 'Paid Off' },
  { value: 'charged_off', label: 'Charged Off' },
  { value: 'defaulted', label: 'Defaulted' },
  { value: 'processing', label: 'Processing' },
];

export default function AdminLoansPage() {
  const [loans, setLoans] = useState<LoanListItem[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  const fetchLoans = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { page, page_size: 20 };
      if (statusFilter) params.status = statusFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      const { data } = await adminLoansApi.list(params);
      setLoans(data.data);
      setPagination(data.pagination);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, searchQuery]);

  useEffect(() => { fetchLoans(); }, [fetchLoans]);
  useEffect(() => { setPage(1); }, [statusFilter, searchQuery]);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Loan Portfolio</h1>
          <p className="text-gray-400 mt-1">Manage and monitor all loans</p>
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
            placeholder="Search by ID..."
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

      {!loading && loans.length === 0 && (
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mx-auto mb-4">
            <CreditCard className="w-8 h-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No loans found</h3>
          <p className="text-gray-500">No loans match the current filters.</p>
        </div>
      )}

      {!loading && loans.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Loan ID</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Amount</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">APR</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Monthly Pmt</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Status</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Days Past Due</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Origination</th>
                  <th className="text-right px-5 py-3.5 font-semibold text-gray-300">Action</th>
                </tr>
              </thead>
              <tbody>
                {loans.map((loan) => {
                  const style = LOAN_STATUS_STYLES[loan.status] || LOAN_STATUS_STYLES.active;
                  const Icon = style.icon;
                  return (
                    <tr key={loan.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                      <td className="px-5 py-4">
                        <span className="font-mono text-xs text-gray-500">{loan.id.slice(0, 8)}...</span>
                      </td>
                      <td className="px-5 py-4 font-medium text-white">{formatCurrency(loan.loan_amount)}</td>
                      <td className="px-5 py-4 text-gray-300">{loan.apr}%</td>
                      <td className="px-5 py-4 text-gray-300">{formatCurrency(loan.monthly_payment)}</td>
                      <td className="px-5 py-4">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${style.color}`}>
                          <Icon className="w-3 h-3" />
                          {style.label}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <span className={loan.days_past_due > 0 ? 'text-red-400 font-medium' : 'text-gray-500'}>
                          {loan.days_past_due > 0 ? `${loan.days_past_due} days` : '—'}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-gray-500 text-xs">{formatDate(loan.origination_date)}</td>
                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/admin/loans/${loan.id}`}
                          className="inline-flex items-center gap-1 text-orange-400 hover:text-orange-300 font-medium"
                        >
                          View <ChevronRight className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {pagination && pagination.total_pages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-white/5">
              <p className="text-sm text-gray-500">
                Page {pagination.page} of {pagination.total_pages} ({pagination.total_items} total)
              </p>
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
