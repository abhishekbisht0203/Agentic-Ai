import apiClient from "./client";
import type {
  CheckoutSessionRequest,
  CheckoutSessionResponse,
  PortalSessionResponse,
  UserSubscription,
  UsageMetric,
  Invoice,
  BillingHistoryEntry,
  AdminBillingStats,
} from "@/types/billing";

export const billingApi = {
  async createCheckoutSession(
    data: CheckoutSessionRequest
  ): Promise<CheckoutSessionResponse> {
    const response = await apiClient.post("/api/billing/checkout", data);
    return response.data;
  },

  async createPortalSession(): Promise<PortalSessionResponse> {
    const response = await apiClient.post("/api/billing/portal");
    return response.data;
  },

  async getSubscription(): Promise<{
    subscription: UserSubscription | null;
    usage: UsageMetric[];
    invoices: Invoice[];
    billingHistory: BillingHistoryEntry[];
  }> {
    const response = await apiClient.get("/api/billing/subscription");
    return response.data;
  },

  async manageSubscription(
    action: "cancel" | "resume"
  ): Promise<{ success: boolean }> {
    const response = await apiClient.post("/api/billing/subscription/manage", {
      action,
    });
    return response.data;
  },

  async getUsage(): Promise<{ usage: UsageMetric[] }> {
    const response = await apiClient.get("/api/billing/usage");
    return response.data;
  },

  async trackUsage(
    metric: string,
    quantity?: number
  ): Promise<{ success: boolean }> {
    const response = await apiClient.post("/api/billing/usage", {
      metric,
      quantity,
    });
    return response.data;
  },

  async getInvoices(): Promise<{ invoices: Invoice[] }> {
    const response = await apiClient.get("/api/billing/invoices");
    return response.data;
  },

  async getAdminStats(): Promise<AdminBillingStats> {
    const response = await apiClient.get("/api/billing/admin");
    return response.data;
  },

  async verifySession(sessionId: string): Promise<{
    status: string;
    payment_status: string;
    customer: string | null;
    subscription: string | null;
  }> {
    const response = await apiClient.get(
      `/api/billing/verify-session?session_id=${sessionId}`
    );
    return response.data;
  },
};
