'use client';

import React, { useEffect, useState } from 'react';
import { adminDashboardApi, getApiErrorMessage, PortfolioSummary } from '@/src/lib/admin-api';
import {
  Briefcase,
  DollarSign,
  TrendingUp,
  AlertCircle,
  Loader2,
  PieChart,
  RefreshCw,
  Shield,
} from 'lucide-react';

export default function AdminPortfolioPage() {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const { data } = await adminDashboardApi.getPortfolioSummary();
        setSummary(data);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

  const formatPercent = (val: number) => `${(val * 100).toFixed(2)}%`;

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-12 text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <p className="text-gray-300 font-medium mb-2">Failed to load portfolio data</p>
          <p className="text-gray-500 text-sm">{error || 'Unable to fetch portfolio summary'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Portfolio Summary</h1>
        <p className="text-gray-400 mt-1">Overall loan portfolio health and breakdown</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Total Loans</p>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-blue-400" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white">{summary.total_loans}</p>
        </div>
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Total Outstanding</p>
            <div className="w-10 h-10 rounded-xl bg-green-500/10 flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-green-400" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white">{formatCurrency(summary.total_outstanding)}</p>
        </div>
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Average APR</p>
            <div className="w-10 h-10 rounded-xl bg-orange-500/10 flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-orange-400" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white">{summary.average_apr.toFixed(2)}%</p>
        </div>
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-5">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-400">Default Rate</p>
            <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
              <Shield className="w-5 h-5 text-red-400" />
            </div>
          </div>
          <p className="text-2xl font-bold text-white">{formatPercent(summary.default_rate)}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* More Metrics */}
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-5">
          <h2 className="font-semibold text-white mb-4">Portfolio Metrics</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Total Principal</span>
              <span className="font-medium text-white">{formatCurrency(summary.total_principal)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Total Interest Earned</span>
              <span className="font-medium text-green-400">{formatCurrency(summary.total_interest_earned)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Delinquency Rate</span>
              <span className="font-medium text-red-400">{formatPercent(summary.delinquency_rate)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">Weighted Avg Risk Score</span>
              <span className="font-medium text-white">{summary.weighted_average_risk_score.toFixed(1)}</span>
            </div>
          </div>
        </div>

        {/* By Status */}
        {summary.portfolio_breakdown_by_status && Object.keys(summary.portfolio_breakdown_by_status).length > 0 && (
          <div className="bg-gray-900/80 rounded-xl border border-white/5 p-5">
            <h2 className="font-semibold text-white mb-4">By Status</h2>
            <div className="space-y-3">
              {Object.entries(summary.portfolio_breakdown_by_status).map(([status, count]) => (
                <div key={status} className="flex justify-between items-center">
                  <span className="text-sm text-gray-400 capitalize">{status.replace(/_/g, ' ')}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-800 rounded-full h-2">
                      <div
                        className="h-2 rounded-full bg-orange-500"
                        style={{ width: `${(count / summary.total_loans) * 100}%` }}
                      />
                    </div>
                    <span className="font-medium text-white text-sm w-16 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* By Tier */}
      {summary.portfolio_breakdown_by_tier && Object.keys(summary.portfolio_breakdown_by_tier).length > 0 && (
        <div className="bg-gray-900/80 rounded-xl border border-white/5 p-5">
          <h2 className="font-semibold text-white mb-4">By Risk Tier</h2>
          <div className="space-y-3">
            {Object.entries(summary.portfolio_breakdown_by_tier).map(([tier, count]) => (
              <div key={tier} className="flex justify-between items-center">
                <span className="text-sm text-gray-400 capitalize">{tier.replace(/_/g, ' ')}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-800 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        tier === 'prime' || tier === 'tier_1' ? 'bg-green-500' :
                        tier === 'near_prime' || tier === 'tier_2' ? 'bg-yellow-500' :
                        tier === 'subprime' || tier === 'tier_3' ? 'bg-orange-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${(count / summary.total_loans) * 100}%` }}
                    />
                  </div>
                  <span className="font-medium text-white text-sm w-16 text-right">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
