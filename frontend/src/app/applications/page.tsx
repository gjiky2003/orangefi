'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AuthGuard from '@/src/components/AuthGuard';
import { applicationsApi, getApiErrorMessage } from '@/src/lib/api';
import type { ApplicationListItem } from '@/src/types';
import {
  FileText,
  Plus,
  ChevronRight,
  AlertCircle,
  Loader2,
  Search,
} from 'lucide-react';

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  submitted: 'bg-blue-100 text-blue-700',
  prequal_submitted: 'bg-blue-100 text-blue-700',
  prequal_completed: 'bg-cyan-100 text-cyan-700',
  application_started: 'bg-gray-100 text-gray-700',
  processing: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
  declined: 'bg-red-100 text-red-700',
  funded: 'bg-emerald-100 text-emerald-700',
  cancelled: 'bg-gray-100 text-gray-500',
};

function ApplicationsContent() {
  const [apps, setApps] = useState<ApplicationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    const fetchApps = async () => {
      try {
        const params: Record<string, any> = { page: 1, page_size: 50 };
        if (statusFilter) params.status = statusFilter;
        const { data } = await applicationsApi.list(params);
        setApps(data.data);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetchApps();
  }, [statusFilter]);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-orange-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Applications</h1>
            <p className="text-gray-600 mt-1">Track and manage your loan applications.</p>
          </div>
          <Link
            href="/pre-qualify"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-orange-600 text-white rounded-xl font-medium hover:bg-orange-700 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New Application
          </Link>
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          <button
            onClick={() => setStatusFilter('')}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              !statusFilter ? 'bg-orange-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-orange-200'
            }`}
          >
            All
          </button>
          {['submitted', 'processing', 'approved', 'declined', 'funded', 'draft'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize whitespace-nowrap transition-colors ${
                statusFilter === s ? 'bg-orange-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-orange-200'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {error && (
          <div className="flex items-start gap-2 p-4 bg-red-50 text-red-700 rounded-xl mb-6 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Table */}
        {apps.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-orange-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No applications yet</h3>
            <p className="text-gray-500 mb-6 max-w-sm mx-auto">
              Start by checking your rate — it only takes a few minutes and won&apos;t affect your credit.
            </p>
            <Link
              href="/pre-qualify"
              className="inline-flex items-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-xl font-medium hover:bg-orange-700 transition-colors"
            >
              Check Your Rate
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-5 py-3 font-semibold text-gray-700">ID</th>
                    <th className="text-left px-5 py-3 font-semibold text-gray-700">Amount</th>
                    <th className="text-left px-5 py-3 font-semibold text-gray-700">Term</th>
                    <th className="text-left px-5 py-3 font-semibold text-gray-700">Purpose</th>
                    <th className="text-left px-5 py-3 font-semibold text-gray-700">Status</th>
                    <th className="text-left px-5 py-3 font-semibold text-gray-700">Created</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {apps.map((app) => (
                    <tr key={app.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="px-5 py-4 font-mono text-xs text-gray-500">
                        {app.id.slice(0, 8)}...
                      </td>
                      <td className="px-5 py-4 font-medium text-gray-900">
                        {formatCurrency(app.requested_amount)}
                      </td>
                      <td className="px-5 py-4 text-gray-600">{app.requested_term_months} mo</td>
                      <td className="px-5 py-4 text-gray-600 capitalize max-w-[150px] truncate">
                        {app.loan_purpose?.replace(/_/g, ' ') || 'Personal'}
                      </td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                            STATUS_COLORS[app.status] || 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {app.status}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-gray-500 text-xs">
                        {formatDate(app.created_at)}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/applications/${app.id}`}
                          className="inline-flex items-center gap-1 text-orange-600 hover:text-orange-700 font-medium"
                        >
                          View
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ApplicationsPage() {
  return (
    <AuthGuard>
      <ApplicationsContent />
    </AuthGuard>
  );
}
