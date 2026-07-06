"use client";

import * as React from "react";
import { format } from "date-fns";
import { Calendar, CreditCard, ExternalLink, Loader2, XCircle } from "lucide-react";
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
import { formatCurrency, type CurrencyCode } from "@/lib/billing";
import type { UserSubscription } from "@/types/billing";

interface CurrentPlanCardProps {
  subscription: UserSubscription | null;
  currency: CurrencyCode;
  onManageBilling: () => void;
  onCancelSubscription: () => void;
  onResumeSubscription: () => void;
  isManaging?: boolean;
}

export function CurrentPlanCard({
  subscription,
  currency,
  onManageBilling,
  onCancelSubscription,
  onResumeSubscription,
  isManaging,
}: CurrentPlanCardProps) {
  const isTrialing = subscription?.status === "trialing";
  const isCanceled = subscription?.status === "canceled";
  const isPastDue = subscription?.status === "past_due";
  const cancelAtPeriodEnd = subscription?.cancelAtPeriodEnd;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Current Plan
            </CardTitle>
            <CardDescription>Your subscription details</CardDescription>
          </div>
          {subscription && (
            <Badge
              variant={
                isPastDue
                  ? "destructive"
                  : cancelAtPeriodEnd
                    ? "secondary"
                    : "default"
              }
            >
              {isPastDue
                ? "Past Due"
                : cancelAtPeriodEnd
                  ? "Canceling"
                  : isTrialing
                    ? "Trial"
                    : subscription.plan.name}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {subscription ? (
          <div className="space-y-4">
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold">
                {formatCurrency(subscription.amount, currency)}
              </span>
              <span className="text-muted-foreground">
                /{subscription.interval === "month" ? "mo" : "yr"}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {subscription.plan.name} Plan
            </p>

            <div className="grid gap-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Status</span>
                <Badge
                  variant={
                    subscription.status === "active"
                      ? "default"
                      : subscription.status === "trialing"
                        ? "secondary"
                        : "destructive"
                  }
                >
                  {subscription.status}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  Current Period
                </span>
                <span>
                  {format(new Date(subscription.currentPeriodStart), "MMM d")} -{" "}
                  {format(new Date(subscription.currentPeriodEnd), "MMM d, yyyy")}
                </span>
              </div>
              {subscription.cancelAtPeriodEnd && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground flex items-center gap-1 text-amber-600">
                    <XCircle className="h-3 w-3" />
                    Cancels At
                  </span>
                  <span className="text-amber-600">
                    {format(
                      new Date(subscription.currentPeriodEnd),
                      "MMM d, yyyy"
                    )}
                  </span>
                </div>
              )}
            </div>

            <Separator />

            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={onManageBilling}>
                <ExternalLink className="mr-2 h-4 w-4" />
                Manage Billing
              </Button>
              {cancelAtPeriodEnd ? (
                <Button
                  variant="outline"
                  onClick={onResumeSubscription}
                  disabled={isManaging}
                >
                  {isManaging ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  Resume Subscription
                </Button>
              ) : subscription.status !== "canceled" ? (
                <Button
                  variant="destructive"
                  onClick={onCancelSubscription}
                  disabled={isManaging}
                >
                  {isManaging ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  Cancel Subscription
                </Button>
              ) : null}
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-muted-foreground mb-4">
              You are on the Free plan
            </p>
            <Button variant="outline" disabled>
              Free Plan
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
