"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Check, Zap, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { BillingToggle } from "@/components/billing";
import { CURRENCY_CONFIG, PLAN_FEATURES } from "@/lib/billing";
import { formatCurrency } from "@/lib/billing";
import type { BillingInterval } from "@/types/billing";

const PRICING_DATA = [
  {
    id: "free",
    name: "Free",
    slug: "free",
    description: "For individuals getting started with AI research",
    prices: {
      USD: { month: 0, year: 0 },
      INR: { month: 0, year: 0 },
      EUR: { month: 0, year: 0 },
      GBP: { month: 0, year: 0 },
    },
    features: PLAN_FEATURES.free,
    isPopular: false,
  },
  {
    id: "pro",
    name: "Pro",
    slug: "pro",
    description: "For power users who need more capacity",
    prices: {
      USD: { month: 2900, year: 27800 },
      INR: { month: 199900, year: 1919000 },
      EUR: { month: 2700, year: 25900 },
      GBP: { month: 2300, year: 22100 },
    },
    features: PLAN_FEATURES.pro,
    isPopular: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    slug: "enterprise",
    description: "For teams and organizations with advanced needs",
    prices: {
      USD: { month: 9900, year: 95000 },
      INR: { month: 799900, year: 7679000 },
      EUR: { month: 9200, year: 88300 },
      GBP: { month: 7900, year: 75800 },
    },
    features: PLAN_FEATURES.enterprise,
    isPopular: false,
  },
];

const SUPPORTED_CURRENCIES: Array<keyof typeof PRICING_DATA[0]["prices"]> = ["USD", "INR", "EUR", "GBP"];

export default function PricingPage() {
  const [currency, setCurrency] = React.useState<keyof typeof PRICING_DATA[0]["prices"]>("USD");
  const [interval, setInterval] = React.useState<BillingInterval>("month");

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16 max-w-6xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold mb-4">
            Simple, transparent pricing
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Choose the plan that fits your needs. Start free, upgrade when
            you&apos;re ready.
          </p>
        </motion.div>

        {/* Controls */}
        <div className="flex items-center justify-center gap-4 mb-12">
          <Select
            value={currency}
              onValueChange={(v) => setCurrency(v as keyof typeof PRICING_DATA[0]["prices"])}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {SUPPORTED_CURRENCIES.map((c) => (
                <SelectItem key={c} value={c}>
                  {CURRENCY_CONFIG[c].symbol} {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <BillingToggle interval={interval} onChange={setInterval} />
        </div>

        {/* Pricing Cards */}
        <div className="grid gap-8 md:grid-cols-3 mb-16">
          {PRICING_DATA.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.4 }}
            >
              <Card
                className={`relative h-full ${
                  plan.isPopular
                    ? "border-primary shadow-lg shadow-primary/10 scale-[1.02]"
                    : ""
                }`}
              >
                {plan.isPopular && (
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
                    <span className="text-4xl font-bold">
                      {formatCurrency(
                        plan.prices[currency]?.[interval] || 0,
                        currency
                      )}
                    </span>
                    {plan.prices[currency]?.[interval] > 0 && (
                      <span className="text-muted-foreground text-sm">
                        /{interval === "month" ? "mo" : "yr"}
                      </span>
                    )}
                  </div>
                  {interval === "year" &&
                    plan.prices[currency]?.year > 0 && (
                      <Badge variant="secondary" className="mt-2 w-fit mx-auto">
                        Save{" "}
                        {Math.round(
                          ((plan.prices[currency].month * 12 -
                            plan.prices[currency].year) /
                            (plan.prices[currency].month * 12)) *
                            100
                        )}
                        %
                      </Badge>
                    )}
                  <CardDescription className="mt-3">
                    {plan.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Separator />
                  <ul className="space-y-2.5">
                    {plan.features.map((feature) => (
                      <li
                        key={feature.label}
                        className={`flex items-start gap-2.5 text-sm ${
                          !feature.included
                            ? "text-muted-foreground"
                            : ""
                        }`}
                      >
                        <Check
                          className={`h-4 w-4 mt-0.5 shrink-0 ${
                            feature.included
                              ? "text-primary"
                              : "text-muted-foreground/50"
                          }`}
                        />
                        <span>{feature.label}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="pt-4">
                    {plan.slug === "free" ? (
                      <Button className="w-full" variant="outline" asChild>
                        <Link href="/register">
                          Get Started Free
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Link>
                      </Button>
                    ) : (
                      <Button
                        className="w-full"
                        variant={plan.isPopular ? "default" : "outline"}
                        asChild
                      >
                        <Link href="/register">
                          Start Free Trial
                          <ArrowRight className="ml-2 h-4 w-4" />
                        </Link>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* FAQ */}
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">
            Frequently Asked Questions
          </h2>
          <p className="text-muted-foreground">
            Can&apos;t find what you&apos;re looking for?{" "}
            <Link href="/support" className="text-primary hover:underline">
              Contact support
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
