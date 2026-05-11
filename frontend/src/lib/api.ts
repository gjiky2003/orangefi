// ═══════════════════════════════════════════════════════════════════════════════
// OrangeFi — API Client (Axios-based with JWT auth, auto-refresh, typed helpers)
// ═══════════════════════════════════════════════════════════════════════════════

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  BorrowerResponse,
  PreQualifyRequest,
  PreQualifyResponse,
  ApplicationCreateRequest,
  ApplicationListItem,
  ApplicationDetail,
  LoanListItem,
  LoanDetail,
  PaymentListItem,
  MakePaymentRequest,
  MakePaymentResponse,
  PaginatedResponse,
  SuccessResponse,
  ApiError,
} from '@/src/types';

// ── Config ────────────────────────────────────────────────────────────────────

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const TOKEN_KEY = 'orangefi_access_token';
const REFRESH_KEY = 'orangefi_refresh_token';

// ── Token helpers ─────────────────────────────────────────────────────────────

export const getAccessToken = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;

export const getRefreshToken = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem(REFRESH_KEY) : null;

export const setTokens = (access: string, refresh: string) => {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
};

export const clearTokens = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
};

export const isAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;
  const token = getAccessToken();
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
};

export const getAuthHeaders = () => {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// ── Axios Instance ────────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Request interceptor — attach JWT
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — auto-refresh on 401
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: any) => void;
  reject: (reason: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) throw new Error('No refresh token');

        const { data } = await axios.post<LoginResponse>(
          `${BASE_URL}/borrowers/refresh`,
          {},
          { headers: { Authorization: `Bearer ${refreshToken}` } }
        );

        setTokens(data.access_token, data.refresh_token);
        processQueue(null, data.access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
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
    if (error.response?.status === 409) return 'Already exists';
    if (error.response?.status === 429) return 'Too many requests. Please wait.';
    if (error.code === 'ERR_NETWORK') return 'Cannot connect to server';
    return error.message || 'An unexpected error occurred';
  }
  return error?.message || 'An unexpected error occurred';
};

// ── Auth API ──────────────────────────────────────────────────────────────────

export const authApi = {
  register: (payload: RegisterRequest) =>
    api.post<LoginResponse>('/borrowers/register', {
      first_name: payload.first_name,
      last_name: payload.last_name,
      email: payload.email,
      phone: payload.phone,
      password: payload.password,
      agreed_to_tos: true,
      agreed_to_privacy: true,
    }),

  login: (payload: LoginRequest) =>
    api.post<LoginResponse>('/borrowers/login', payload),

  refresh: () =>
    api.post<LoginResponse>(
      '/borrowers/refresh',
      {},
      { headers: { Authorization: `Bearer ${getRefreshToken()}` } }
    ),

  getProfile: () => api.get<BorrowerResponse>('/borrowers/me'),

  updateProfile: (payload: Partial<BorrowerResponse>) =>
    api.put<BorrowerResponse>('/borrowers/me', payload),
};

// ── Pre-Qualification API ─────────────────────────────────────────────────────

export const preQualifyApi = {
  checkRate: (payload: PreQualifyRequest) =>
    api.post<PreQualifyResponse>('/underwriting/pre-qualify', payload),

  getTiers: () => api.get<{ success: boolean; data: { tiers: any[] } }>('/underwriting/tiers'),
};

// ── Applications API ──────────────────────────────────────────────────────────

export const applicationsApi = {
  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get<PaginatedResponse<ApplicationListItem>>('/borrowers/applications', { params }),

  create: (payload: ApplicationCreateRequest) =>
    api.post<ApplicationListItem>('/borrowers/applications', payload),

  get: (id: string) => api.get<ApplicationDetail>(`/borrowers/applications/${id}`),

  withdraw: (id: string) =>
    api.post<SuccessResponse>(`/borrowers/applications/${id}/withdraw`),
};

// ── Loans API ─────────────────────────────────────────────────────────────────

export const loansApi = {
  list: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get<PaginatedResponse<LoanListItem>>('/borrowers/loans', { params }),

  get: (id: string) => api.get<LoanDetail>(`/borrowers/loans/${id}`),
};

// ── Payments API ──────────────────────────────────────────────────────────────

export const paymentsApi = {
  list: (params?: { page?: number; page_size?: number; loan_id?: string; status?: string }) =>
    api.get<PaginatedResponse<PaymentListItem>>('/borrowers/payments', { params }),

  make: (payload: MakePaymentRequest) =>
    api.post<MakePaymentResponse>('/borrowers/payments/make', payload),
};

// ── Documents API ─────────────────────────────────────────────────────────────

export const documentsApi = {
  list: (params?: { page?: number; page_size?: number; document_type?: string }) =>
    api.get<PaginatedResponse<any>>('/borrowers/documents', { params }),

  upload: (payload: { document_type: string; file_name: string; file_size_bytes: number; mime_type?: string; application_id?: string }) =>
    api.post<SuccessResponse>('/borrowers/documents/upload', null, { params: payload }),

  delete: (id: string) =>
    api.post<SuccessResponse>(`/borrowers/documents/${id}/delete`),
};

// ── Bank Connect API ──────────────────────────────────────────────────────────

export const bankApi = {
  connect: () => api.post<SuccessResponse>('/borrowers/bank-connect'),
};

export default api;
