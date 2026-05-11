'use client';

import React, { useEffect, useState } from 'react';
import { adminSettingsApi, getApiErrorMessage, AdminSettings } from '@/src/lib/admin-api';
import {
  Settings,
  AlertCircle,
  Loader2,
  RefreshCw,
  Shield,
  ShieldCheck,
  ShieldX,
  Server,
  Globe,
  Activity,
  Key,
} from 'lucide-react';

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<AdminSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = async (showLoader = true) => {
    if (showLoader) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const { data } = await adminSettingsApi.get();
      setSettings(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchSettings(); }, []);

  const ApiKeyStatus = ({ label, enabled }: { label: string; enabled: boolean }) => (
    <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
      <div className="flex items-center gap-2">
        <Key className="w-4 h-4 text-gray-400" />
        <span className="text-sm text-gray-300">{label}</span>
      </div>
      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
        enabled ? 'text-green-400 bg-green-500/10' : 'text-red-400 bg-red-500/10'
      }`}>
        {enabled ? <ShieldCheck className="w-3 h-3" /> : <ShieldX className="w-3 h-3" />}
        {enabled ? 'Configured' : 'Not Set'}
      </span>
    </div>
  );

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto">
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white">System Settings</h1>
          <p className="text-gray-400 mt-1">View platform configuration and API status</p>
        </div>
        <button
          onClick={() => fetchSettings(false)}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-white/5 text-gray-300 border border-white/10 rounded-xl text-sm font-medium hover:bg-white/10 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-xl mb-6 text-sm text-red-300">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {settings && (
        <div className="space-y-6">
          {/* General */}
          <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
            <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
              <Server className="w-5 h-5 text-blue-400" />
              <h2 className="font-semibold text-white">General</h2>
            </div>
            <div className="p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Application Name</span>
                <span className="font-medium text-white">{settings.app_name || 'OrangeFi'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-400">Environment</span>
                <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${
                  settings.environment === 'production' ? 'text-green-400 bg-green-500/10' :
                  settings.environment === 'staging' ? 'text-yellow-400 bg-yellow-500/10' :
                  'text-blue-400 bg-blue-500/10'
                }`}>
                  {settings.environment || 'development'}
                </span>
              </div>
            </div>
          </div>

          {/* Rate Limits */}
          {settings.rate_limits && (
            <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
              <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-400" />
                <h2 className="font-semibold text-white">Rate Limits</h2>
              </div>
              <div className="p-5 space-y-3">
                {Object.entries(settings.rate_limits).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                    <span className="font-medium text-white">{String(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* API Keys Status */}
          <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
            <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
              <Key className="w-5 h-5 text-orange-400" />
              <h2 className="font-semibold text-white">API Integrations</h2>
            </div>
            <div className="p-5 space-y-3">
              {settings.api_keys ? (
                <>
                  <ApiKeyStatus label="Plaid" enabled={settings.api_keys.plaid} />
                  <ApiKeyStatus label="Stripe" enabled={settings.api_keys.stripe} />
                  <ApiKeyStatus label="Twilio (SMS)" enabled={settings.api_keys.twilio} />
                  <ApiKeyStatus label="SendGrid (Email)" enabled={settings.api_keys.sendgrid} />
                </>
              ) : (
                <p className="text-sm text-gray-500">API key status information not available</p>
              )}
            </div>
          </div>

          {/* Other settings */}
          {Object.entries(settings).filter(([key]) => !['app_name', 'environment', 'rate_limits', 'api_keys'].includes(key)).length > 0 && (
            <div className="bg-gray-900/80 backdrop-blur-sm rounded-xl border border-white/5">
              <div className="px-5 py-4 border-b border-white/5 flex items-center gap-2">
                <Settings className="w-5 h-5 text-gray-400" />
                <h2 className="font-semibold text-white">Additional Configuration</h2>
              </div>
              <div className="p-5 space-y-3">
                {Object.entries(settings)
                  .filter(([key]) => !['app_name', 'environment', 'rate_limits', 'api_keys'].includes(key))
                  .map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm text-gray-400 capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-medium text-white text-sm max-w-[300px] truncate text-right">
                        {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
