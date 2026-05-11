// ═══════════════════════════════════════════════════════════════════════════════
// OrangeFi — TypeScript Interfaces (matching backend API responses)
// ═══════════════════════════════════════════════════════════════════════════════

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  password: string;
  confirm_password?: string;
  // Optional extended fields
  middle_name?: string;
  date_of_birth?: string;
  ssn?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  zip_code?: string;
  employer?: string;
  employment_status?: string;
  monthly_income?: number;
  agreed_to_tos?: boolean;
  agreed_to_privacy?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  borrower_id: string;
  first_name: string;
  last_name: string;
  email: string;
}

// ── Borrower / Profile ────────────────────────────────────────────────────────

export interface BorrowerResponse {
  id: string;
  email: string;
  phone: string;
  first_name: string;
  middle_name: string | null;
  last_name: string;
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
}

// ── Pre-Qualification ─────────────────────────────────────────────────────────

export interface PreQualifyRequest {
  credit_score?: number;
  annual_income: number;
  requested_amount: number;
  dti_ratio?: number;
}

export interface PreQualifyResponse {
  success: boolean;
  data: {
    pre_qualified: boolean;
    tier: string;
    risk_score: number;
    risk_score_range: [number, number];
    apr_range: [number, number];
    monthly_payment_estimate: number;
    origination_fee_percent: number;
    message: string;
    factors: Record<string, any>;
  };
}

// ── Applications ──────────────────────────────────────────────────────────────

export interface ApplicationCreateRequest {
  requested_amount: number;
  requested_term_months: number;
  loan_purpose: string;
  loan_purpose_details?: string;
  total_existing_debt?: number;
  creditor_details?: Record<string, any>;
  monthly_debt_payments?: number;
  application_monthly_income?: number;
  application_employer?: string;
  application_employment_status?: string;
  years_at_current_job?: number;
  housing_status?: string;
  monthly_housing_payment?: number;
  application_metadata?: Record<string, any>;
}

export type ApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'processing'
  | 'approved'
  | 'declined'
  | 'funded'
  | 'cancelled'
  | 'prequal_submitted'
  | 'prequal_completed'
  | 'application_started';

export interface ApplicationListItem {
  id: string;
  borrower_id: string;
  borrower_name: string;
  status: ApplicationStatus;
  requested_amount: number;
  requested_term_months: number;
  loan_purpose: string;
  amount_funded: number | null;
  decisioned_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationDetail {
  id: string;
  borrower_id: string;
  borrower_name: string;
  borrower_email: string;
  status: ApplicationStatus;
  requested_amount: number;
  requested_term_months: number;
  loan_purpose: string;
  loan_purpose_details: string | null;
  total_existing_debt: number | null;
  creditor_details: Record<string, any> | null;
  monthly_debt_payments: number | null;
  application_monthly_income: number | null;
  application_employer: string | null;
  application_employment_status: string | null;
  years_at_current_job: number | null;
  housing_status: string | null;
  monthly_housing_payment: number | null;
  ip_address: string | null;
  user_agent: string | null;
  application_metadata: Record<string, any> | null;
  amount_funded: number | null;
  decisioned_at: string | null;
  decisioned_by: string | null;
  declined_reason: string | null;
  declined_reason_codes: string[] | null;
  funded_at: string | null;
  created_at: string;
  updated_at: string;
  // Underwriting result (injected separately)
  underwriting_result?: UnderwritingResult | null;
}

// ── Loans ─────────────────────────────────────────────────────────────────────

export type LoanStatus =
  | 'active'
  | 'delinquent'
  | 'paid_off'
  | 'charged_off'
  | 'defaulted'
  | 'processing';

export interface LoanListItem {
  id: string;
  application_id: string;
  borrower_id: string;
  status: LoanStatus;
  loan_amount: number;
  apr: number;
  term_months: number;
  monthly_payment: number;
  disbursement_amount: number;
  origination_fee: number;
  interest_rate_type: string;
  interest_accrued: number;
  days_past_due: number;
  total_amount_due: number;
  collections_status: string | null;
  origination_date: string;
  first_payment_date: string | null;
  maturity_date: string | null;
  paid_off_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentScheduleItem {
  payment_number: number;
  scheduled_date: string;
  total_amount: number;
  principal_amount: number;
  interest_amount: number;
  fees_amount: number | null;
  remaining_balance: number | null;
  status: string;
}

export interface RecentPayment {
  id: string;
  payment_number: number;
  status: string;
  scheduled_date: string;
  paid_date: string | null;
  total_amount: number;
  amount_paid: number | null;
  payment_method: string | null;
}

export interface LoanDetail {
  id: string;
  application_id: string;
  borrower_id: string;
  borrower_name: string;
  status: LoanStatus;
  loan_amount: number;
  apr: number;
  term_months: number;
  monthly_payment: number;
  disbursement_amount: number;
  origination_fee: number;
  interest_rate_type: string;
  interest_accrued: number;
  days_past_due: number;
  total_amount_due: number;
  collections_status: string | null;
  origination_date: string;
  first_payment_date: string | null;
  maturity_date: string | null;
  paid_off_at: string | null;
  funding_account_id: string | null;
  funding_reference: string | null;
  charge_off_reason: string | null;
  delinquency_started_at: string | null;
  last_interest_calc_at: string | null;
  payment_schedule: PaymentScheduleItem[];
  recent_payments: RecentPayment[];
  created_at: string;
  updated_at: string;
}

// ── Payments ──────────────────────────────────────────────────────────────────

export type PaymentStatus =
  | 'scheduled'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'refunded'
  | 'cancelled';

export interface PaymentListItem {
  id: string;
  loan_id: string;
  borrower_id: string;
  payment_number: number;
  status: PaymentStatus;
  scheduled_date: string;
  paid_date: string | null;
  period_start: string | null;
  period_end: string | null;
  total_amount: number;
  principal_amount: number;
  interest_amount: number;
  fees_amount: number;
  late_fee: number;
  amount_paid: number | null;
  payment_method: string | null;
  payment_source: string | null;
  external_reference: string | null;
  external_status: string | null;
  failure_reason: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export interface MakePaymentRequest {
  loan_id: string;
  amount: number;
  payment_method: string;
  payment_source_id?: string;
  payment_number?: number;
  idempotency_key?: string;
}

export interface MakePaymentResponse {
  payment_id: string;
  loan_id: string;
  payment_number: number;
  amount: number;
  status: string;
  message: string;
  estimated_completion: string | null;
  idempotency_key: string | null;
}

// ── Underwriting ──────────────────────────────────────────────────────────────

export interface UnderwritingResult {
  application_id: string;
  decision: string;
  risk_score: number;
  risk_tier: string;
  apr: number | null;
  approved_amount: number | null;
  term_months: number | null;
  monthly_payment: number | null;
  adverse_action_codes: string[];
  factors: Record<string, any>;
  pricing_tier: string | null;
}

export interface PricingTier {
  name: string;
  min_risk_score: number;
  max_risk_score: number;
  apr_range: [number, number];
  origination_fee_percent: number;
}

// ── Generic / Common ──────────────────────────────────────────────────────────

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

export interface ApiError {
  success: boolean;
  error: string;
  detail: string | null;
  code: string | null;
  status_code: number;
  validation_errors?: { field: string; message: string; code: string }[];
  request_id: string | null;
  timestamp: string;
}

export interface SuccessResponse {
  message: string;
  data?: Record<string, any>;
}
