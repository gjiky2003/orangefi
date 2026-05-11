'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { adminApplicationsApi, getApiErrorMessage, ApplicationDecisionRequest } from '@/src/lib/admin-api';
import type { ApplicationDetail } from '@/src/types';
import {
  ArrowLeft,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Loader2,
  DollarSign,
  User,
  TrendingUp,
  Shield,
  Check,
  ThumbsUp,
  ThumbsDown,
  Upload,
  Calendar,
} from 'lucide-react';

const STATUS_CONFIG: Record<string, { color: string; icon: any; label: string }> = {
  draft: { color: 'text-gray-400 bg-gray-800', icon: FileText, label: 'Draft' },
  submitted: { color: 'text-blue-400 bg-blue-500/10', icon: Clock, label: 'Submitted' },
  prequal_submitted: { color: 'text-blue-400 bg-blue-500/10', icon: Clock, label: 'Pre-Qual Submitted' },
  prequal_completed: { color: 'text-cyan-400 bg-cyan-500/10', icon: CheckCircle, label: 'Pre-Qual Completed' },
  application_started: { color: 'text-gray-400 bg-gray-800', icon: FileText, label: 'Started' },
  processing: { color: 'text-yellow-400 bg-yellow-500/10', icon: Clock, label: 'Processing' },
  manual_review: { color: 'text-orange-400 bg-orange-500/10', icon: Shield, label: 'Manual Review' },
  approved: { color: 'text-green-400 bg-green-500/10', icon: CheckCircle, label: 'Approved' },
  declined: { color: 'text-red-400 bg-red-500/10', icon: XCircle, label: 'Declined' },
  funded: { color: 'text-emerald-400 bg-emerald-500/10', icon: CheckCircle, label: 'Funded' },
  cancelled: { color: 'text-gray-500 bg-gray-800', icon: XCircle, label: 'Cancelled' },
};

const DECLINE_REASONS = [
  { value: 'insufficient_income', label: 'Insufficient Income' },
  { value: 'high_dti_ratio', label: 'High Debt-to-Income Ratio' },
  { value: 'poor_credit_history', label: 'Poor Credit History' },
  { value: 'unstable_employment', label: 'Unstable Employment' },
  { value: 'incomplete_documentation', label: 'Incomplete Documentation' },
  { value: 'identity_verification_failed', label: 'Identity Verification Failed' },
  { value: 'policy_restriction', label: 'Policy Restriction' },
  { value: 'other', label: 'Other' },
];

export default function AdminApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [app, setApp] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Decision form state
  const [showDecideForm, setShowDecideForm] = useState(false);
  const [decision, setDecision] = useState<'approved' | 'declined'>('approved');
  const [approvedAmount, setApprovedAmount] = useState<number>(0);
  const [termMonths, setTermMonths] = useState<number>(12);
  const [declineReason, setDeclineReason] = useState('');
  const [declineNote, setDeclineNote] = useState('');

  useEffect(() => {
    const fetchApp = async () => {
      try {
        const { data } = await adminApplicationsApi.get(id);
        setApp(data);
        setApprovedAmount(data.requested_amount);
        setTermMonths(data.requested_term_months || 12);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchApp();
  }, [id]);

  const handleDecision = async () => {
    setActionError(null);
    setActionSuccess(null);
    setActionLoading(true);

    try {
      const payload: ApplicationDecisionRequest = {
        decision,
      };

      if (decision === 'approved') {
        payload.approved_amount = approvedAmount;
        payload.term_months = termMonths;
      } else {
        payload.declined_reason = declineReason;
        payload.declined_reason_codes = declineReason ? [declineReason] : [];
        payload.notes = declineNote || undefined;
      }

      await adminApplicationsApi.decision(id, payload);
      setActionSuccess(`Application ${decision === 'approved' ? 'approved' : 'declined'} successfully`);
      setShowDecideForm(false);

      // Refresh application data
      const { data } = await adminApplicationsApi.get(id);
      setApp(data);
    } catch (err) {
      setActionError(getApiErrorMessage(err));
    } finally {
      setActionLoading(false);
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

  const canDecide = app && ['submitted', 'processing', 'manual_review'].includes(app.status);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
      </div>
    );
  }

  if (error || !app) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-gray-300 font-medium mb-2">Failed to load application</p>
          <p className="text-gray-500 text-sm mb-4">{error || 'Application not found'}</p>
          <Link href="/admin/applications" className="text-orange-400 hover:underline">
            Back to applications
          </Link>
        </div>
      </div>
    );
  }

  const statusConf = STATUS_CONFIG[app.status] || STATUS_CONFIG.submitted;
  const StatusIcon = statusConf.icon;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto">
      {/* Back */}
      <Link
        href="/admin/applications"
        className="inline-flex items-center gap-1.5 text-gray-400 hover:text-orange-400 text-sm mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Applications
      </Link>

      {/* Status Header */}
      <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 p-6 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${statusConf.color}`}>
              <StatusIcon className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-white">Loan Application</h1>
              <p className="text-sm text-gray-400 mt-1">
                ID: <span className="font-mono">{app.id}</span>
              </p>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium mt-2 ${statusConf.color}`}>
                <StatusIcon className="w-4 h-4" />
                {statusConf.label}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            {canDecide && !showDecideForm && (
              <button
                onClick={() => setShowDecideForm(true)}
                className="px-5 py-2.5 bg-orange-500 text-white rounded-xl font-medium hover:bg-orange-600 transition-all shadow-lg shadow-orange-500/20"
              >
                Make Decision
              </button>
            )}
          </div>
        </div>

        {/* Action status messages */}
        {actionSuccess && (
          <div className="flex items-start gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-xl mt-4 text-sm text-green-300">
            <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{actionSuccess}</span>
          </div>
        )}
        {actionError && (
          <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-xl mt-4 text-sm text-red-300">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{actionError}</span>
          </div>
        )}
      </div>

      {/* Decision Form */}
      {showDecideForm && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-orange-500/20 p-6 mb-6">
          <h2 className="font-semibold text-white mb-4">Application Decision</h2>

          {/* Decision type toggle */}
          <div className="flex gap-3 mb-6">
            <button
              onClick={() => setDecision('approved')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all ${
                decision === 'approved'
                  ? 'bg-green-500/15 text-green-400 border border-green-500/30'
                  : 'bg-white/5 text-gray-400 border border-white/10 hover:border-white/20'
              }`}
            >
              <ThumbsUp className="w-4 h-4" />
              Approve
            </button>
            <button
              onClick={() => setDecision('declined')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all ${
                decision === 'declined'
                  ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                  : 'bg-white/5 text-gray-400 border border-white/10 hover:border-white/20'
              }`}
            >
              <ThumbsDown className="w-4 h-4" />
              Decline
            </button>
          </div>

          {decision === 'approved' ? (
            <div className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">Approved Amount</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="number"
                      value={approvedAmount}
                      onChange={(e) => setApprovedAmount(Number(e.target.value))}
                      className="w-full pl-8 pr-4 py-2.5 bg-gray-800 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5">Term (Months)</label>
                  <select
                    value={termMonths}
                    onChange={(e) => setTermMonths(Number(e.target.value))}
                    className="w-full px-4 py-2.5 bg-gray-800 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-500/50 transition-all"
                  >
                    {[6, 12, 18, 24, 36, 48, 60].map((m) => (
                      <option key={m} value={m} className="bg-gray-800">{m} months</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Decline Reason</label>
                <select
                  value={declineReason}
                  onChange={(e) => setDeclineReason(e.target.value)}
                  className="w-full px-4 py-2.5 bg-gray-800 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50 transition-all"
                >
                  <option value="" className="bg-gray-800">Select a reason...</option>
                  {DECLINE_REASONS.map((r) => (
                    <option key={r.value} value={r.value} className="bg-gray-800">{r.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1.5">Notes (optional)</label>
                <textarea
                  value={declineNote}
                  onChange={(e) => setDeclineNote(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2.5 bg-gray-800 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-red-500/50 transition-all resize-none"
                  placeholder="Additional notes about this decision..."
                />
              </div>
            </div>
          )}

          <div className="flex items-center gap-3 mt-6 pt-4 border-t border-white/5">
            <button
              onClick={handleDecision}
              disabled={actionLoading || (decision === 'declined' && !declineReason)}
              className="px-6 py-2.5 bg-orange-500 text-white rounded-xl font-medium hover:bg-orange-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {actionLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Submit Decision
                </>
              )}
            </button>
            <button
              onClick={() => setShowDecideForm(false)}
              className="px-4 py-2.5 text-gray-400 hover:text-white transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Main content grid */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Borrower Info */}
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
            <User className="w-5 h-5 text-blue-400" />
            <h2 className="font-semibold text-white">Borrower Information</h2>
          </div>
          <div className="p-5 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Name</span>
              <span className="font-medium text-white">{app.borrower_name}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Email</span>
              <span className="font-medium text-white">{app.borrower_email}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Employer</span>
              <span className="font-medium text-white">{app.application_employer || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Employment Status</span>
              <span className="font-medium text-white capitalize">{app.application_employment_status?.replace(/_/g, ' ') || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Years at Job</span>
              <span className="font-medium text-white">{app.years_at_current_job ? `${app.years_at_current_job} yrs` : '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Housing Status</span>
              <span className="font-medium text-white capitalize">{app.housing_status?.replace(/_/g, ' ') || '—'}</span>
            </div>
          </div>
        </div>

        {/* Application Details */}
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
            <FileText className="w-5 h-5 text-orange-400" />
            <h2 className="font-semibold text-white">Application Details</h2>
          </div>
          <div className="p-5 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Requested Amount</span>
              <span className="font-semibold text-white">{formatCurrency(app.requested_amount)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Term</span>
              <span className="font-semibold text-white">{app.requested_term_months} months</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Loan Purpose</span>
              <span className="font-semibold text-white capitalize">{app.loan_purpose?.replace(/_/g, ' ') || 'Personal'}</span>
            </div>
            {app.loan_purpose_details && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Details</span>
                <span className="font-semibold text-white text-right max-w-[200px]">{app.loan_purpose_details}</span>
              </div>
            )}
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Created</span>
              <span className="font-semibold text-white">{formatDate(app.created_at)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Last Updated</span>
              <span className="font-semibold text-white">{formatDate(app.updated_at)}</span>
            </div>
            {app.decisioned_at && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Decisioned At</span>
                <span className="font-semibold text-white">{formatDate(app.decisioned_at)}</span>
              </div>
            )}
            {app.funded_at && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Funded At</span>
                <span className="font-semibold text-white">{formatDate(app.funded_at)}</span>
              </div>
            )}
            {app.amount_funded && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">Amount Funded</span>
                <span className="font-semibold text-green-400">{formatCurrency(app.amount_funded)}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Financial Info */}
      <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 mb-6">
        <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-green-400" />
          <h2 className="font-semibold text-white">Financial Information</h2>
        </div>
        <div className="p-5">
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Monthly Income</p>
              <p className="text-lg font-bold text-white">{formatCurrency(app.application_monthly_income || null)}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Monthly Housing Payment</p>
              <p className="text-lg font-bold text-white">{formatCurrency(app.monthly_housing_payment || null)}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Total Existing Debt</p>
              <p className="text-lg font-bold text-white">{formatCurrency(app.total_existing_debt || null)}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-xs text-gray-500 mb-1">Monthly Debt Payments</p>
              <p className="text-lg font-bold text-white">{formatCurrency(app.monthly_debt_payments || null)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Underwriting Result */}
      {app.underwriting_result && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 mb-6">
          <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-orange-400" />
            <h2 className="font-semibold text-white">Underwriting Result</h2>
          </div>
          <div className="p-5">
            <div className="grid sm:grid-cols-3 gap-4 mb-4">
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Risk Score</p>
                <p className="text-xl font-bold text-white">{app.underwriting_result.risk_score ?? '—'}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Risk Tier</p>
                <p className="text-xl font-bold text-white capitalize">{app.underwriting_result.risk_tier?.replace(/_/g, ' ') || '—'}</p>
              </div>
              <div className="bg-white/5 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-1">Decision</p>
                <p className={`text-xl font-bold capitalize ${app.underwriting_result.decision === 'approved' ? 'text-green-400' : 'text-red-400'}`}>
                  {app.underwriting_result.decision || '—'}
                </p>
              </div>
            </div>
            {app.underwriting_result.apr && (
              <div className="flex justify-between items-center p-3 bg-orange-500/10 rounded-lg">
                <span className="text-sm font-medium text-gray-300">Offered APR</span>
                <span className="text-lg font-bold text-orange-400">{app.underwriting_result.apr}%</span>
              </div>
            )}
            {app.underwriting_result.factors && Object.keys(app.underwriting_result.factors).length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-300 mb-2">Decision Factors</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(app.underwriting_result.factors).map(([key, val]) => (
                    <span key={key} className="px-2.5 py-1 bg-white/5 rounded-lg text-xs text-gray-400">
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
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-5 mb-6">
          <div className="flex items-start gap-3">
            <XCircle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-300 mb-1">Application Declined</h3>
              {app.declined_reason && <p className="text-sm text-red-300 mb-2">{app.declined_reason}</p>}
              {app.declined_reason_codes && app.declined_reason_codes.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {app.declined_reason_codes.map((code, i) => (
                    <span key={i} className="px-2 py-0.5 bg-red-500/20 text-red-300 rounded text-xs font-medium">{code}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
