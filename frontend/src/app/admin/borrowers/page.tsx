'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { adminBorrowersApi, getApiErrorMessage, BorrowerListItem } from '@/src/lib/admin-api';
import type { PaginationMeta } from '@/src/types';
import {
  Users,
  ChevronRight,
  AlertCircle,
  Loader2,
  Search,
  ChevronLeft,
  ChevronsLeft,
  ChevronsRight,
  Shield,
  ShieldCheck,
  ShieldX,
} from 'lucide-react';

const KYC_BADGE: Record<string, { color: string; label: string }> = {
  verified: { color: 'text-green-400 bg-green-500/10', label: 'Verified' },
  pending: { color: 'text-yellow-400 bg-yellow-500/10', label: 'Pending' },
  not_started: { color: 'text-gray-400 bg-gray-800', label: 'Not Started' },
};

export default function AdminBorrowersPage() {
  const [borrowers, setBorrowers] = useState<BorrowerListItem[]>([]);
  const [pagination, setPagination] = useState<PaginationMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  const fetchBorrowers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = { page, page_size: 20 };
      if (searchQuery.trim()) params.search = searchQuery.trim();
      const { data } = await adminBorrowersApi.list(params);
      setBorrowers(data.data);
      setPagination(data.pagination);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery]);

  useEffect(() => { fetchBorrowers(); }, [fetchBorrowers]);
  useEffect(() => { setPage(1); }, [searchQuery]);

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Borrowers</h1>
          <p className="text-gray-400 mt-1">Manage borrower accounts and profiles</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name, email, or phone..."
            className="w-full pl-10 pr-4 py-2.5 bg-gray-900 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 transition-all text-sm"
          />
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

      {!loading && borrowers.length === 0 && (
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-12 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-800 flex items-center justify-center mx-auto mb-4">
            <Users className="w-8 h-8 text-gray-500" />
          </div>
          <h3 className="text-lg font-semibold text-gray-300 mb-2">No borrowers found</h3>
          <p className="text-gray-500">{searchQuery ? 'No borrowers match your search.' : 'No borrowers have registered yet.'}</p>
        </div>
      )}

      {!loading && borrowers.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Name</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Email</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Phone</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Credit Tier</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">KYC</th>
                  <th className="text-left px-5 py-3.5 font-semibold text-gray-300">Joined</th>
                  <th className="text-center px-5 py-3.5 font-semibold text-gray-300">Loans</th>
                  <th className="text-right px-5 py-3.5 font-semibold text-gray-300">Action</th>
                </tr>
              </thead>
              <tbody>
                {borrowers.map((b) => (
                  <tr key={b.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-4">
                      <span className="font-medium text-white">{b.first_name} {b.last_name}</span>
                    </td>
                    <td className="px-5 py-4 text-gray-300">{b.email}</td>
                    <td className="px-5 py-4 text-gray-400">{b.phone}</td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                        b.credit_tier
                          ? 'text-purple-400 bg-purple-500/10'
                          : 'text-gray-500 bg-gray-800'
                      }`}>
                        {b.credit_tier?.replace(/_/g, ' ') || '—'}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                        b.is_identity_verified ? 'text-green-400 bg-green-500/10' : 'text-yellow-400 bg-yellow-500/10'
                      }`}>
                        {b.is_identity_verified ? <ShieldCheck className="w-3 h-3" /> : <ShieldX className="w-3 h-3" />}
                        {b.is_identity_verified ? 'Verified' : 'Pending'}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-gray-500 text-xs">{formatDate(b.created_at)}</td>
                    <td className="px-5 py-4 text-center">
                      <span className="text-gray-300 font-medium">{b.loan_count}</span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        href={`/admin/borrowers/${b.id}`}
                        className="inline-flex items-center gap-1 text-orange-400 hover:text-orange-300 font-medium"
                      >
                        View <ChevronRight className="w-4 h-4" />
                      </Link>
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
