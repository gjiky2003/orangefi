'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import AuthGuard from '@/src/components/AuthGuard';
import { loansApi, paymentsApi, getApiErrorMessage } from '@/src/lib/api';
import type { LoanDetail, PaymentScheduleItem } from '@/src/types';
import {
  ArrowLeft,
  CreditCard,
  Calendar,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Send,
} from 'lucide-react';

function LoanDetailContent() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [loan, setLoan] = useState<LoanDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [paymentAmount, setPaymentAmount] = useState<number>(0);
  const [paymentMethod, setPaymentMethod] = useState('ach');
  const [makingPayment, setMakingPayment] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [paymentSuccess, setPaymentSuccess] = useState<string | null>(null);
  const [showSchedule, setShowSchedule] = useState(false);

  useEffect(() => {
    const fetchLoan = async () => {
      try {
        const { data } = await loansApi.get(id);
        setLoan(data);
        setPaymentAmount(data.monthly_payment);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchLoan();
  }, [id]);

  const handleMakePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loan || paymentAmount <= 0) return;

    setMakingPayment(true);
    setPaymentError(null);
    setPaymentSuccess(null);

    try {
      const { data } = await paymentsApi.make({
        loan_id: loan.id,
        amount: paymentAmount,
        payment_method: paymentMethod,
        idempotency_key: `${loan.id}_${Date.now()}`,
      });
      setPaymentSuccess(`Payment of $${paymentAmount.toFixed(2)} is being processed. Reference: ${data.payment_id.slice(0, 8)}...`);
      // Refresh loan
      const refreshed = await loansApi.get(id);
      setLoan(refreshed.data);
    } catch (err) {
      setPaymentError(getApiErrorMessage(err));
    } finally {
      setMakingPayment(false);
    }
  };

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

  const statusConfig: Record<string, { color: string; label: string; icon: any }> = {
    active: { color: 'text-green-600 bg-green-100', label: 'Current', icon: TrendingUp },
    current: { color: 'text-green-600 bg-green-100', label: 'Current', icon: TrendingUp },
    delinquent: { color: 'text-red-600 bg-red-100', label: 'Delinquent', icon: AlertTriangle },
    paid_off: { color: 'text-emerald-600 bg-emerald-100', label: 'Paid Off', icon: CheckCircle },
    charged_off: { color: 'text-gray-600 bg-gray-100', label: 'Charged Off', icon: AlertCircle },
    defaulted: { color: 'text-red-700 bg-red-100', label: 'Defaulted', icon: AlertCircle },
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-orange-600 animate-spin" />
      </div>
    );
  }

  if (error || !loan) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-gray-700 font-medium mb-2">Failed to load loan</p>
          <p className="text-gray-500 text-sm mb-4">{error || 'Loan not found'}</p>
          <Link href="/loans" className="text-orange-600 hover:underline">
            Back to loans
          </Link>
        </div>
      </div>
    );
  }

  const statusStyle = statusConfig[loan.status] || statusConfig.active;
  const StatusIcon = statusStyle.icon;
  const isActive = loan.status === 'active' || loan.status === 'delinquent';

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back */}
        <Link
          href="/loans"
          className="inline-flex items-center gap-1.5 text-gray-500 hover:text-orange-600 text-sm mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Loans
        </Link>

        {/* Loan Summary Card */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div className="flex items-start gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${statusStyle.color}`}>
                <StatusIcon className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                  Loan Summary
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  ID: <span className="font-mono">{loan.id}</span>
                </p>
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium mt-2 ${statusStyle.color}`}>
                  <StatusIcon className="w-4 h-4" />
                  {statusStyle.label}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-xs text-gray-500 mb-1">Loan Amount</p>
              <p className="text-xl font-bold text-gray-900">{formatCurrency(loan.loan_amount)}</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-xs text-gray-500 mb-1">APR</p>
              <p className="text-xl font-bold text-orange-600">{loan.apr}%</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-xs text-gray-500 mb-1">Monthly Payment</p>
              <p className="text-xl font-bold text-gray-900">{formatCurrency(loan.monthly_payment)}</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-xs text-gray-500 mb-1">Term</p>
              <p className="text-xl font-bold text-gray-900">{loan.term_months} mo</p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
            <div>
              <p className="text-xs text-gray-500">Origination Fee</p>
              <p className="text-sm font-medium text-gray-700">{formatCurrency(loan.origination_fee)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Disbursed Amount</p>
              <p className="text-sm font-medium text-gray-700">{formatCurrency(loan.disbursement_amount)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Origination Date</p>
              <p className="text-sm font-medium text-gray-700">{formatDate(loan.origination_date)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Maturity Date</p>
              <p className="text-sm font-medium text-gray-700">{formatDate(loan.maturity_date)}</p>
            </div>
          </div>
        </div>

        {/* Make Payment Section */}
        {isActive && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-orange-600" />
              Make a Payment
            </h2>

            {paymentSuccess && (
              <div className="flex items-start gap-2 p-3 bg-green-50 text-green-700 rounded-xl text-sm mb-4">
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
                <span>{paymentSuccess}</span>
              </div>
            )}

            {paymentError && (
              <div className="flex items-start gap-2 p-3 bg-red-50 text-red-700 rounded-xl text-sm mb-4">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{paymentError}</span>
              </div>
            )}

            <form onSubmit={handleMakePayment} className="flex flex-col sm:flex-row gap-4 items-end">
              <div className="flex-1 w-full">
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Amount</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                  <input
                    type="number"
                    value={paymentAmount}
                    onChange={(e) => setPaymentAmount(Number(e.target.value))}
                    className="w-full pl-8 pr-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                    step="0.01"
                    min="0"
                    max={loan.total_amount_due || loan.loan_amount}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  Min: {formatCurrency(loan.monthly_payment)} &middot; Full balance: {formatCurrency(loan.total_amount_due || loan.loan_amount)}
                </p>
              </div>
              <div className="w-full sm:w-40">
                <label className="block text-sm font-medium text-gray-700 mb-1">Method</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                >
                  <option value="ach">ACH Transfer</option>
                  <option value="wire">Wire Transfer</option>
                  <option value="card">Debit Card</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={makingPayment || paymentAmount <= 0}
                className="flex items-center gap-2 px-6 py-2.5 bg-orange-600 text-white rounded-xl font-medium hover:bg-orange-700 transition-colors disabled:opacity-50 whitespace-nowrap"
              >
                {makingPayment ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Pay
                  </>
                )}
              </button>
            </form>
          </div>
        )}

        {/* Payoff Quote */}
        {isActive && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-6">
            <h2 className="font-semibold text-gray-900 mb-2">Payoff Quote</h2>
            <p className="text-sm text-gray-500 mb-4">
              Pay off your remaining balance early with no prepayment penalty.
            </p>
            <div className="bg-orange-50 rounded-xl p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600">Remaining Balance</p>
                <p className="text-xl font-bold text-gray-900">
                  {formatCurrency(loan.total_amount_due || loan.loan_amount)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-600">As of</p>
                <p className="text-sm font-medium text-gray-700">{formatDate(loan.updated_at)}</p>
              </div>
            </div>
          </div>
        )}

        {/* Amortization Schedule */}
        {loan.payment_schedule && loan.payment_schedule.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <button
              onClick={() => setShowSchedule(!showSchedule)}
              className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <h2 className="font-semibold text-gray-900">Amortization Schedule</h2>
              {showSchedule ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>

            {showSchedule && (
              <div className="border-t border-gray-100 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="text-left px-4 py-3 font-semibold text-gray-700">#</th>
                      <th className="text-left px-4 py-3 font-semibold text-gray-700">Due Date</th>
                      <th className="text-right px-4 py-3 font-semibold text-gray-700">Amount</th>
                      <th className="text-right px-4 py-3 font-semibold text-gray-700">Principal</th>
                      <th className="text-right px-4 py-3 font-semibold text-gray-700">Interest</th>
                      <th className="text-right px-4 py-3 font-semibold text-gray-700">Balance</th>
                      <th className="text-center px-4 py-3 font-semibold text-gray-700">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loan.payment_schedule.map((pmt: PaymentScheduleItem) => (
                      <tr
                        key={pmt.payment_number}
                        className="border-t border-gray-100 hover:bg-gray-50"
                      >
                        <td className="px-4 py-3 font-mono text-gray-500">{pmt.payment_number}</td>
                        <td className="px-4 py-3 text-gray-700">{formatDate(pmt.scheduled_date)}</td>
                        <td className="px-4 py-3 text-right font-medium text-gray-900">
                          {formatCurrency(pmt.total_amount)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">
                          {formatCurrency(pmt.principal_amount)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">
                          {formatCurrency(pmt.interest_amount)}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-500">
                          {pmt.remaining_balance !== null && pmt.remaining_balance !== undefined
                            ? formatCurrency(pmt.remaining_balance)
                            : '—'}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span
                            className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                              pmt.status === 'completed' || pmt.status === 'paid'
                                ? 'bg-green-100 text-green-700'
                                : pmt.status === 'failed'
                                ? 'bg-red-100 text-red-700'
                                : pmt.status === 'scheduled'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-gray-100 text-gray-600'
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
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function LoanDetailPage() {
  return (
    <AuthGuard>
      <LoanDetailContent />
    </AuthGuard>
  );
}
