'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { adminDashboardApi, adminAuditLogApi, getApiErrorMessage, DashboardMetrics, AuditLogEntry } from '@/src/lib/admin-api';
import {
  CalendarCheck,
  Clock,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  PieChart,
  FileText,
  Download,
  ChevronRight,
  Loader2,
  AlertCircle,
  Activity,
  Users,
  Shield,
  CreditCard,
  Settings,
} from 'lucide-react';

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  loading,
  subtitle,
}: {
  label: string;
  value: string | number;
  icon: any;
  color: string;
  loading?: boolean;
  subtitle?: string;
}) {
  const colorMap: Record<string, string> = {
    orange: 'bg-orange-500/15 text-orange-400 border-orange-500/20',
    blue: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
    green: 'bg-green-500/15 text-green-400 border-green-500/20',
    red: 'bg-red-500/15 text-red-400 border-red-500/20',
    purple: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
    cyan: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
  };

  return (
    <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5 p-5 hover:border-white/10 transition-all">
      <div className="flex items-start justify-between mb-3">
        <p className="text-sm text-gray-400">{label}</p>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colorMap[color] || colorMap.blue}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {loading ? (
        <div className="h-8 w-24 bg-white/5 rounded animate-pulse" />
      ) : (
        <p className="text-2xl font-bold text-white">{value}</p>
      )}
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  );
}

function ActivityFeed({ entries, loading }: { entries: AuditLogEntry[]; loading: boolean }) {
  const formatTime = (ts: string) => {
    const d = new Date(ts);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center gap-3 p-3">
            <div className="w-8 h-8 rounded-lg bg-white/5 animate-pulse" />
            <div className="flex-1">
              <div className="h-4 w-3/4 bg-white/5 rounded animate-pulse mb-1" />
              <div className="h-3 w-1/2 bg-white/5 rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className="text-center py-10">
        <Activity className="w-10 h-10 text-gray-600 mx-auto mb-3" />
        <p className="text-gray-500 text-sm">No recent activity</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {entries.map((entry) => (
        <div
          key={entry.id}
          className="flex items-start gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors"
        >
          <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center flex-shrink-0 mt-0.5">
            <Activity className="w-4 h-4 text-gray-400" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-gray-300">
              <span className="font-medium text-white">{entry.actor}</span>
              {' '}{entry.description || entry.action}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-gray-500">{formatTime(entry.timestamp)}</span>
              {entry.resource_type && (
                <span className="text-xs px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 capitalize">
                  {entry.resource_type}
                </span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [activities, setActivities] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activityLoading, setActivityLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const { data } = await adminDashboardApi.getMetrics();
        setMetrics(data);
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    const fetchActivity = async () => {
      try {
        const { data } = await adminAuditLogApi.list({ page: 1, page_size: 10 });
        setActivities(data.data);
      } catch {
        // Non-critical
      } finally {
        setActivityLoading(false);
      }
    };
    fetchActivity();
  }, []);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);

  const formatPercent = (val: number) => `${val.toFixed(1)}%`;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">Overview of platform metrics and activity</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/admin/applications?status=manual_review"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-orange-500/10 text-orange-400 border border-orange-500/20 rounded-xl text-sm font-medium hover:bg-orange-500/20 transition-all"
          >
            <FileText className="w-4 h-4" />
            Pending Applications
          </Link>
          <button
            onClick={() => window.open('/admin/audit-log', '_blank')}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-white/5 text-gray-300 border border-white/10 rounded-xl text-sm font-medium hover:bg-white/10 transition-all"
          >
            <Download className="w-4 h-4" />
            Generate Report
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-xl mb-6 text-sm text-red-300">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
        <StatCard label="Applications Today" value={metrics?.applications_today ?? '—'} icon={CalendarCheck} color="blue" loading={loading} />
        <StatCard label="Pending Review" value={metrics?.pending_review ?? '—'} icon={Clock} color="orange" loading={loading} subtitle="Awaiting decision" />
        <StatCard label="Funded MTD" value={metrics?.funded_mtd_amount != null ? formatCurrency(metrics.funded_mtd_amount) : '—'} icon={DollarSign} color="green" loading={loading} />
        <StatCard label="Active Loans" value={metrics?.active_loans ?? '—'} icon={TrendingUp} color="cyan" loading={loading} />
        <StatCard label="Delinquency Rate" value={metrics?.delinquency_rate_pct != null ? formatPercent(metrics.delinquency_rate_pct) : '—'} icon={AlertTriangle} color="red" loading={loading} subtitle={`${metrics?.delinquent_loans ?? 0} delinquent loans`} />
        <StatCard label="Charged Off" value={metrics?.charged_off_loans ?? '—'} icon={PieChart} color="purple" loading={loading} />
        <StatCard label="Portfolio Outstanding" value={metrics?.portfolio_outstanding != null ? formatCurrency(metrics.portfolio_outstanding) : '—'} icon={DollarSign} color="green" loading={loading} />
        <StatCard label="New Borrowers (30d)" value={metrics?.new_borrowers_30d ?? '—'} icon={Users} color="blue" loading={loading} />
      </div>

      {/* Bottom row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5 flex items-center justify-between">
            <h2 className="font-semibold text-white">Recent Activity</h2>
            <Link href="/admin/audit-log" className="text-sm text-orange-400 hover:text-orange-300 font-medium inline-flex items-center gap-1">
              View all <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="p-5">
            <ActivityFeed entries={activities} loading={activityLoading} />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
          <div className="px-5 py-4 border-b border-white/5">
            <h2 className="font-semibold text-white">Quick Actions</h2>
          </div>
          <div className="p-5 space-y-3">
            <Link href="/admin/applications" className="flex items-center gap-4 p-4 rounded-xl border border-white/5 hover:border-orange-500/20 hover:bg-orange-500/5 transition-all group">
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center group-hover:bg-orange-500/20 transition-all">
                <FileText className="w-5 h-5 text-orange-400" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-white">Review Applications</p>
                <p className="text-sm text-gray-400">Process pending loan applications</p>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-orange-400 transition-all" />
            </Link>
            <Link href="/admin/loans" className="flex items-center gap-4 p-4 rounded-xl border border-white/5 hover:border-orange-500/20 hover:bg-orange-500/5 transition-all group">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center group-hover:bg-blue-500/20 transition-all">
                <CreditCard className="w-5 h-5 text-blue-400" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-white">Monitor Loans</p>
                <p className="text-sm text-gray-400">View loan portfolio and delinquencies</p>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-orange-400 transition-all" />
            </Link>
            <Link href="/admin/compliance" className="flex items-center gap-4 p-4 rounded-xl border border-white/5 hover:border-orange-500/20 hover:bg-orange-500/5 transition-all group">
              <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center group-hover:bg-red-500/20 transition-all">
                <Shield className="w-5 h-5 text-red-400" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-white">Compliance Events</p>
                <p className="text-sm text-gray-400">Review compliance and risk events</p>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-orange-400 transition-all" />
            </Link>
            <Link href="/admin/settings" className="flex items-center gap-4 p-4 rounded-xl border border-white/5 hover:border-orange-500/20 hover:bg-orange-500/5 transition-all group">
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center group-hover:bg-purple-500/20 transition-all">
                <Settings className="w-5 h-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-white">System Settings</p>
                <p className="text-sm text-gray-400">Configure platform settings</p>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-orange-400 transition-all" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
