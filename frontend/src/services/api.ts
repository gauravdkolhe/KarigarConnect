import type {
  AdminMetrics,
  AuthResponse,
  BuyerRequirement,
  ImageStyleOption,
  InAppNotification,
  Inquiry,
  ProductMatch,
  UserProfile,
  WorkflowState,
} from '../types';

export const API_BASE =
  import.meta.env.VITE_API_URL ||
  (typeof window !== 'undefined'
    ? (window.location.port === '8000'
        ? ''
        : `${window.location.protocol}//${window.location.hostname}:8000`)
    : 'http://127.0.0.1:8000');

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('karigar_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('karigar_token');
    localStorage.removeItem('karigar_user');
  }

  if (!response.ok) {
    let errorDetail = `Request failed (${response.status})`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Authentication
  async register(data: any): Promise<UserProfile> {
    return request<UserProfile>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('karigar_token', res.access_token);
    localStorage.setItem('karigar_user', JSON.stringify(res.user));
    return res;
  },

  async getMe(): Promise<UserProfile> {
    return request<UserProfile>('/api/auth/me');
  },

  async updateMe(data: any): Promise<UserProfile> {
    const updated = await request<UserProfile>('/api/auth/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    localStorage.setItem('karigar_user', JSON.stringify(updated));
    return updated;
  },

  logout(): void {
    localStorage.removeItem('karigar_token');
    localStorage.removeItem('karigar_user');
  },

  // Four-Agent Workflow
  async createProductDraft(data: {
    product_name: string;
    category: string;
    initial_material: string;
    initial_craft_type?: string;
  }): Promise<WorkflowState> {
    return request<WorkflowState>('/api/workflow/products', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async listArtisanProducts(): Promise<{ total_records: number; products: any[] }> {
    return request<{ total_records: number; products: any[] }>('/api/workflow/products');
  },

  async getProductWorkflow(productId: string): Promise<WorkflowState> {
    return request<WorkflowState>(`/api/workflow/products/${productId}`);
  },

  async getImageStyles(): Promise<{ styles: ImageStyleOption[]; default: string }> {
    return request<{ styles: ImageStyleOption[]; default: string }>('/api/images/styles');
  },

  async uploadProductImage(
    productId: string,
    file: File,
    style: string = 'studio_white'
  ): Promise<any> {
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('file', file);
    formData.append('style', style);

    const token = localStorage.getItem('karigar_token');
    const response = await fetch(`${API_BASE}/api/images/enhance`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Image enhancement failed.');
    }
    return response.json();
  },

  async restyleProductImage(
    imageId: string,
    style: string
  ): Promise<any> {
    const formData = new FormData();
    formData.append('style', style);

    const token = localStorage.getItem('karigar_token');
    const response = await fetch(`${API_BASE}/api/images/${imageId}/restyle`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Image re-styling failed.');
    }
    return response.json();
  },

  async generateAICatalog(productId: string): Promise<WorkflowState> {
    return request<WorkflowState>(`/api/workflow/products/${productId}/ai-catalog`, {
      method: 'POST',
    });
  },

  async approveCatalog(productId: string, data: any): Promise<WorkflowState> {
    return request<WorkflowState>(`/api/workflow/products/${productId}/catalog`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async calculatePricing(productId: string, data: any): Promise<WorkflowState> {
    return request<WorkflowState>(`/api/workflow/products/${productId}/pricing`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async saveInventory(productId: string, data: any): Promise<WorkflowState> {
    return request<WorkflowState>(`/api/workflow/products/${productId}/inventory`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async publishProduct(productId: string): Promise<WorkflowState> {
    return request<WorkflowState>(`/api/workflow/products/${productId}/publish`, {
      method: 'POST',
    });
  },

  async getProductMatches(productId: string, minScore = 30): Promise<{ matches: ProductMatch[] }> {
    return request<{ matches: ProductMatch[] }>(
      `/api/workflow/products/${productId}/matches?min_score=${minScore}`
    );
  },

  // Buyer Requirements
  async createRequirement(data: any): Promise<BuyerRequirement> {
    return request<BuyerRequirement>('/api/buyers/requirements', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async listRequirements(status = 'active', category?: string): Promise<{ requirements: BuyerRequirement[] }> {
    let url = `/api/buyers/requirements?status=${status}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    return request<{ requirements: BuyerRequirement[] }>(url);
  },

  async getRequirement(requirementId: string, authorized = false): Promise<BuyerRequirement> {
    return request<BuyerRequirement>(`/api/buyers/requirements/${requirementId}?authorized=${authorized}`);
  },

  async updateRequirementStatus(requirementId: string, status: string): Promise<BuyerRequirement> {
    return request<BuyerRequirement>(`/api/buyers/requirements/${requirementId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ requirement_status: status }),
    });
  },

  async getBuyerMatches(requirementId: string, minScore = 30): Promise<{ matches: ProductMatch[] }> {
    return request<{ matches: ProductMatch[] }>(
      `/api/market-linkage/buyer/${requirementId}/matches?min_score=${minScore}`
    );
  },

  // Inquiries
  async submitInquiry(data: any): Promise<Inquiry> {
    return request<Inquiry>('/api/inquiries', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async listInquiries(statusFilter?: string): Promise<{ inquiries: Inquiry[] }> {
    const url = statusFilter ? `/api/inquiries?status_filter=${statusFilter}` : '/api/inquiries';
    return request<{ inquiries: Inquiry[] }>(url);
  },

  async updateInquiryStatus(inquiryId: string, status: string, responseNote?: string): Promise<Inquiry> {
    return request<Inquiry>(`/api/inquiries/${inquiryId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, artisan_response_note: responseNote }),
    });
  },

  // Notifications
  async listNotifications(): Promise<{ notifications: InAppNotification[] }> {
    return request<{ notifications: InAppNotification[] }>('/api/notifications');
  },

  async markNotificationRead(notificationId: string): Promise<{ status: string }> {
    return request<{ status: string }>(`/api/notifications/${notificationId}/read`, {
      method: 'PATCH',
    });
  },

  async markAllNotificationsRead(): Promise<{ marked_read: number }> {
    return request<{ marked_read: number }>('/api/notifications/read-all', {
      method: 'POST',
    });
  },

  // Admin Oversight
  async getAdminMetrics(): Promise<AdminMetrics> {
    return request<AdminMetrics>('/api/admin/metrics');
  },

  async listAdminUsers(role?: string, status?: string): Promise<{ total_users: number; users: UserProfile[] }> {
    let url = '/api/admin/users?';
    if (role) url += `role=${role}&`;
    if (status) url += `status=${status}&`;
    return request<{ total_users: number; users: UserProfile[] }>(url);
  },

  async updateUserStatus(userId: string, status: string, reason: string): Promise<any> {
    return request<any>(`/api/admin/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, reason }),
    });
  },

  async listAdminProducts(statusFilter?: string): Promise<{ total_products: number; products: any[] }> {
    const url = statusFilter ? `/api/admin/products?status_filter=${statusFilter}` : '/api/admin/products';
    return request<{ total_products: number; products: any[] }>(url);
  },

  async moderateProduct(productId: string, workflowStatus: string, moderationNote?: string): Promise<any> {
    return request<any>(`/api/admin/products/${productId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ workflow_status: workflowStatus, moderation_note: moderationNote }),
    });
  },
};
