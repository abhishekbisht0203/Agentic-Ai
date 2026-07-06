"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { CreditCard, Settings, Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  useSubscription,
  useCheckout,
  usePortal,
  useManageSubscription,
} from "@/hooks/use-billing";
import {
  PricingCards,
  UsageDisplay,
  InvoiceTable,
  BillingHistory,
  CurrentPlanCard,
  BillingToggle,
} from "@/components/billing";
import { BillingInterval } from "@/types/billing";
import type { PricingPlan } from "@/types/billing";
import {
  PLAN_FEATURES,
  CURRENCY_CONFIG,
  getSupportedCurrencies,
  DEFAULT_CURRENCY,
} from "@/lib/billing";
import type { CurrencyCode } from "@/lib/billing";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const PLANS: PricingPlan[] = [
  {
    id: "free",
    name: "Free",
    slug: "free",
    description: "For individuals getting started with AI research",
    stripeProductId: "",
    features: [...PLAN_FEATURES.free],
    limits: {
      messages: 50,
      documents: 10,
      knowledgeBases: 1,
      agents: 1,
      storageBytes: 500 * 1024 * 1024,
    },
    prices: [
      { id: "free-usd-month", stripePriceId: "", currency: "USD", amount: 0, interval: "month" as const, intervalCount: 1, formattedAmount: "$0" },
      { id: "free-usd-year", stripePriceId: "", currency: "USD", amount: 0, interval: "year" as const, intervalCount: 1, formattedAmount: "$0" },
      { id: "free-inr-month", stripePriceId: "", currency: "INR", amount: 0, interval: "month" as const, intervalCount: 1, formattedAmount: "\u20B90" },
      { id: "free-inr-year", stripePriceId: "", currency: "INR", amount: 0, interval: "year" as const, intervalCount: 1, formattedAmount: "\u20B90" },
      { id: "free-eur-month", stripePriceId: "", currency: "EUR", amount: 0, interval: "month" as const, intervalCount: 1, formattedAmount: "\u20AC0" },
      { id: "free-eur-year", stripePriceId: "", currency: "EUR", amount: 0, interval: "year" as const, intervalCount: 1, formattedAmount: "\u20AC0" },
      { id: "free-gbp-month", stripePriceId: "", currency: "GBP", amount: 0, interval: "month" as const, intervalCount: 1, formattedAmount: "\u00A30" },
      { id: "free-gbp-year", stripePriceId: "", currency: "GBP", amount: 0, interval: "year" as const, intervalCount: 1, formattedAmount: "\u00A30" },
    ],
  },
  {
    id: "pro",
    name: "Pro",
    slug: "pro",
    description: "For power users who need more capacity",
    stripeProductId: "",
    features: [...PLAN_FEATURES.pro],
    limits: {
      messages: 1000,
      documents: 100,
      knowledgeBases: 10,
      agents: 5,
      storageBytes: 10 * 1024 * 1024 * 1024,
    },
    prices: [
      { id: "pro-usd-month", stripePriceId: "", currency: "USD", amount: 2900, interval: "month" as const, intervalCount: 1, formattedAmount: "$29" },
      { id: "pro-usd-year", stripePriceId: "", currency: "USD", amount: 27800, interval: "year" as const, intervalCount: 1, formattedAmount: "$23.17" },
      { id: "pro-inr-month", stripePriceId: "", currency: "INR", amount: 199900, interval: "month" as const, intervalCount: 1, formattedAmount: "\u20B91,999" },
      { id: "pro-inr-year", stripePriceId: "", currency: "INR", amount: 1919000, interval: "year" as const, intervalCount: 1, formattedAmount: "\u20B915,991.67" },
      { id: "pro-eur-month", stripePriceId: "", currency: "EUR", amount: 2700, interval: "month" as const, intervalCount: 1, formattedAmount: "\u20AC27" },
      { id: "pro-eur-year", stripePriceId: "", currency: "EUR", amount: 25900, interval: "year" as const, intervalCount: 1, formattedAmount: "\u20AC21.58" },
      { id: "pro-gbp-month", stripePriceId: "", currency: "GBP", amount: 2300, interval: "month" as const, intervalCount: 1, formattedAmount: "\u00A323" },
      { id: "pro-gbp-year", stripePriceId: "", currency: "GBP", amount: 22100, interval: "year" as const, intervalCount: 1, formattedAmount: "\u00A318.42" },
    ],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    slug: "enterprise",
    description: "For teams and organizations with advanced needs",
    stripeProductId: "",
    features: [...PLAN_FEATURES.enterprise],
    limits: {
      messages: -1,
      documents: -1,
      knowledgeBases: -1,
      agents: -1,
      storageBytes: -1,
    },
    prices: [
      { id: "ent-usd-month", stripePriceId: "", currency: "USD", amount: 9900, interval: "month" as const, intervalCount: 1, formattedAmount: "$99" },
      { id: "ent-usd-year", stripePriceId: "", currency: "USD", amount: 95000, interval: "year" as const, intervalCount: 1, formattedAmount: "$79.17" },
      { id: "ent-inr-month", stripePriceId: "", currency: "INR", amount: 799900, interval: "month" as const, intervalCount: 1, formattedAmount: "\u20B97,999" },
      { id: "ent-inr-year", stripePriceId: "", currency: "INR", amount: 7679000, interval: "year" as const, intervalCount: 1, formattedAmount: "\u20B963,991.67" },
      { id: "ent-eur-month", stripePriceId: "", currency: "EUR", amount: 9200, interval: "month" as const, intervalCount: 1, formattedAmount: "\u20AC92" },
      { id: "ent-eur-year", stripePriceId: "", currency: "EUR", amount: 88300, interval: "year" as const, intervalCount: 1, formattedAmount: "\u20AC73.58" },
      { id: "ent-gbp-month", stripePriceId: "", currency: "GBP", amount: 7900, interval: "month" as const, intervalCount: 1, formattedAmount: "\u00A379" },
      { id: "ent-gbp-year", stripePriceId: "", currency: "GBP", amount: 75800, interval: "year" as const, intervalCount: 1, formattedAmount: "\u00A363.17" },
    ],
  },
];

export default function BillingPage() {
  const searchParams = useSearchParams();
  const [interval, setInterval] = React.useState<BillingInterval>("month");
  const [currency, setCurrency] = React.useState<CurrencyCode>(DEFAULT_CURRENCY);
  const [cancelDialogOpen, setCancelDialogOpen] = React.useState(false);
  const [resumeDialogOpen, setResumeDialogOpen] = React.useState(false);

  const { data: billingData, isLoading } = useSubscription();
  const { createCheckoutSession, isRedirecting } = useCheckout();
  const { createPortalSession } = usePortal();
  const manageMutation = useManageSubscription();

  const success = searchParams.get("success");
  const canceled = searchParams.get("canceled");

  React.useEffect(() => {
    if (success === "true") {
      toast.success("Payment successful! Your subscription is now active.");
    }
    if (canceled === "true") {
      toast.info("Checkout was canceled.");
    }
  }, [success, canceled]);

  const currentPlanSlug = billingData?.subscription?.plan?.slug || "free";
  const currentPrice =
    billingData?.subscription?.amount || 0;

  const handleSelectPlan = React.useCallback(
    (plan: PricingPlan, priceId: string) => {
      createCheckoutSession({
        priceId,
        currency,
        interval,
      });
    },
    [createCheckoutSession, currency, interval]
  );

  const handleCancelSubscription = React.useCallback(() => {
    manageMutation.mutate("cancel", {
      onSuccess: () => setCancelDialogOpen(false),
    });
  }, [manageMutation]);

  const handleResumeSubscription = React.useCallback(() => {
    manageMutation.mutate("resume", {
      onSuccess: () => setResumeDialogOpen(false),
    });
  }, [manageMutation]);

  const supportedCurrencies = getSupportedCurrencies();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <Skeleton className="h-48 w-full" />
        <div className="grid gap-6 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-96" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CreditCard className="h-6 w-6" />
            Billing & Subscription
          </h1>
          <p className="text-muted-foreground">
            Manage your subscription, usage, and payment methods
          </p>
        </div>
      </div>

      {/* Current Plan */}
      <CurrentPlanCard
        subscription={billingData?.subscription || null}
        currency={currency}
        onManageBilling={createPortalSession}
        onCancelSubscription={() => setCancelDialogOpen(true)}
        onResumeSubscription={() => setResumeDialogOpen(true)}
        isManaging={manageMutation.isPending}
      />

      {/* Usage */}
      {billingData?.usage && billingData.usage.length > 0 && (
        <UsageDisplay usage={billingData.usage} />
      )}

      {/* Plan Selection */}
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">Choose a Plan</h2>
          <div className="flex items-center gap-4">
            <Select
              value={currency}
              onValueChange={(v) => setCurrency(v as CurrencyCode)}
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {supportedCurrencies.map((c) => (
                  <SelectItem key={c} value={c}>
                    {CURRENCY_CONFIG[c].symbol} {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <BillingToggle interval={interval} onChange={setInterval} />
          </div>
        </div>

        <PricingCards
          plans={PLANS}
          currentPlanSlug={currentPlanSlug}
          currency={currency}
          interval={interval}
          onSelectPlan={handleSelectPlan}
          isLoading={isRedirecting}
        />
      </div>

      {/* Invoices */}
      {billingData?.invoices && (
        <InvoiceTable invoices={billingData.invoices} currency={currency} />
      )}

      {/* Billing History */}
      {billingData?.billingHistory && (
        <BillingHistory history={billingData.billingHistory} />
      )}

      {/* Cancel Dialog */}
      <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Subscription?</AlertDialogTitle>
            <AlertDialogDescription>
              Your subscription will remain active until the end of the current
              billing period. After that, you will be downgraded to the Free
              plan.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep Subscription</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCancelSubscription}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {manageMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Cancel Subscription
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Resume Dialog */}
      <AlertDialog open={resumeDialogOpen} onOpenChange={setResumeDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Resume Subscription?</AlertDialogTitle>
            <AlertDialogDescription>
              Your subscription will continue and you will not be downgraded.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Don't Resume</AlertDialogCancel>
            <AlertDialogAction onClick={handleResumeSubscription}>
              {manageMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Resume Subscription
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
