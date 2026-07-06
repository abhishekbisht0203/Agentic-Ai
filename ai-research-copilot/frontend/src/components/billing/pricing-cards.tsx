"use client";

import * as React from "react";
import { motion } from "framer-motion";
import { Check, Zap, ArrowUpRight, Loader2 } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/utils/helpers";
import type { PricingPlan, BillingInterval } from "@/types/billing";
import { formatCurrency, type CurrencyCode } from "@/lib/billing";

interface PricingCardsProps {
  plans: PricingPlan[];
  currentPlanSlug: string | null;
  currency: CurrencyCode;
  interval: BillingInterval;
  onSelectPlan: (plan: PricingPlan, priceId: string) => void;
  isLoading?: boolean;
}

export function PricingCards({
  plans,
  currentPlanSlug,
  currency,
  interval,
  onSelectPlan,
  isLoading,
}: PricingCardsProps) {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      {plans.map((plan, index) => {
        const price = plan.prices.find(
          (p) => p.currency === currency && p.interval === interval
        );
        const isCurrent = currentPlanSlug === plan.slug;
        const isPopular = plan.slug === "pro";

        return (
          <motion.div
            key={plan.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, duration: 0.4 }}
          >
            <Card
              className={cn(
                "relative h-full transition-all duration-300",
                isPopular &&
                  "border-primary shadow-lg shadow-primary/10 scale-[1.02]",
                isCurrent && "border-muted-foreground/20"
              )}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                  <Badge className="px-3 py-1">
                    <Zap className="mr-1 h-3 w-3" />
                    Most Popular
                  </Badge>
                </div>
              )}
              <CardHeader className="text-center pt-8">
                <CardTitle className="text-xl">{plan.name}</CardTitle>
                <div className="flex items-baseline justify-center gap-1 mt-3">
                  {price ? (
                    <>
                      <span className="text-4xl font-bold">
                        {formatCurrency(price.amount, currency)}
                      </span>
                      <span className="text-muted-foreground text-sm">
                        /{interval === "month" ? "mo" : "yr"}
                      </span>
                    </>
                  ) : (
                    <span className="text-4xl font-bold">$0</span>
                  )}
                </div>
                {interval === "year" && price && (
                  <Badge variant="secondary" className="mt-2 w-fit mx-auto">
                    Save{" "}
                    {Math.round(
                      ((price.amount * 12 -
                        (plan.prices.find(
                          (p) =>
                            p.currency === currency && p.interval === "month"
                        )?.amount || price.amount) *
                          12) /
                        ((plan.prices.find(
                          (p) =>
                            p.currency === currency && p.interval === "month"
                        )?.amount || price.amount) *
                          12)) *
                        100
                    )}
                    %
                  </Badge>
                )}
                <CardDescription className="mt-3 min-h-[40px]">
                  {plan.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Separator />
                <ul className="space-y-2.5">
                  {plan.features.map((feature) => (
                    <li
                      key={feature.label}
                      className={cn(
                        "flex items-start gap-2.5 text-sm",
                        !feature.included && "text-muted-foreground"
                      )}
                    >
                      <Check
                        className={cn(
                          "h-4 w-4 mt-0.5 shrink-0",
                          feature.included
                            ? "text-primary"
                            : "text-muted-foreground/50"
                        )}
                      />
                      <span>{feature.label}</span>
                    </li>
                  ))}
                </ul>
                <div className="pt-4">
                  {isCurrent ? (
                    <Button
                      className="w-full"
                      variant="outline"
                      disabled
                    >
                      Current Plan
                    </Button>
                  ) : price ? (
                    <Button
                      className="w-full"
                      variant={isPopular ? "default" : "outline"}
                      disabled={isLoading}
                      onClick={() => onSelectPlan(plan, price.stripePriceId)}
                    >
                      {isLoading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <ArrowUpRight className="mr-2 h-4 w-4" />
                      )}
                      {isCurrent
                        ? "Current Plan"
                        : currentPlanSlug === "free"
                          ? "Upgrade"
                          : plan.slug === "free"
                            ? "Downgrade"
                            : "Switch Plan"}
                    </Button>
                  ) : (
                    <Button
                      className="w-full"
                      variant="outline"
                      disabled
                    >
                      Free Forever
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
