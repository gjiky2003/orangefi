'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AuthGuard from '@/src/components/AuthGuard';
import { paymentsApi, getApiErrorMessage } from '@/src/lib/api';
import type { PaymentListItem } from '@/src/types';
import {
  DollarSign,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Search,
  Calendar,
  Filter,
} from 'lucide-react';

const PAYMENT_STATUS_STYLES: Record<string, string> = {
  scheduled: 'bg-blue-100 text-blue-700',
  processing: 'bg-yellow-100 text-yellow-700',
  completed: 'bg-green-100 text-green-700',
  paid: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  refunded: 'bg-purple-100 text-purple-700',
  cancelled: 'bg-gray-100 text-gray-500',
};

function PaymentsContent() {
  const [payments, setPayments] = useState<PaymentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  useEffect(() => {
    const fetchPayments = async () => {
      setLoading(true);
      try {
        const params: Record<string, any> = { page: 1, page_size: 100 };
        if (statusFilter) params.status = statusFilter;
        const { data } = await paymentsApi.list(params);
        let filtered = data.data;

        // Client-side date filtering
        if (dateFrom) {
          const from = new Date(dateFrom).getTime();
          filtered = filtered.filter((p) => new Date(p.scheduled_date).getTime() >= from);
        }
        if (dateTo) {
          const to = new Date(dateTo).getTime() + 86400000; // end of day
          filtered = filtered.filter((p) => new Date(p.scheduled_date).getTime() <= to);
        }

        setPayments(filtered);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetchPayments();
  }, [statusFilter, dateFrom, dateTo]);

  const formatCurrency = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '—';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const totalPaid = payments
    .filter((p) => p.status === 'completed')
    .reduce((sum, p) => sum + (p.amount_paid || p.total_amount), 0);

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
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Payment History</h1>
          <p className="text-gray-600 mt-1">View all your payments and their status.</p>
        </div>

        {/* Summary */}
        {payments.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
              <p className="text-sm text-gray-500 mb-1">Total Payments</p>
              <p className="text-2xl font-bold text-gray-900">{payments.length}</p>
            </div>
            <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
              <p className="text-sm text-gray-500 mb-1">Total Paid</p>
              <p className="text-2xl font-bold text-green-600">{formatCurrency(totalPaid)}</p>
            </div>
            <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
              <p className="text-sm text-gray-500 mb-1">Completed</p>
              <p className="text-2xl font-bold text-gray-900">
                {payments.filter((p) => p.status === 'completed').length}
              </p>
            </div>
          </div>
        )}

        {/* Filters Toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-4 transition-colors"
        >
          <Filter className="w-4 h-4" />
          Filters
          {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showFilters && (
          <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 flex flex-wrap gap-4 items-end">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none"
              >
                <option value="">All Statuses</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
                <option value="scheduled">Scheduled</option>
                <option value="failed">Failed</option>
                <option value="refunded">Refunded</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">From Date</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">To Date</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-orange-500 outline-none"
              />
            </div>
            {(dateFrom || dateTo || statusFilter) && (
              <button
                onClick={() => {
                  setStatusFilter('');
                  setDateFrom('');
                  setDateTo('');
                }}
                className="px-3 py-2 text-sm text-red-600 hover:text-red-700"
              >
                Clear
              </button>
            )}
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2 p-4 bg-red-50 text-red-700 rounded-xl mb-6 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {payments.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-4">
              <DollarSign className="w-8 h-8 text-orange-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No payments found</h3>
            <p className="text-gray-500 mb-6 max-w-sm mx-auto">
              Payments will appear here once you make your first payment on an active loan.
            </p>
            <Link
              href="/loans"
              className="inline-flex items-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-xl font-medium hover:bg-orange-700 transition-colors"
            >
              View Your Loans
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left px-5 py-3 font-semibold text-gray-700">#</th>
                    <th className="text-left px-5 py-3 font-semibold text-gray-700">Date</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-700">Amount</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-700">Principal</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-700">Interest</th>
                    <th className="text-right px-5 py-3 font-semibold text-gray-700">Fees</th>
                    <th className="text-center px-5 py-3 font-semibold text-gray-700">Method</th>
                    <th className="text-center px-5 py-3 font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {payments.map((pmt) => (
                    <tr key={pmt.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="px-5 py-4 font-mono text-xs text-gray-500">
                        {pmt.payment_number}
                      </td>
                      <td className="px-5 py-4 text-gray-700 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-gray-400" />
                          {formatDate(pmt.paid_date || pmt.scheduled_date)}
                        </div>
                      </td>
                      <td className="px-5 py-4 text-right font-medium text-gray-900">
                        {formatCurrency(pmt.total_amount)}
                      </td>
                      <td className="px-5 py-4 text-right text-gray-700">
                        {formatCurrency(pmt.principal_amount)}
                      </td>
                      <td className="px-5 py-4 text-right text-gray-700">
                        {formatCurrency(pmt.interest_amount)}
                      </td>
                      <td className="px-5 py-4 text-right text-gray-500">
                        {formatCurrency(pmt.fees_amount || null)}
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span className="text-xs text-gray-500 capitalize">
                          {pmt.payment_method || '—'}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-center">
                        <span
                          className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium capitalize ${
                            PAYMENT_STATUS_STYLES[pmt.status] || 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {pmt.status}
                        </span>
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

export default function PaymentsPage() {
  return (
    <AuthGuard>
      <PaymentsContent />
    </AuthGuard>
  );
}
