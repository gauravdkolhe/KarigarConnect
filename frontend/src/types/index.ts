export type UserRole = 'artisan' | 'buyer' | 'admin';

export interface UserProfile {
  user_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  status: 'active' | 'suspended';
  phone_number?: string;
  phone?: string;
  location?: string;
  business_name?: string;
  craft_type?: string;
  product_categories?: string[];
  workshop_location?: string;
  short_bio?: string;
  bio?: string;
  buyer_type?: string;
  procurement_interests?: string[];
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export type WorkflowStatus =
  | 'draft'
  | 'image_uploaded'
  | 'catalog_pending'
  | 'catalog_approved'
  | 'pricing_calculated'
  | 'inventory_configured'
  | 'published'
  | 'archived';

export interface ImageStyleOption {
  key: string;
  name: string;
  description: string;
  bg_color: [number, number, number];
  has_shadow: boolean;
  warm_tint: boolean;
}

export interface ProductImage {
  image_id: string;
  enhanced_filename?: string;
  file_url: string;
  original_dimensions?: number[];
  enhanced_dimensions?: number[];
  style_applied?: {
    key: string;
    name: string;
    description: string;
    bg_color: number[];
  };
  settings?: Record<string, any>;
}

export interface ProductCatalog {
  product_id: string;
  product_name: string;
  product_title: string;
  description: string;
  keywords: string[];
  language: string;
  product_details?: {
    material?: string;
    craft_type?: string;
    color?: string;
    purpose?: string;
  };
  requires_artisan_review?: boolean;
}

export interface PricingRecord {
  product_id: string;
  suggested_selling_price: number;
  total_cost: number;
  estimated_profit: number;
  estimated_profit_margin_percent: number;
  currency: string;
  pricing_method: string;
  pricing_strategy: string;
  cost_breakdown?: {
    material_cost: number;
    labor_cost: number;
    packaging_cost: number;
    overhead_cost: number;
    shipping_cost: number;
    other_variable_costs: number;
    base_production_cost: number;
    total_seller_cost: number;
  };
  fee_breakdown?: {
    marketplace_commission_percent: number;
    marketplace_commission_amount: number;
    discount_percent: number;
    discount_amount: number;
    tax_rate_percent?: number | null;
    tax_amount: number;
  };
  explanation?: string;
  warnings?: string[];
}

export interface ArtisanInventory {
  product_id: string;
  artisan_id: string;
  available_quantity: number;
  production_capacity_per_month: number;
  minimum_order_quantity: number;
  unit_price?: number;
  currency: string;
  production_lead_time_days: number;
  location: string;
}

export interface ProductMatch {
  match_id: string;
  product_id: string;
  requirement_id: string;
  product_title: string;
  buyer_name: string;
  buyer_type: string;
  match_score: number;
  match_category: 'Excellent' | 'Good' | 'Moderate' | 'Conditional' | 'Not eligible';
  compatibility: {
    category: boolean;
    material: boolean;
    craft_type: boolean;
    budget: boolean;
    quantity: boolean;
    delivery: boolean;
    location: boolean;
  };
  score_breakdown: {
    category_score: number;
    keyword_score: number;
    material_score: number;
    craft_type_score: number;
    price_score: number;
    quantity_score: number;
    location_score: number;
    delivery_score: number;
    total_score: number;
  };
  warnings: string[];
  recommendation: string;
  buyer_summary: {
    buyer_id: string;
    buyer_name: string;
    buyer_type: string;
    delivery_location: string;
    required_quantity: number;
    budget_range: string;
    delivery_deadline_days: number;
    contact_email_masked?: string;
    contact_phone_masked?: string;
  };
  artisan_summary?: {
    product_id: string;
    product_title: string;
    unit_price: string;
    material: string;
    available_quantity: number;
    monthly_capacity: number;
    lead_time_days: number;
  };
}

export interface WorkflowState {
  product_id: string;
  artisan_id: string;
  product_name: string;
  workflow_status: WorkflowStatus;
  steps_completed: string[];
  images: ProductImage[];
  catalog?: ProductCatalog | null;
  pricing?: PricingRecord | null;
  inventory?: ArtisanInventory | null;
  match_count: number;
  created_at: string;
  updated_at: string;
}

export interface BuyerRequirement {
  requirement_id: string;
  buyer_id: string;
  buyer_name: string;
  buyer_type: string;
  required_category: string;
  requirement_title: string;
  description: string;
  required_keywords: string[];
  preferred_materials: string[];
  preferred_craft_types: string[];
  required_quantity: number;
  minimum_budget: number;
  maximum_budget: number;
  currency: string;
  delivery_location: string;
  delivery_deadline_days: number;
  contact_email?: string;
  contact_phone?: string;
  requirement_status: 'draft' | 'active' | 'paused' | 'fulfilled' | 'cancelled';
  created_at: string;
  updated_at: string;
}

export interface Inquiry {
  inquiry_id: string;
  product_id: string;
  product_name: string;
  artisan_id: string;
  buyer_id: string;
  buyer_name: string;
  buyer_business?: string;
  buyer_contact_email?: string;
  buyer_contact_phone?: string;
  requirement_id?: string;
  quantity_requested: number;
  target_price_per_unit?: number;
  delivery_destination: string;
  message: string;
  status: 'pending' | 'accepted' | 'replied' | 'declined' | 'closed';
  artisan_response_note?: string;
  created_at: string;
  updated_at: string;
}

export interface InAppNotification {
  notification_id: string;
  user_id: string;
  title: string;
  message: string;
  notification_type: string;
  reference_id?: string;
  is_read: boolean;
  created_at: string;
}

export interface AdminMetrics {
  total_artisans: number;
  total_buyers: number;
  total_products: number;
  published_products: number;
  total_requirements: number;
  active_requirements: number;
  total_inquiries: number;
  total_pricing_records: number;
  categories_breakdown: Array<{ category: string; count: number }>;
  generated_at: string;
}
