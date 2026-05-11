'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { adminLoansApi, getApiErrorMessage } from '@/src/lib/admin-api';
import type { LoanDetail } from '@/src/types';
import {
  ArrowLeft,
  CreditCard,
  Calendar,
  DollarSign,
  AlertCircle,
  Loader2,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  User,
  FileText,
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

export default function AdminLoanDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [loan, setLoan] = useState<LoanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLoan = async () => {
      try {
        const { data } = await adminLoansApi.get(id);
        setLoan(data);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchLoan();
  }, [id]);

  const formatCurrency = (val: number | null) => {
    if (val === null || val === undefined) return '—';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  };

  const formatPercent = (val: number) => `${val.toFixed(2)}%`;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
      </div>
    );
  }

  if (error || !loan) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-gray-300 font-medium mb-2">Failed to load loan</p>
          <p className="text-gray-500 text-sm mb-4">{error || 'Loan not found'}</p>
          <Link href="/admin/loans" className="text-orange-400 hover:underline">Back to loans</Link>
        </div>
      </div>
    );
  }

  const style = LOAN_STATUS_STYLES[loan.status] || LOAN_STATUS_STYLES.active;
  const StatusIcon = style.icon;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto">
      <Link href="/admin/loans" className="inline-flex items-center gap-1.5 text-gray-400 hover:text-orange-400 text-sm mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Back to Loans
      </Link>

      {/* Header */}
      <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 p-6 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${style.color}`}>
              <StatusIcon className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-white">Loan Details</h1>
              <p className="text-sm text-gray-400 mt-1">ID: <span className="font-mono">{loan.id}</span></p>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium mt-2 ${style.color}`}>
                <StatusIcon className="w-4 h-4" />
                {style.label}
              </span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-white">{formatCurrency(loan.loan_amount)}</p>
            <p className="text-sm text-gray-400">{loan.apr}% APR &middot; {loan.term_months} months</p>
          </div>
        </div>

        {/* Delinquency alert */}
        {loan.days_past_due > 0 && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-xl mt-4">
            <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <span className="text-sm text-red-300">
              This loan is <strong>{loan.days_past_due} days past due</strong>
              {loan.collections_status && ` — Collections status: ${loan.collections_status.replace(/_/g, ' ')}`}
            </span>
          </div>
        )}
        {loan.charge_off_reason && (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-xl mt-4">
            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <span className="text-sm text-red-300">Charge-off reason: {loan.charge_off_reason}</span>
          </div>
        )}
      </div>

      {/* Loan Info Grid */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-green-400" />
            <h2 className="font-semibold text-white">Loan Information</h2>
          </div>
          <div className="p-5 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Loan Amount</span>
              <span className="font-semibold text-white">{formatCurrency(loan.loan_amount)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Disbursement Amount</span>
              <span className="font-semibold text-white">{formatCurrency(loan.disbursement_amount)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Origination Fee</span>
              <span className="font-semibold text-white">{formatCurrency(loan.origination_fee)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">APR</span>
              <span className="font-semibold text-white">{formatPercent(loan.apr)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Interest Rate Type</span>
              <span className="font-semibold text-white capitalize">{loan.interest_rate_type}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Term</span>
              <span className="font-semibold text-white">{loan.term_months} months</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Monthly Payment</span>
              <span className="font-semibold text-white">{formatCurrency(loan.monthly_payment)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Interest Accrued</span>
              <span className="font-semibold text-white">{formatCurrency(loan.interest_accrued)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Total Amount Due</span>
              <span className="font-semibold text-white">{formatCurrency(loan.total_amount_due)}</span>
            </div>
          </div>
        </div>

        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-400" />
            <h2 className="font-semibold text-white">Dates & Status</h2>
          </div>
          <div className="p-5 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Origination Date</span>
              <span className="font-medium text-white">{formatDate(loan.origination_date)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">First Payment Date</span>
              <span className="font-medium text-white">{formatDate(loan.first_payment_date)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Maturity Date</span>
              <span className="font-medium text-white">{formatDate(loan.maturity_date)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Days Past Due</span>
              <span className={`font-medium ${loan.days_past_due > 0 ? 'text-red-400' : 'text-white'}`}>
                {loan.days_past_due > 0 ? `${loan.days_past_due} days` : 'Current'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Collections Status</span>
              <span className="font-medium text-white capitalize">{loan.collections_status?.replace(/_/g, ' ') || 'None'}</span>
            </div>
            {loan.paid_off_at && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Paid Off At</span>
                <span className="font-medium text-green-400">{formatDate(loan.paid_off_at)}</span>
              </div>
            )}
            {loan.delinquency_started_at && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Delinquency Started</span>
                <span className="font-medium text-red-400">{formatDate(loan.delinquency_started_at)}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Payment Schedule */}
      {loan.payment_schedule && loan.payment_schedule.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 mb-6">
          <div className="px-5 py-4 border-b border-white/5">
            <h2 className="font-semibold text-white">Payment Schedule</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">#</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Scheduled Date</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Total</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Principal</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Interest</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Balance</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Status</th>
                </tr>
              </thead>
              <tbody>
                {loan.payment_schedule.map((pmt) => (
                  <tr key={pmt.payment_number} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-3 text-gray-400">{pmt.payment_number}</td>
                    <td className="px-5 py-3 text-gray-300">{formatDate(pmt.scheduled_date)}</td>
                    <td className="px-5 py-3 text-white">{formatCurrency(pmt.total_amount)}</td>
                    <td className="px-5 py-3 text-gray-300">{formatCurrency(pmt.principal_amount)}</td>
                    <td className="px-5 py-3 text-gray-300">{formatCurrency(pmt.interest_amount)}</td>
                    <td className="px-5 py-3 text-gray-400">{formatCurrency(pmt.remaining_balance)}</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium capitalize ${
                        pmt.status === 'completed' || pmt.status === 'paid'
                          ? 'text-green-400 bg-green-500/10'
                          : pmt.status === 'due' || pmt.status === 'scheduled'
                          ? 'text-yellow-400 bg-yellow-500/10'
                          : pmt.status === 'overdue'
                          ? 'text-red-400 bg-red-500/10'
                          : 'text-gray-400 bg-gray-800'
                      }`}>
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

      {/* Payment History */}
      {loan.recent_payments && loan.recent_payments.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 mb-6">
          <div className="px-5 py-4 border-b border-white/5">
            <h2 className="font-semibold text-white">Payment History</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">#</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Scheduled</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Paid Date</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Amount</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Amount Paid</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Method</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Status</th>
                </tr>
              </thead>
              <tbody>
                {loan.recent_payments.map((pmt) => (
                  <tr key={pmt.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-3 text-gray-400">{pmt.payment_number}</td>
                    <td className="px-5 py-3 text-gray-300">{formatDate(pmt.scheduled_date)}</td>
                    <td className="px-5 py-3 text-gray-300">{formatDate(pmt.paid_date)}</td>
                    <td className="px-5 py-3 text-white">{formatCurrency(pmt.total_amount)}</td>
                    <td className="px-5 py-3 text-gray-300">{formatCurrency(pmt.amount_paid)}</td>
                    <td className="px-5 py-3 text-gray-400 capitalize">{pmt.payment_method?.replace(/_/g, ' ') || '—'}</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium capitalize ${
                        pmt.status === 'completed' || pmt.status === 'paid'
                          ? 'text-green-400 bg-green-500/10'
                          : pmt.status === 'failed'
                          ? 'text-red-400 bg-red-500/10'
                          : pmt.status === 'processing'
                          ? 'text-yellow-400 bg-yellow-500/10'
                          : 'text-gray-400 bg-gray-800'
                      }`}>
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
  );
}
