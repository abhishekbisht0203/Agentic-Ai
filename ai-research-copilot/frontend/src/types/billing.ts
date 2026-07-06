import type { CurrencyCode as _CurrencyCode } from "@/lib/billing/constants";

export type CurrencyCode = _CurrencyCode;

export type SubscriptionStatus =
  | "active"
  | "canceled"
  | "incomplete"
  | "incomplete_expired"
  | "past_due"
  | "trialing"
  | "unpaid"
  | "paused";

export type BillingInterval = "month" | "year";

export type PaymentStatus =
  | "succeeded"
  | "failed"
  | "pending"
  | "refunded";

export type InvoiceStatus =
  | "draft"
  | "open"
  | "paid"
  | "uncollectible"
  | "void";

export type BillingEventType =
  | "subscription_created"
  | "subscription_updated"
  | "subscription_canceled"
  | "payment_succeeded"
  | "payment_failed"
  | "plan_upgraded"
  | "plan_downgraded";

export interface PlanLimits {
  messages: number;
  documents: number;
  knowledgeBases: number;
  agents: number;
  storageBytes: number;
}

export interface PlanFeatures {
  label: string;
  included: boolean;
}

export interface PricingPlan {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  stripeProductId: string;
  features: PlanFeatures[];
  limits: PlanLimits;
  prices: PlanPrice[];
  isPopular?: boolean;
}

export interface PlanPrice {
  id: string;
  stripePriceId: string;
  currency: string;
  amount: number;
  interval: BillingInterval;
  intervalCount: number;
  formattedAmount: string;
}

export interface UserSubscription {
  id: string;
  stripeSubscriptionId: string;
  status: SubscriptionStatus;
  interval: BillingInterval;
  currency: string;
  amount: number;
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  plan: {
    id: string;
    name: string;
    slug: string;
  };
}

export interface UsageMetric {
  metric: string;
  label: string;
  used: number;
  limit: number;
  percentage: number;
}

export interface Invoice {
  id: string;
  stripeInvoiceId: string;
  amount: number;
  currency: string;
  status: InvoiceStatus;
  invoiceNumber: string | null;
  invoiceUrl: string | null;
  pdfUrl: string | null;
  periodStart: string | null;
  periodEnd: string | null;
  paidAt: string | null;
  createdAt: string;
}

export interface Payment {
  id: string;
  amount: number;
  currency: string;
  status: PaymentStatus;
  failureReason: string | null;
  refundAmount: number | null;
  createdAt: string;
}

export interface BillingHistoryEntry {
  id: string;
  type: BillingEventType;
  description: string;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface CheckoutSessionRequest {
  priceId: string;
  currency: string;
  interval: BillingInterval;
  country?: string;
}

export interface CheckoutSessionResponse {
  sessionId: string;
  url: string;
}

export interface PortalSessionResponse {
  url: string;
}

export interface AdminBillingStats {
  mrr: number;
  arr: number;
  totalCustomers: number;
  activeSubscriptions: number;
  failedPayments: number;
  refunds: number;
  revenueByPlan: { plan: string; count: number; revenue: number }[];
  revenueByCountry: { country: string; count: number; revenue: number }[];
  revenueByCurrency: { currency: string; count: number; revenue: number }[];
  recentPayments: Payment[];
}

export interface CountryDetection {
  country: string;
  currency: string;
  language: string;
  timezone: string;
}
