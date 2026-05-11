// ═══════════════════════════════════════════════════════════════════════════════
// OrangeFi — Admin API Client (separate from borrower API)
// ═══════════════════════════════════════════════════════════════════════════════

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { PaginatedResponse, ApplicationListItem, ApplicationDetail, LoanListItem, LoanDetail, ApiError, ApplicationStatus } from '@/src/types';

// ── Config ────────────────────────────────────────────────────────────────────

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://orangefi-backend.onrender.com/api/v1';

const ADMIN_TOKEN_KEY = 'orangefi_admin_token';
const ADMIN_REFRESH_KEY = 'orangefi_admin_refresh';

// ── Token helpers ─────────────────────────────────────────────────────────────

export const getAdminAccessToken = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem(ADMIN_TOKEN_KEY) : null;

export const getAdminRefreshToken = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem(ADMIN_REFRESH_KEY) : null;

export const setAdminTokens = (access: string, refresh: string) => {
  localStorage.setItem(ADMIN_TOKEN_KEY, access);
  localStorage.setItem(ADMIN_REFRESH_KEY, refresh);
};

export const clearAdminTokens = () => {
  localStorage.removeItem(ADMIN_TOKEN_KEY);
  localStorage.removeItem(ADMIN_REFRESH_KEY);
};

export const isAdminAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;
  const token = getAdminAccessToken();
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
};

// ── Axios Instance ────────────────────────────────────────────────────────────

const adminApi = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Request interceptor — attach admin JWT
adminApi.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAdminAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — auto-refresh on 401
let isAdminRefreshing = false;
let adminFailedQueue: Array<{
  resolve: (value: any) => void;
  reject: (reason: any) => void;
}> = [];

const processAdminQueue = (error: any, token: string | null = null) => {
  adminFailedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  adminFailedQueue = [];
};

adminApi.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isAdminRefreshing) {
        return new Promise((resolve, reject) => {
          adminFailedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return adminApi(originalRequest);
        });
      }

      originalRequest._retry = true;
      isAdminRefreshing = true;

      try {
        const refreshToken = getAdminRefreshToken();
        if (!refreshToken) throw new Error('No refresh token');

        const { data } = await axios.post(
          `${BASE_URL}/admin/refresh`,
          {},
          { headers: { Authorization: `Bearer ${refreshToken}` } }
        );

        setAdminTokens(data.access_token, data.refresh_token);
        processAdminQueue(null, data.access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return adminApi(originalRequest);
      } catch (refreshError) {
        processAdminQueue(refreshError, null);
        clearAdminTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/admin/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isAdminRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ── Error helper ──────────────────────────────────────────────────────────────

export const getApiErrorMessage = (error: any): string => {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiError | undefined;
    if (data?.detail) return data.detail;
    if (data?.error) return data.error;
    if (error.response?.status === 401) return 'Invalid credentials';
    if (error.response?.status === 403) return 'Access denied';
    if (error.response?.status === 404) return 'Not found';
    if (error.response?.status === 429) return 'Too many requests. Please wait.';
    if (error.code === 'ERR_NETWORK') return 'Cannot connect to server';
    return error.message || 'An unexpected error occurred';
  }
  return error?.message || 'An unexpected error occurred';
};

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AdminLoginRequest {
  email: string;
  password: string;
  mfa_code?: string;
}

export interface AdminLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  admin_id: string;
  email: string;
  name: string;
  role: string;
}

export interface DashboardMetrics {
  applications_today: number;
  pending_review: number;
  funded_mtd_amount: number;
  active_loans: number;
  delinquent_loans: number;
  delinquency_rate_pct: number;
  charged_off_loans: number;
  portfolio_outstanding: number;
  new_borrowers_30d: number;
}

export interface BorrowerListItem {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  credit_tier: string | null;
  is_identity_verified: boolean;
  is_active: boolean;
  created_at: string;
  loan_count: number;
}

export interface BorrowerDetailResponse {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  date_of_birth: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  employer: string | null;
  employment_status: string | null;
  monthly_income: number | null;
  is_identity_verified: boolean;
  kyc_completed_at: string | null;
  credit_score_range: string | null;
  credit_tier: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  loans: LoanListItem[];
  applications: ApplicationListItem[];
  documents: any[];
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  resource_type: string;
  resource_id: string;
  description: string;
  ip_address: string;
  metadata: Record<string, any> | null;
}

export interface ComplianceEvent {
  id: string;
  event_type: string;
  description: string;
  borrower_id: string | null;
  borrower_name: string | null;
  severity: string;
  status: string;
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
}

export interface PortfolioSummary {
  total_loans: number;
  total_outstanding: number;
  total_principal: number;
  total_interest_earned: number;
  average_apr: number;
  default_rate: number;
  delinquency_rate: number;
  weighted_average_risk_score: number;
  portfolio_breakdown_by_status: Record<string, number>;
  portfolio_breakdown_by_tier: Record<string, number>;
}

export interface AdminSettings {
  app_name: string;
  environment: string;
  rate_limits: Record<string, any>;
  api_keys: {
    plaid: boolean;
    stripe: boolean;
    twilio: boolean;
    sendgrid: boolean;
  };
  [key: string]: any;
}

export interface ApplicationDecisionRequest {
  decision: 'approved' | 'declined';
  approved_amount?: number;
  term_months?: number;
  declined_reason?: string;
  declined_reason_codes?: string[];
  notes?: string;
}

// ── Admin API ─────────────────────────────────────────────────────────────────

export const adminAuthApi = {
  login: (payload: AdminLoginRequest) =>
    adminApi.post<AdminLoginResponse>('/admin/login', payload),

  setupMfa: () => adminApi.post<any>('/admin/mfa/setup'),

  verifyMfa: (mfa_code: string) =>
    adminApi.post<any>('/admin/mfa/verify', { mfa_code }),

  refresh: () =>
    adminApi.post<any>(
      '/admin/refresh',
      {},
      { headers: { Authorization: `Bearer ${getAdminRefreshToken()}` } }
    ),

  getProfile: () => adminApi.get<any>('/admin/me'),
};

export const adminDashboardApi = {
  getMetrics: () => adminApi.get<DashboardMetrics>('/admin/dashboard'),
  getPortfolioSummary: () => adminApi.get<PortfolioSummary>('/admin/portfolio/summary'),
};

export const adminApplicationsApi = {
  list: (params?: { page?: number; page_size?: number; status?: string; search?: string }) =>
    adminApi.get<PaginatedResponse<ApplicationListItem>>('/admin/applications', { params }),

  get: (id: string) => adminApi.get<ApplicationDetail>(`/admin/applications/${id}`),

  decision: (id: string, payload: ApplicationDecisionRequest) =>
    adminApi.post<any>(`/admin/applications/${id}/decision`, payload),
};

export const adminLoansApi = {
  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    adminApi.get<PaginatedResponse<LoanListItem>>('/admin/loans', { params }),

  get: (id: string) => adminApi.get<LoanDetail>(`/admin/loans/${id}`),
};

export const adminBorrowersApi = {
  list: (params?: { page?: number; page_size?: number; search?: string }) =>
    adminApi.get<PaginatedResponse<BorrowerListItem>>('/admin/borrowers', { params }),

  get: (id: string) => adminApi.get<BorrowerDetailResponse>(`/admin/borrowers/${id}`),
};

export const adminAuditLogApi = {
  list: (params?: { page?: number; page_size?: number; action?: string; actor?: string; from?: string; to?: string }) =>
    adminApi.get<PaginatedResponse<AuditLogEntry>>('/admin/audit-log', { params }),
};

export const adminComplianceApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    adminApi.get<PaginatedResponse<ComplianceEvent>>('/admin/compliance/events', { params }),
};

export const adminSettingsApi = {
  get: () => adminApi.get<AdminSettings>('/admin/settings'),
};

export const adminReportsApi = {
  applicationsCsv: (params?: Record<string, any>) =>
    adminApi.get<Blob>('/admin/reports/applications', {
      params: { ...params, format: 'csv' },
      responseType: 'blob',
    }),

  exportApplications: (params?: { status?: string; format?: string }) =>
    adminApi.get<Blob>('/admin/export/applications', {
      params: { ...params, format: 'csv' },
      responseType: 'blob',
    }),
};

export default adminApi;
