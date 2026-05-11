'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import AuthGuard from '@/src/components/AuthGuard';
import { applicationsApi, getApiErrorMessage } from '@/src/lib/api';
import type { ApplicationDetail } from '@/src/types';
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Loader2,
  Calendar,
  DollarSign,
  User,
  TrendingUp,
  Shield,
} from 'lucide-react';

const STATUS_CONFIG: Record<string, { color: string; icon: any; label: string }> = {
  draft: { color: 'text-gray-600 bg-gray-100', icon: FileText, label: 'Draft' },
  submitted: { color: 'text-blue-600 bg-blue-100', icon: Clock, label: 'Submitted' },
  prequal_submitted: { color: 'text-blue-600 bg-blue-100', icon: Clock, label: 'Pre-Qual Submitted' },
  prequal_completed: { color: 'text-cyan-600 bg-cyan-100', icon: CheckCircle, label: 'Pre-Qual Completed' },
  application_started: { color: 'text-gray-600 bg-gray-100', icon: FileText, label: 'Started' },
  processing: { color: 'text-yellow-600 bg-yellow-100', icon: Clock, label: 'Processing' },
  approved: { color: 'text-green-600 bg-green-100', icon: CheckCircle, label: 'Approved' },
  declined: { color: 'text-red-600 bg-red-100', icon: XCircle, label: 'Declined' },
  funded: { color: 'text-emerald-600 bg-emerald-100', icon: CheckCircle, label: 'Funded' },
  cancelled: { color: 'text-gray-500 bg-gray-100', icon: XCircle, label: 'Cancelled' },
};

function ApplicationDetailContent() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [app, setApp] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [withdrawing, setWithdrawing] = useState(false);

  useEffect(() => {
    const fetchApp = async () => {
      try {
        const { data } = await applicationsApi.get(id);
        setApp(data);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchApp();
  }, [id]);

  const handleWithdraw = async () => {
    if (!confirm('Are you sure you want to withdraw this application?')) return;
    setWithdrawing(true);
    try {
      await applicationsApi.withdraw(id);
      // Refresh
      const { data } = await applicationsApi.get(id);
      setApp(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setWithdrawing(false);
    }
  };

  const formatCurrency = (val: number | null) => {
    if (val === null || val === undefined) return '—';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'long',
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

  if (error || !app) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-gray-700 font-medium mb-2">Failed to load application</p>
          <p className="text-gray-500 text-sm mb-4">{error || 'Application not found'}</p>
          <Link href="/applications" className="text-orange-600 hover:underline">
            Back to applications
          </Link>
        </div>
      </div>
    );
  }

  const statusConf = STATUS_CONFIG[app.status] || STATUS_CONFIG.submitted;
  const StatusIcon = statusConf.icon;

  const isWithdrawable = ['draft', 'submitted', 'processing', 'prequal_submitted', 'prequal_completed', 'application_started'].includes(app.status);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back */}
        <Link
          href="/applications"
          className="inline-flex items-center gap-1.5 text-gray-500 hover:text-orange-600 text-sm mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Applications
        </Link>

        {/* Status Header */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${statusConf.color}`}>
                <StatusIcon className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                  Loan Application
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  ID: <span className="font-mono">{app.id}</span>
                </p>
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium mt-2 ${statusConf.color}`}>
                  <StatusIcon className="w-4 h-4" />
                  {statusConf.label}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              {isWithdrawable && (
                <button
                  onClick={handleWithdraw}
                  disabled={withdrawing}
                  className="px-4 py-2 text-sm font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
                >
                  {withdrawing ? 'Withdrawing...' : 'Withdraw'}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Main content grid */}
        <div className="grid lg:grid-cols-2 gap-6 mb-6">
          {/* Application Details */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Application Details</h2>
            </div>
            <div className="p-5 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Requested Amount</span>
                <span className="font-semibold text-gray-900">{formatCurrency(app.requested_amount)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Term</span>
                <span className="font-semibold text-gray-900">{app.requested_term_months} months</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Loan Purpose</span>
                <span className="font-semibold text-gray-900 capitalize">
                  {app.loan_purpose?.replace(/_/g, ' ') || 'Personal'}
                </span>
              </div>
              {app.loan_purpose_details && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Details</span>
                  <span className="font-semibold text-gray-900 text-right max-w-[200px]">
                    {app.loan_purpose_details}
                  </span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Created</span>
                <span className="font-semibold text-gray-900">{formatDate(app.created_at)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Last Updated</span>
                <span className="font-semibold text-gray-900">{formatDate(app.updated_at)}</span>
              </div>
              {app.decisioned_at && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Decisioned At</span>
                  <span className="font-semibold text-gray-900">{formatDate(app.decisioned_at)}</span>
                </div>
              )}
              {app.funded_at && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Funded At</span>
                  <span className="font-semibold text-gray-900">{formatDate(app.funded_at)}</span>
                </div>
              )}
              {app.amount_funded && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-500">Amount Funded</span>
                  <span className="font-semibold text-green-600">{formatCurrency(app.amount_funded)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Financial Info */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">Financial Information</h2>
            </div>
            <div className="p-5 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Monthly Income</span>
                <span className="font-semibold text-gray-900">
                  {formatCurrency(app.application_monthly_income || null)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Employer</span>
                <span className="font-semibold text-gray-900">{app.application_employer || '—'}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Employment Status</span>
                <span className="font-semibold text-gray-900 capitalize">
                  {app.application_employment_status?.replace(/_/g, ' ') || '—'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Years at Job</span>
                <span className="font-semibold text-gray-900">
                  {app.years_at_current_job ? `${app.years_at_current_job} yrs` : '—'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Housing Status</span>
                <span className="font-semibold text-gray-900 capitalize">
                  {app.housing_status?.replace(/_/g, ' ') || '—'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Monthly Housing Payment</span>
                <span className="font-semibold text-gray-900">
                  {formatCurrency(app.monthly_housing_payment || null)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total Existing Debt</span>
                <span className="font-semibold text-gray-900">
                  {formatCurrency(app.total_existing_debt || null)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Underwriting Result / Decision */}
        {app.underwriting_result && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-600" />
              <h2 className="font-semibold text-gray-900">Underwriting Result</h2>
            </div>
            <div className="p-5">
              <div className="grid sm:grid-cols-3 gap-4 mb-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-500 mb-1">Risk Score</p>
                  <p className="text-xl font-bold text-gray-900">
                    {app.underwriting_result.risk_score ?? '—'}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-500 mb-1">Risk Tier</p>
                  <p className="text-xl font-bold text-gray-900 capitalize">
                    {app.underwriting_result.risk_tier?.replace(/_/g, ' ') || '—'}
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-xs text-gray-500 mb-1">Decision</p>
                  <p className={`text-xl font-bold capitalize ${
                    app.underwriting_result.decision === 'approved' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {app.underwriting_result.decision || '—'}
                  </p>
                </div>
              </div>
              {app.underwriting_result.apr && (
                <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Offered APR</span>
                  <span className="text-lg font-bold text-orange-600">
                    {app.underwriting_result.apr}%
                  </span>
                </div>
              )}
              {app.underwriting_result.factors && Object.keys(app.underwriting_result.factors).length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-700 mb-2">Decision Factors</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(app.underwriting_result.factors).map(([key, val]) => (
                      <span key={key} className="px-2.5 py-1 bg-gray-100 rounded-lg text-xs text-gray-600">
                        {key.replace(/_/g, ' ')}: {String(val)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Declined reasons */}
        {app.status === 'declined' && (app.declined_reason || app.declined_reason_codes) && (
          <div className="bg-red-50 rounded-xl border border-red-200 p-5 mb-6">
            <div className="flex items-start gap-3">
              <XCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-800 mb-1">Application Declined</h3>
                {app.declined_reason && (
                  <p className="text-sm text-red-700 mb-2">{app.declined_reason}</p>
                )}
                {app.declined_reason_codes && app.declined_reason_codes.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {app.declined_reason_codes.map((code, i) => (
                      <span key={i} className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-medium">
                        {code}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Accept Offer (if approved) */}
        {app.status === 'approved' && app.underwriting_result?.apr && (
          <div className="bg-green-50 rounded-xl border border-green-200 p-6 mb-6">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-green-800 text-lg mb-1">
                  You&apos;ve Been Approved!
                </h3>
                <p className="text-green-700 text-sm mb-4">
                  Your application has been approved. Accept your offer to proceed with funding.
                </p>
                <div className="flex items-center gap-6 mb-4 p-3 bg-white rounded-lg border border-green-100">
                  <div>
                    <p className="text-xs text-gray-500">Amount</p>
                    <p className="font-bold text-gray-900">{formatCurrency(app.underwriting_result.approved_amount || app.requested_amount)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">APR</p>
                    <p className="font-bold text-green-600">{app.underwriting_result.apr}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Monthly</p>
                    <p className="font-bold text-gray-900">{formatCurrency(app.underwriting_result.monthly_payment || null)}</p>
                  </div>
                </div>
                <button
                  onClick={() => alert('Offer accepted! (API integration pending)')}
                  className="px-6 py-2.5 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
                >
                  Accept Offer
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ApplicationDetailPage() {
  return (
    <AuthGuard>
      <ApplicationDetailContent />
    </AuthGuard>
  );
}
