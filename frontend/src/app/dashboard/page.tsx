'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import AuthGuard from '@/src/components/AuthGuard';
import { useAuth } from '@/src/lib/auth-context';
import { applicationsApi, loansApi, paymentsApi } from '@/src/lib/api';
import type { ApplicationListItem, LoanListItem, PaymentListItem } from '@/src/types';
import {
  Wallet,
  CreditCard,
  Calendar,
  ArrowRight,
  TrendingUp,
  PiggyBank,
  FileText,
  DollarSign,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';

function DashboardContent() {
  const { user } = useAuth();
  const [applications, setApplications] = useState<ApplicationListItem[]>([]);
  const [loans, setLoans] = useState<LoanListItem[]>([]);
  const [recentPayments, setRecentPayments] = useState<PaymentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [appsRes, loansRes, paymentsRes] = await Promise.all([
          applicationsApi.list({ page: 1, page_size: 5 }),
          loansApi.list({ page: 1, page_size: 5 }),
          paymentsApi.list({ page: 1, page_size: 5 }),
        ]);
        setApplications(appsRes.data.data);
        setLoans(loansRes.data.data);
        setRecentPayments(paymentsRes.data.data);
      } catch (err: any) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Find active loan and next payment
  const activeLoan = loans.find(
    (l) => l.status === 'active' || l.status === 'delinquent'
  );
  const nextPayment = activeLoan
    ? {
        amount: activeLoan.monthly_payment,
        date: activeLoan.first_payment_date || activeLoan.maturity_date,
      }
    : null;

  const latestApplication = applications[0];

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-orange-600 animate-spin" />
          <p className="text-sm text-gray-500">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Welcome back{user?.first_name ? `, ${user.first_name}` : ''}!
          </h1>
          <p className="text-gray-600 mt-1">Here&apos;s an overview of your finances.</p>
        </div>

        {error && (
          <div className="flex items-start gap-2 p-4 bg-yellow-50 text-yellow-700 rounded-xl mb-6 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Overview Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-gray-500">Active Loan Balance</p>
              <div className="w-9 h-9 rounded-lg bg-orange-100 flex items-center justify-center">
                <Wallet className="w-5 h-5 text-orange-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {activeLoan ? formatCurrency(activeLoan.loan_amount) : '$0.00'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {activeLoan ? `${activeLoan.term_months} mo term` : 'No active loans'}
            </p>
          </div>

          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-gray-500">Next Payment</p>
              <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {nextPayment ? formatCurrency(nextPayment.amount) : '$0.00'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {nextPayment ? `Due ${formatDate(nextPayment.date)}` : 'No payments due'}
            </p>
          </div>

          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-gray-500">Loan Status</p>
              <div className="w-9 h-9 rounded-lg bg-green-100 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
            </div>
            {activeLoan ? (
              <>
                <p className="text-2xl font-bold text-green-600 capitalize">{activeLoan.status}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {activeLoan.apr}% APR &middot; {formatCurrency(activeLoan.monthly_payment)}/mo
                </p>
              </>
            ) : (
              <>
                <p className="text-2xl font-bold text-gray-400">No Loan</p>
                <p className="text-xs text-gray-400 mt-1">Ready to apply?</p>
              </>
            )}
          </div>

          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-gray-500">Applications</p>
              <div className="w-9 h-9 rounded-lg bg-purple-100 flex items-center justify-center">
                <FileText className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <p className="text-2xl font-bold text-gray-900">{applications.length}</p>
            <p className="text-xs text-gray-400 mt-1">
              {latestApplication
                ? `Last: ${latestApplication.status}`
                : 'No applications yet'}
            </p>
          </div>
        </div>

        {!activeLoan && !latestApplication && (
          /* Ready to consolidate? card */
          <div className="bg-gradient-to-r from-orange-500 to-orange-700 rounded-2xl p-8 mb-8 text-white shadow-lg">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <PiggyBank className="w-6 h-6" />
                  <h2 className="text-xl font-bold">Ready to Consolidate?</h2>
                </div>
                <p className="text-orange-100">
                  Lower your credit card rate and save money. Check your rate in minutes with no impact to your credit.
                </p>
              </div>
              <Link
                href="/pre-qualify"
                className="flex items-center gap-2 px-6 py-3 bg-white text-orange-700 rounded-xl font-semibold hover:bg-orange-50 transition-colors whitespace-nowrap shadow-md"
              >
                Apply Now
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        )}

        {/* Two column layout */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Recent Activity</h2>
              <Link href="/applications" className="text-sm text-orange-600 hover:text-orange-700 font-medium">
                View all
              </Link>
            </div>
            <div className="p-5">
              {applications.length === 0 && recentPayments.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-3">
                    <FileText className="w-6 h-6 text-gray-400" />
                  </div>
                  <p className="text-gray-500 text-sm">No recent activity</p>
                  <Link
                    href="/pre-qualify"
                    className="text-orange-600 text-sm font-medium hover:underline mt-1 inline-block"
                  >
                    Start your first application
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {applications.slice(0, 3).map((app) => (
                    <Link
                      key={app.id}
                      href={`/applications/${app.id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                            app.status === 'approved' || app.status === 'funded'
                              ? 'bg-green-100'
                              : app.status === 'declined'
                              ? 'bg-red-100'
                              : 'bg-orange-100'
                          }`}
                        >
                          <FileText
                            className={`w-4 h-4 ${
                              app.status === 'approved' || app.status === 'funded'
                                ? 'text-green-600'
                                : app.status === 'declined'
                                ? 'text-red-600'
                                : 'text-orange-600'
                            }`}
                          />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Loan Application
                          </p>
                          <p className="text-xs text-gray-500 capitalize">{app.status}</p>
                        </div>
                      </div>
                      <span className="text-sm text-gray-500">
                        {formatCurrency(app.requested_amount)}
                      </span>
                    </Link>
                  ))}
                  {recentPayments.slice(0, 3).map((pmt) => (
                    <div
                      key={pmt.id}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
                          <DollarSign className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Payment
                          </p>
                          <p className="text-xs text-gray-500 capitalize">{pmt.status}</p>
                        </div>
                      </div>
                      <span className="text-sm text-gray-500">
                        {formatCurrency(pmt.total_amount)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Quick Actions</h2>
            </div>
            <div className="p-5 space-y-3">
              <Link
                href={activeLoan ? `/loans/${activeLoan.id}` : '/pre-qualify'}
                className="flex items-center gap-4 p-4 rounded-xl border border-gray-200 hover:border-orange-200 hover:bg-orange-50/50 transition-all"
              >
                <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-orange-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Make a Payment</p>
                  <p className="text-sm text-gray-500">
                    {activeLoan ? 'Pay your monthly bill' : 'Apply for a loan first'}
                  </p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </Link>

              <Link
                href="/pre-qualify"
                className="flex items-center gap-4 p-4 rounded-xl border border-gray-200 hover:border-orange-200 hover:bg-orange-50/50 transition-all"
              >
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Apply for a Loan</p>
                  <p className="text-sm text-gray-500">Check your rate and apply</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </Link>

              <Link
                href="/payments"
                className="flex items-center gap-4 p-4 rounded-xl border border-gray-200 hover:border-orange-200 hover:bg-orange-50/50 transition-all"
              >
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <CreditCard className="w-5 h-5 text-purple-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">Payment History</p>
                  <p className="text-sm text-gray-500">View all past payments</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardContent />
    </AuthGuard>
  );
}
