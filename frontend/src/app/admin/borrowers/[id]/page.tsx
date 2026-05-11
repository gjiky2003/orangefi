'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { adminBorrowersApi, getApiErrorMessage, BorrowerDetailResponse } from '@/src/lib/admin-api';
import type { LoanListItem, ApplicationListItem } from '@/src/types';
import {
  ArrowLeft,
  User,
  Mail,
  Phone,
  Shield,
  ShieldCheck,
  ShieldX,
  Calendar,
  CreditCard,
  FileText,
  AlertCircle,
  Loader2,
  ChevronRight,
  DollarSign,
  MapPin,
  Briefcase,
} from 'lucide-react';

const LOAN_STATUS_STYLES: Record<string, string> = {
  active: 'text-green-400 bg-green-500/10',
  current: 'text-green-400 bg-green-500/10',
  delinquent: 'text-red-400 bg-red-500/10',
  paid_off: 'text-emerald-400 bg-emerald-500/10',
  charged_off: 'text-gray-400 bg-gray-800',
  defaulted: 'text-red-400 bg-red-500/10',
  processing: 'text-blue-400 bg-blue-500/10',
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'text-gray-400 bg-gray-800',
  submitted: 'text-blue-400 bg-blue-500/10',
  processing: 'text-yellow-400 bg-yellow-500/10',
  approved: 'text-green-400 bg-green-500/10',
  declined: 'text-red-400 bg-red-500/10',
  funded: 'text-emerald-400 bg-emerald-500/10',
  cancelled: 'text-gray-500 bg-gray-800',
};

export default function AdminBorrowerDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [borrower, setBorrower] = useState<BorrowerDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBorrower = async () => {
      try {
        const { data } = await adminBorrowersApi.get(id);
        setBorrower(data);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchBorrower();
  }, [id]);

  const formatCurrency = (val: number | null) => {
    if (val === null || val === undefined) return '—';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
      </div>
    );
  }

  if (error || !borrower) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-gray-300 font-medium mb-2">Failed to load borrower</p>
          <p className="text-gray-500 text-sm mb-4">{error || 'Borrower not found'}</p>
          <Link href="/admin/borrowers" className="text-orange-400 hover:underline">Back to borrowers</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto">
      <Link href="/admin/borrowers" className="inline-flex items-center gap-1.5 text-gray-400 hover:text-orange-400 text-sm mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" />
        Back to Borrowers
      </Link>

      {/* Profile Card */}
      <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 p-6 mb-6">
        <div className="flex flex-col sm:flex-row items-start gap-5">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center flex-shrink-0">
            <span className="text-2xl font-bold text-white">
              {borrower.first_name?.[0]}{borrower.last_name?.[0]}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-white">
                {borrower.first_name} {borrower.last_name}
              </h1>
              <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
                borrower.is_identity_verified ? 'text-green-400 bg-green-500/10' : 'text-yellow-400 bg-yellow-500/10'
              }`}>
                {borrower.is_identity_verified ? <ShieldCheck className="w-3 h-3" /> : <ShieldX className="w-3 h-3" />}
                KYC: {borrower.is_identity_verified ? 'Verified' : 'Pending'}
              </span>
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-400">
              <span className="inline-flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5" /> {borrower.email}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Phone className="w-3.5 h-3.5" /> {borrower.phone}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" /> Joined {formatDate(borrower.created_at)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Credit & Identity Info */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5">
            <h2 className="font-semibold text-white">Credit & Identity</h2>
          </div>
          <div className="p-5 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Credit Score Range</span>
              <span className="font-medium text-white">{borrower.credit_score_range || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Credit Tier</span>
              <span className="font-medium text-white capitalize">{borrower.credit_tier?.replace(/_/g, ' ') || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Monthly Income</span>
              <span className="font-medium text-white">{formatCurrency(borrower.monthly_income)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Identity Verified</span>
              <span className={`font-medium ${borrower.is_identity_verified ? 'text-green-400' : 'text-yellow-400'}`}>
                {borrower.is_identity_verified ? 'Yes' : 'No'}
              </span>
            </div>
            {borrower.kyc_completed_at && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">KYC Completed</span>
                <span className="font-medium text-white">{formatDate(borrower.kyc_completed_at)}</span>
              </div>
            )}
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Active</span>
              <span className={`font-medium ${borrower.is_active ? 'text-green-400' : 'text-red-400'}`}>
                {borrower.is_active ? 'Yes' : 'No'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5">
            <h2 className="font-semibold text-white">Personal Details</h2>
          </div>
          <div className="p-5 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Date of Birth</span>
              <span className="font-medium text-white">{formatDate(borrower.date_of_birth)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Employer</span>
              <span className="font-medium text-white">{borrower.employer || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Employment Status</span>
              <span className="font-medium text-white capitalize">{borrower.employment_status?.replace(/_/g, ' ') || '—'}</span>
            </div>
            <div className="flex justify-between items-start">
              <span className="text-sm text-gray-400">Address</span>
              <span className="font-medium text-white text-right max-w-[200px]">
                {[borrower.address_line1, borrower.address_line2, borrower.city, borrower.state, borrower.zip_code]
                  .filter(Boolean).join(', ') || '—'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Loan History */}
      {borrower.loans && borrower.loans.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 mb-6">
          <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
            <h2 className="font-semibold text-white">Loan History ({borrower.loans.length})</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">ID</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Amount</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">APR</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Status</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Origination</th>
                  <th className="text-right px-5 py-3 font-semibold text-gray-300">Action</th>
                </tr>
              </thead>
              <tbody>
                {borrower.loans.map((loan) => (
                  <tr key={loan.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-3">
                      <span className="font-mono text-xs text-gray-500">{loan.id.slice(0, 8)}...</span>
                    </td>
                    <td className="px-5 py-3 text-white">{formatCurrency(loan.loan_amount)}</td>
                    <td className="px-5 py-3 text-gray-300">{loan.apr}%</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium capitalize ${LOAN_STATUS_STYLES[loan.status] || 'text-gray-400 bg-gray-800'}`}>
                        {loan.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-500 text-xs">{formatDate(loan.origination_date)}</td>
                    <td className="px-5 py-3 text-right">
                      <Link href={`/admin/loans/${loan.id}`} className="text-orange-400 hover:text-orange-300 font-medium text-xs">
                        View <ChevronRight className="w-3 h-3 inline" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Application History */}
      {borrower.applications && borrower.applications.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 mb-6">
          <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
            <h2 className="font-semibold text-white">Application History ({borrower.applications.length})</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">ID</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Amount</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Purpose</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Status</th>
                  <th className="text-left px-5 py-3 font-semibold text-gray-300">Created</th>
                  <th className="text-right px-5 py-3 font-semibold text-gray-300">Action</th>
                </tr>
              </thead>
              <tbody>
                {borrower.applications.map((app) => (
                  <tr key={app.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-3">
                      <span className="font-mono text-xs text-gray-500">{app.id.slice(0, 8)}...</span>
                    </td>
                    <td className="px-5 py-3 text-white">{formatCurrency(app.requested_amount)}</td>
                    <td className="px-5 py-3 text-gray-400 capitalize">{app.loan_purpose?.replace(/_/g, ' ') || 'Personal'}</td>
                    <td className="px-5 py-3">
                      <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium capitalize ${STATUS_COLORS[app.status] || 'text-gray-400 bg-gray-800'}`}>
                        {app.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-500 text-xs">{formatDate(app.created_at)}</td>
                    <td className="px-5 py-3 text-right">
                      <Link href={`/admin/applications/${app.id}`} className="text-orange-400 hover:text-orange-300 font-medium text-xs">
                        View <ChevronRight className="w-3 h-3 inline" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Documents */}
      {borrower.documents && borrower.documents.length > 0 && (
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5">
            <h2 className="font-semibold text-white">Documents ({borrower.documents.length})</h2>
          </div>
          <div className="p-5">
            <div className="grid sm:grid-cols-2 gap-3">
              {borrower.documents.map((doc: any, i: number) => (
                <div key={doc.id || i} className="flex items-center gap-3 p-3 bg-white/5 rounded-lg">
                  <FileText className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-white">{doc.file_name || doc.document_type || 'Document'}</p>
                    <p className="text-xs text-gray-500 capitalize">{doc.document_type?.replace(/_/g, ' ') || '—'}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
