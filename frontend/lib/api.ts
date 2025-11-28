/**
 * API Client for AI Voice Agent Backend
 * Handles authentication and all API calls
 */

// For production, default to HTTPS backend URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (
  typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')
    ? 'https://ai-voice-agent-30yv.onrender.com'
    : 'http://localhost:8000'
);

// Token storage
let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
}

export function getAuthToken(): string | null {
  if (!authToken && typeof window !== 'undefined') {
    authToken = localStorage.getItem('auth_token');
  }
  return authToken;
}

// Base fetch wrapper with auth
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    if (response.status === 401) {
      // Token expired or invalid
      setAuthToken(null);
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// ============================================
// Auth API
// ============================================

export interface LoginResponse {
  token: string;
  token_type: string;
  message: string;
  user: {
    id: string;
    username: string;
    email: string;
    full_name: string;
    client_id?: string;
    client_name?: string;
  };
  expires_in_seconds: number;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await apiFetch<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  
  setAuthToken(response.token);
  return response;
}

export async function getCurrentUser() {
  return apiFetch('/auth/me');
}

export function logout() {
  setAuthToken(null);
}

// ============================================
// Dashboard API
// ============================================

export interface DashboardStats {
  period: {
    from_date: string;
    to_date: string;
  };
  total_calls: number;
  successful_transfers: number;
  transfer_rate: number;
  total_duration_minutes: number;
  avg_duration_seconds: number;
  avg_duration_formatted: string;
  dnc_count: number;
  calls_by_tier: {
    high: number;
    mid: number;
    low: number;
    none: number;
  };
  calls_by_reason: Record<string, number>;
}

export async function getDashboardStats(params?: {
  from_date?: string;
  to_date?: string;
  agent_id?: string;
}): Promise<DashboardStats> {
  const searchParams = new URLSearchParams();
  if (params?.from_date) searchParams.set('from_date', params.from_date);
  if (params?.to_date) searchParams.set('to_date', params.to_date);
  if (params?.agent_id) searchParams.set('agent_id', params.agent_id);
  
  const query = searchParams.toString();
  return apiFetch(`/api/dashboard/stats${query ? `?${query}` : ''}`);
}

export interface AgentOverview {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  stats: {
    total_calls: number;
    successful_transfers: number;
    transfer_rate: number;
    total_duration_minutes: number;
    avg_duration_seconds: number;
  };
}

export async function getAgentsOverview(params?: {
  from_date?: string;
  to_date?: string;
}): Promise<{ period: { from_date: string; to_date: string }; agents: AgentOverview[] }> {
  const searchParams = new URLSearchParams();
  if (params?.from_date) searchParams.set('from_date', params.from_date);
  if (params?.to_date) searchParams.set('to_date', params.to_date);
  
  const query = searchParams.toString();
  return apiFetch(`/api/dashboard/agents-overview${query ? `?${query}` : ''}`);
}

// ============================================
// Calls API
// ============================================

export interface CallRecord {
  id: string;
  call_sid: string;
  from_number: string;
  to_number: string;
  lead_name: string;
  duration: number;
  duration_formatted: string;
  status: string;
  disconnection_reason: string;
  transfer_tier: string;
  transfer_success: boolean;
  is_dnc_flagged: boolean;
  total_debt: number;
  recording_url?: string;
  call_started_at?: string;
  created_at: string;
}

export interface CallsResponse {
  total: number;
  skip: number;
  limit: number;
  calls: CallRecord[];
}

export async function getCalls(params?: {
  from_date?: string;
  to_date?: string;
  agent_id?: string;
  status?: string;
  disconnection_reason?: string;
  transfer_tier?: string;
  is_dnc?: boolean;
  skip?: number;
  limit?: number;
}): Promise<CallsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.from_date) searchParams.set('from_date', params.from_date);
  if (params?.to_date) searchParams.set('to_date', params.to_date);
  if (params?.agent_id) searchParams.set('agent_id', params.agent_id);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.disconnection_reason) searchParams.set('disconnection_reason', params.disconnection_reason);
  if (params?.transfer_tier) searchParams.set('transfer_tier', params.transfer_tier);
  if (params?.is_dnc !== undefined) searchParams.set('is_dnc', String(params.is_dnc));
  if (params?.skip) searchParams.set('skip', String(params.skip));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  
  const query = searchParams.toString();
  return apiFetch(`/api/calls${query ? `?${query}` : ''}`);
}

export async function getCallDetails(callId: string) {
  return apiFetch(`/api/calls/${callId}`);
}

export async function getConcurrentCalls(): Promise<{ concurrent_calls: number; timestamp: string }> {
  return apiFetch('/api/calls/live/concurrent');
}

// ============================================
// Agents API
// ============================================

export interface Agent {
  id: string;
  name: string;
  description?: string;
  voice_config: Record<string, unknown>;
  routing_config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
}

export async function getAgents(params?: { is_active?: boolean }): Promise<{ agents: Agent[] }> {
  const searchParams = new URLSearchParams();
  if (params?.is_active !== undefined) searchParams.set('is_active', String(params.is_active));
  
  const query = searchParams.toString();
  return apiFetch(`/api/agents${query ? `?${query}` : ''}`);
}

export async function getAgent(agentId: string): Promise<Agent> {
  return apiFetch(`/api/agents/${agentId}`);
}

// ============================================
// Phone Numbers API
// ============================================

export interface PhoneNumber {
  id: string;
  number: string;
  formatted_number: string;
  friendly_name?: string;
  description?: string;
  number_type: string;
  type_label: string;
  is_active: boolean;
  last_used_at?: string;
  total_calls: string;
}

export interface PhoneNumbersResponse {
  phone_numbers: PhoneNumber[];
  grouped: Record<string, PhoneNumber[]>;
  counts: Record<string, number>;
}

export async function getPhoneNumbers(params?: { number_type?: string }): Promise<PhoneNumbersResponse> {
  const searchParams = new URLSearchParams();
  if (params?.number_type) searchParams.set('number_type', params.number_type);
  
  const query = searchParams.toString();
  return apiFetch(`/api/phone-numbers${query ? `?${query}` : ''}`);
}

export async function updatePhoneNumber(
  numberId: string,
  data: { friendly_name?: string; description?: string; number_type?: string }
): Promise<PhoneNumber> {
  return apiFetch(`/api/phone-numbers/${numberId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// ============================================
// DNC API
// ============================================

export interface DNCEntry {
  id: string;
  phone_number: string;
  reason?: string;
  detection_method: string;
  detected_phrase?: string;
  call_record_id?: string;
  flagged_at: string;
}

export interface DNCResponse {
  total: number;
  skip: number;
  limit: number;
  dnc_entries: DNCEntry[];
}

export async function getDNCEntries(params?: {
  from_date?: string;
  to_date?: string;
  skip?: number;
  limit?: number;
}): Promise<DNCResponse> {
  const searchParams = new URLSearchParams();
  if (params?.from_date) searchParams.set('from_date', params.from_date);
  if (params?.to_date) searchParams.set('to_date', params.to_date);
  if (params?.skip) searchParams.set('skip', String(params.skip));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  
  const query = searchParams.toString();
  return apiFetch(`/api/dnc${query ? `?${query}` : ''}`);
}

export async function getDNCStats(): Promise<{ total: number; today: number; by_method: Record<string, number> }> {
  return apiFetch('/api/dnc/stats');
}

export function getDNCExportUrl(params?: { from_date?: string; to_date?: string }): string {
  const searchParams = new URLSearchParams();
  if (params?.from_date) searchParams.set('from_date', params.from_date);
  if (params?.to_date) searchParams.set('to_date', params.to_date);
  
  const token = getAuthToken();
  if (token) searchParams.set('token', token); // For auth in download
  
  const query = searchParams.toString();
  return `${API_BASE_URL}/api/dnc/export${query ? `?${query}` : ''}`;
}

// ============================================
// Billing API
// ============================================

export interface BillingUsage {
  period: {
    from_date: string;
    to_date: string;
  };
  summary: {
    total_calls: number;
    total_minutes: number;
    total_transfers: number;
    avg_call_duration_seconds: number;
  };
  breakdown_by_agent: Array<{
    agent_id: string;
    agent_name: string;
    total_calls: number;
    total_minutes: number;
  }>;
  billing_note: string;
}

export async function getBillingUsage(params?: {
  from_date?: string;
  to_date?: string;
}): Promise<BillingUsage> {
  const searchParams = new URLSearchParams();
  if (params?.from_date) searchParams.set('from_date', params.from_date);
  if (params?.to_date) searchParams.set('to_date', params.to_date);
  
  const query = searchParams.toString();
  return apiFetch(`/api/billing/usage${query ? `?${query}` : ''}`);
}

export interface BillingProfile {
  has_billing_profile: boolean;
  client_id?: string;
  company_name?: string;
  billing_email?: string;
  contact_name?: string;
  contact_phone?: string;
  stripe_customer_id?: string;
  is_active?: boolean;
  payment_method?: {
    status: string;
    message: string;
  };
}

export async function getBillingProfile(): Promise<BillingProfile> {
  return apiFetch('/api/billing/profile');
}

export interface Invoice {
  id: string;
  period: {
    from_date: string;
    to_date: string;
  };
  status: string;
  amount?: number;
  notes?: string;
}

export async function getBillingHistory(params?: {
  skip?: number;
  limit?: number;
}): Promise<{ invoices: Invoice[]; total: number; billing_note: string }> {
  const searchParams = new URLSearchParams();
  if (params?.skip) searchParams.set('skip', String(params.skip));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  
  const query = searchParams.toString();
  return apiFetch(`/api/billing/history${query ? `?${query}` : ''}`);
}

// ============================================
// Transfers API
// ============================================

export async function getTransfers(params?: {
  from_date?: string;
  to_date?: string;
  agent_id?: string;
  tier?: string;
  skip?: number;
  limit?: number;
}): Promise<{ total: number; skip: number; limit: number; transfers: CallRecord[] }> {
  const searchParams = new URLSearchParams();
  if (params?.from_date) searchParams.set('from_date', params.from_date);
  if (params?.to_date) searchParams.set('to_date', params.to_date);
  if (params?.agent_id) searchParams.set('agent_id', params.agent_id);
  if (params?.tier) searchParams.set('tier', params.tier);
  if (params?.skip) searchParams.set('skip', String(params.skip));
  if (params?.limit) searchParams.set('limit', String(params.limit));
  
  const query = searchParams.toString();
  return apiFetch(`/api/dashboard/transfers${query ? `?${query}` : ''}`);
}

