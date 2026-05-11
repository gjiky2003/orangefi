'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AuthGuard from '@/src/components/AuthGuard';
import { loansApi, getApiErrorMessage } from '@/src/lib/api';
import type { LoanListItem } from '@/src/types';
import {
  CreditCard,
  ChevronRight,
  AlertCircle,
  Loader2,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';

const LOAN_STATUS_STYLES: Record<string, { color: string; icon: any; label: string }> = {
  active: { color: 'text-green-600 bg-green-100', icon: TrendingUp, label: 'Current' },
  current: { color: 'text-green-600 bg-green-100', icon: TrendingUp, label: 'Current' },
  delinquent: { color: 'text-red-600 bg-red-100', icon: AlertTriangle, label: 'Delinquent' },
  paid_off: { color: 'text-emerald-600 bg-emerald-100', icon: CheckCircle, label: 'Paid Off' },
  charged_off: { color: 'text-gray-600 bg-gray-100', icon: XCircle, label: 'Charged Off' },
  defaulted: { color: 'text-red-700 bg-red-100', icon: XCircle, label: 'Defaulted' },
  processing: { color: 'text-blue-600 bg-blue-100', icon: Loader2, label: 'Processing' },
};

function LoansContent() {
  const [loans, setLoans] = useState<LoanListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    const fetchLoans = async () => {
      try {
        const params: Record<string, any> = { page: 1, page_size: 50 };
        if (statusFilter) params.status = statusFilter;
        const { data } = await loansApi.list(params);
        setLoans(data.data);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetchLoans();
  }, [statusFilter]);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

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
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Your Loans</h1>
          <p className="text-gray-600 mt-1">View and manage your active and past loans.</p>
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
          {['active', 'delinquent', 'paid_off'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize whitespace-nowrap transition-colors ${
                statusFilter === s ? 'bg-orange-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:border-orange-200'
              }`}
            >
              {s.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        {error && (
          <div className="flex items-start gap-2 p-4 bg-red-50 text-red-700 rounded-xl mb-6 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {loans.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
            <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-4">
              <CreditCard className="w-8 h-8 text-orange-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No loans yet</h3>
            <p className="text-gray-500 mb-6 max-w-sm mx-auto">
              Once your application is approved and funded, your loan will appear here.
            </p>
            <Link
              href="/pre-qualify"
              className="inline-flex items-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-xl font-medium hover:bg-orange-700 transition-colors"
            >
              Apply for a Loan
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {loans.map((loan) => {
              const style = LOAN_STATUS_STYLES[loan.status] || LOAN_STATUS_STYLES.active;
              const StatusIcon = style.icon;

              // Calculate remaining balance approximation
              const progress = loan.loan_amount > 0
                ? Math.min(100, Math.round(((loan.loan_amount - (loan.total_amount_due || 0)) / loan.loan_amount) * 100))
                : 0;

              return (
                <Link
                  key={loan.id}
                  href={`/loans/${loan.id}`}
                  className="bg-white rounded-xl border border-gray-200 p-5 hover:border-orange-200 hover:shadow-md transition-all"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${style.color}`}>
                        <StatusIcon className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-gray-900">
                            {formatCurrency(loan.loan_amount)}
                          </h3>
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${style.color}`}>
                            <StatusIcon className="w-3 h-3" />
                            {style.label}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
                          <span>{loan.apr}% APR</span>
                          <span>{formatCurrency(loan.monthly_payment)}/mo</span>
                          <span>{loan.term_months} mo term</span>
                        </div>
                        {/* Progress bar */}
                        <div className="mt-3 w-full max-w-xs">
                          <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>Remaining: {formatCurrency(loan.total_amount_due || loan.loan_amount)}</span>
                            <span>Of {formatCurrency(loan.loan_amount)}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-orange-500 h-2 rounded-full transition-all"
                              style={{ width: `${100 - progress}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 sm:flex-shrink-0">
                      <div className="text-right hidden sm:block">
                        <p className="text-xs text-gray-400">Originated</p>
                        <p className="text-sm text-gray-600">{formatDate(loan.origination_date)}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function LoansPage() {
  return (
    <AuthGuard>
      <LoansContent />
    </AuthGuard>
  );
}
