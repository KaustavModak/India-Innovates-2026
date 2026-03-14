/**
 * API client for the Election Audit backend.
 */

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';

export interface VerificationResult {
  id: string;
  submitted_hash: string;
  status: 'pending' | 'verified' | 'tampered' | 'error';
  is_verified: boolean;
  blockchain_verified: boolean;
  blockchain_tx_id: string | null;
  matched_record: HashRecord | null;
  result_details: Record<string, any>;
  verified_at: string;
}

export interface HashRecord {
  id: string;
  result_file_id: string;
  sha256_hash: string;
  hash_algorithm: string;
  file_size_bytes: number;
  blockchain_tx_id: string | null;
  blockchain_block_number: number | null;
  blockchain_timestamp: string | null;
  is_on_blockchain: boolean;
  created_at: string;
}

export interface Constituency {
  id: string;
  name: string;
  code: string;
  state: string;
  district: string | null;
  country: string;
  total_registered_voters: number | null;
  created_at: string;
}

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string | null;
  details: Record<string, any>;
  success: boolean;
  created_at: string;
}

export interface AuditLogList {
  total: number;
  page: number;
  per_page: number;
  logs: AuditLog[];
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // --- Verification (Public) ---

  async verifyResult(fileHash: string): Promise<VerificationResult> {
    return this.request<VerificationResult>(`/verify/result/${fileHash}`);
  }

  async getConstituencies(state?: string): Promise<Constituency[]> {
    const params = state ? `?state=${encodeURIComponent(state)}` : '';
    return this.request<Constituency[]>(`/verify/constituencies${params}`);
  }

  async getAuditLogs(page = 1, perPage = 20): Promise<AuditLogList> {
    return this.request<AuditLogList>(`/verify/audit-logs?page=${page}&per_page=${perPage}`);
  }

  // --- Auth ---

  async login(email: string, password: string) {
    return this.request<{ access_token: string; requires_mfa: boolean; mfa_session_token?: string }>(
      '/auth/login',
      { method: 'POST', body: JSON.stringify({ email, password }) }
    );
  }

  async verifyMfa(sessionToken: string, code: string) {
    return this.request<{ access_token: string }>(
      '/auth/mfa-verify',
      { method: 'POST', body: JSON.stringify({ session_token: sessionToken, mfa_code: code }) }
    );
  }

  // --- Upload (Authenticated) ---

  async uploadResult(file: File, constituencyId: string, electionDate: string, electionType: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('constituency_id', constituencyId);
    formData.append('election_date', electionDate);
    formData.append('election_type', electionType);

    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}/upload/result`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  // --- Hash ---

  async generateHash(resultFileId: string) {
    return this.request('/hash/generate', {
      method: 'POST',
      body: JSON.stringify({ result_file_id: resultFileId }),
    });
  }

  async storeHash(hashRecordId: string) {
    return this.request('/hash/store', {
      method: 'POST',
      body: JSON.stringify({ hash_record_id: hashRecordId }),
    });
  }
}

export const api = new ApiClient(API_BASE);
