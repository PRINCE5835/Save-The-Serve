export type UserRole = "donor" | "ngo" | "driver";

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  phone?: string;
  address?: string;
  organizationName?: string;
  vehicleType?: string;
  vehicleNumber?: string;
  verified: boolean;
  avatarUrl?: string;
}

export type DonationCategory =
  | "cooked_food"
  | "clothes"
  | "blankets"
  | "medical"
  | "earmarked_money"
  | "other";

export type DonationUrgency = "normal" | "high" | "critical";

export type DonationStatus =
  | "open"
  | "claimed"
  | "in_transit"
  | "delivered"
  | "expired";

export interface DonationItem {
  id: string;
  donor_id: string;
  donor_name: string;
  donor_phone: string;
  category: DonationCategory;
  title: string;
  description: string;
  quantity: number;
  unit: string;
  prepared_at?: string;
  expires_at?: string;
  pickup_address: string;
  latitude: number;
  longitude: number;
  distance_km?: number;
  urgency: DonationUrgency;
  status: DonationStatus;
  claimed_by_ngo_id?: string;
  claimed_by_ngo_name?: string;
  claim_expires_at?: string;
  pickup_otp: string;
  dropoff_otp: string;
  target_ngo_id?: string;
  target_ngo_name?: string;
  cost_per_unit?: number;
  amount_funded?: number;
  amount_goal?: number;
  dietary_tags?: string[];
  created_at: string;
}

export interface WishlistItem {
  id: string;
  ngo_id: string;
  ngo_name: string;
  title: string;
  unit_cost: number;
  target_count: number;
  funded_count: number;
  category: DonationCategory;
  urgent: boolean;
  created_at: string;
}

export interface NGODirectoryItem {
  id: string;
  name: string;
  mission: string;
  registration_number: string;
  contact_email: string;
  phone: string;
  address: string;
  city: string;
  latitude: number;
  longitude: number;
  intake_capacity_active: boolean;
  max_daily_meals: number;
  current_daily_meals: number;
  accepted_categories: DonationCategory[];
  operating_radius_km: number;
  verified: boolean;
  rating: number;
  wishlists: WishlistItem[];
}

export interface DeliveryMission {
  id: string;
  donation_id: string;
  donation_title: string;
  category: DonationCategory;
  donor_name: string;
  donor_address: string;
  donor_phone: string;
  ngo_name: string;
  ngo_address: string;
  ngo_phone: string;
  distance_km: number;
  est_minutes: number;
  urgency: DonationUrgency;
  status: "available" | "claimed" | "picked_up" | "delivered";
  driver_id?: string;
  driver_name?: string;
  pickup_otp: string;
  dropoff_otp: string;
  proof_image_url?: string;
  created_at: string;
}

export interface SupportTicket {
  id: string;
  user_id: string;
  user_name: string;
  user_role: UserRole;
  category: "delivery" | "donation" | "ngo" | "technical" | "urgent";
  priority: "normal" | "high" | "urgent";
  subject: string;
  description: string;
  status: "open" | "in_progress" | "resolved";
  response?: string;
  created_at: string;
}
