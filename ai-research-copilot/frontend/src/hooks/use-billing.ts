"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { billingApi } from "@/services/api/billing";
import { toast } from "sonner";
import type { BillingInterval, CheckoutSessionRequest } from "@/types/billing";

export function useSubscription() {
  return useQuery({
    queryKey: ["billing-subscription"],
    queryFn: billingApi.getSubscription,
    staleTime: 30 * 1000,
  });
}

export function useCheckout() {
  const queryClient = useQueryClient();
  const [isRedirecting, setIsRedirecting] = useState(false);

  const createCheckoutSession = useCallback(
    async (data: CheckoutSessionRequest) => {
      try {
        setIsRedirecting(true);
        const { url } = await billingApi.createCheckoutSession(data);
        if (url) {
          window.location.href = url;
        }
      } catch (error: unknown) {
        const message =
          error instanceof Error
            ? error.message
            : "Failed to create checkout session";
        toast.error(message);
        setIsRedirecting(false);
      }
    },
    []
  );

  return { createCheckoutSession, isRedirecting };
}

export function usePortal() {
  const queryClient = useQueryClient();

  const createPortalSession = useCallback(async () => {
    try {
      const { url } = await billingApi.createPortalSession();
      if (url) {
        window.location.href = url;
      }
    } catch (error: unknown) {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to open billing portal";
      toast.error(message);
    }
  }, []);

  return { createPortalSession };
}

export function useManageSubscription() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (action: "cancel" | "resume") =>
      billingApi.manageSubscription(action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["billing-subscription"] });
      toast.success("Subscription updated successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to update subscription");
    },
  });
}

export function useUsage() {
  return useQuery({
    queryKey: ["billing-usage"],
    queryFn: billingApi.getUsage,
    staleTime: 60 * 1000,
  });
}

export function useTrackUsage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ metric, quantity }: { metric: string; quantity?: number }) =>
      billingApi.trackUsage(metric, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["billing-usage"] });
    },
  });
}

export function useInvoices() {
  return useQuery({
    queryKey: ["billing-invoices"],
    queryFn: billingApi.getInvoices,
    staleTime: 60 * 1000,
  });
}

export function useAdminBillingStats() {
  return useQuery({
    queryKey: ["admin-billing-stats"],
    queryFn: billingApi.getAdminStats,
    staleTime: 60 * 1000,
  });
}

export function useBillingInterval() {
  const [interval, setInterval] = useState<BillingInterval>("month");
  return { interval, setInterval };
}
