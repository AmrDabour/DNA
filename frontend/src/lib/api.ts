/**
 * API Client for GenovaAI Backend
 */

// For client-side requests, use the public URL
// For server-side requests in Docker, use the internal service name
const getApiBaseUrl = () => {
  if (typeof window === 'undefined') {
    // Server-side: can use internal Docker network
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
  } else {
    // Client-side: must use public URL
    // In Docker, backend is exposed on port 5001, or use nginx proxy
    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    if (envUrl && envUrl.includes('backend:')) {
      // Docker internal URL, use localhost instead for browser
      return 'http://localhost:5001';
    }
    return envUrl || 'http://localhost:5001';
  }
};

const API_BASE_URL = getApiBaseUrl();

interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
  credentials?: RequestCredentials;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: options.credentials || 'include',
    };

    if (options.body) {
      config.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        return {
          success: false,
          error: data.error || data.message || 'An error occurred',
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      console.error('API Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    });
  }

  async register(username: string, email: string, password: string) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: { username, email, password },
    });
  }

  async logout() {
    return this.request('/api/auth/logout', { method: 'POST' });
  }

  async getCurrentUser() {
    return this.request('/api/auth/me');
  }

  // SNP Database endpoints
  async searchSnps(params: {
    q?: string;
    chromosome?: string;
    gene?: string;
    trait?: string;
    page?: number;
    per_page?: number;
  }) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        searchParams.append(key, String(value));
      }
    });
    return this.request(`/api/snp/search?${searchParams.toString()}`);
  }

  async getSnpById(rsId: string) {
    return this.request(`/api/snp/${rsId}`);
  }

  async getSnpStats() {
    return this.request('/api/snp/stats');
  }

  async getChromosomes() {
    return this.request<{ chromosomes: string[] }>('/api/snp/chromosomes');
  }

  async getGenes() {
    return this.request<{ genes: string[] }>('/api/snp/genes');
  }

  async getTraits() {
    return this.request<{ traits: string[] }>('/api/snp/traits');
  }

  // Prediction endpoints
  async uploadFile(formData: FormData) {
    const url = `${this.baseUrl}/api/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });
    return response.json();
  }

  async getPredictionResults(sampleId: string) {
    return this.request(`/api/predict/results/${sampleId}`);
  }

  async getPredictionHistory() {
    return this.request('/api/history');
  }

  // Risk Calculator endpoints
  async calculateRisk(data: {
    sample_id?: string;
    population?: string;
    gender?: string;
    age?: number;
    snps?: Record<string, string>;
  }) {
    return this.request('/api/risk/calculate', {
      method: 'POST',
      body: data,
    });
  }

  async getDiseases() {
    return this.request('/api/risk/diseases');
  }

  // Samples endpoints
  async getSamples() {
    return this.request('/api/samples');
  }

  async getSampleById(id: string) {
    return this.request(`/api/samples/${id}`);
  }

  // Chat/Agent endpoints
  async sendChatMessage(message: string, context?: unknown) {
    return this.request('/api/agent/chat', {
      method: 'POST',
      body: { message, context },
    });
  }

  // Dashboard endpoints
  async getDashboardStats() {
    return this.request('/api/dashboard/stats');
  }

  // Notification endpoints
  async getNotifications() {
    return this.request<{ notifications: unknown[]; unread_count: number }>('/api/notifications');
  }

  async getNotificationCount() {
    return this.request<{ count: number }>('/api/notifications/count');
  }

  async markNotificationRead(notificationId: string) {
    return this.request(`/api/notifications/${notificationId}/read`, { method: 'POST' });
  }

  async markAllNotificationsRead() {
    return this.request('/api/notifications/mark-all-read', { method: 'POST' });
  }

  async deleteNotification(notificationId: string) {
    return this.request(`/api/notifications/${notificationId}`, { method: 'DELETE' });
  }

  // Progress tracking endpoints
  async getProgress(taskId: string) {
    return this.request(`/api/progress/${taskId}`);
  }

  async updateProgress(taskId: string, data: { progress: number; message?: string; status?: string }) {
    return this.request(`/api/progress/${taskId}/update`, {
      method: 'POST',
      body: data,
    });
  }

  // Model status endpoint
  async getModelStatus() {
    return this.request<{ gender_loaded: boolean; ancestry_loaded: boolean; gender_model_dir?: string; ancestry_model_dir?: string }>('/api/models/status');
  }

  // Chat endpoint
  async chat(message: string) {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }
}

// Export singleton instance
export const api = new ApiClient(API_BASE_URL);

// Export types
export type { ApiResponse, RequestOptions };


