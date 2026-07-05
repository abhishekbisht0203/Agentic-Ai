"use client";

import * as React from "react";
import {
  CreditCard,
  Check,
  Zap,
  Building2,
  MessageSquare,
  FileText,
  Database,
  Bot,
  ArrowUpRight,
  ExternalLink,
  Loader2,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuthStore } from "@/store/auth-store";

const plans = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    description: "For individuals getting started with AI research",
    features: [
      "50 AI messages per month",
      "10 documents uploaded",
      "1 knowledge base",
      "1 AI agent",
      "Basic analytics",
      "Community support",
    ],
    limits: {
      messages: 50,
      documents: 10,
      knowledgeBases: 1,
      agents: 1,
    },
    cta: "Current Plan",
    current: true,
  },
  {
    id: "pro",
    name: "Pro",
    price: "$29",
    period: "/month",
    description: "For power users who need more capacity",
    features: [
      "1,000 AI messages per month",
      "100 documents uploaded",
      "10 knowledge bases",
      "5 AI agents",
      "Advanced analytics & reports",
      "Priority support",
      "Custom AI models",
      "API access",
    ],
    limits: {
      messages: 1000,
      documents: 100,
      knowledgeBases: 10,
      agents: 5,
    },
    cta: "Upgrade to Pro",
    current: false,
    popular: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "$99",
    period: "/month",
    description: "For teams and organizations with advanced needs",
    features: [
      "Unlimited AI messages",
      "Unlimited documents",
      "Unlimited knowledge bases",
      "Unlimited AI agents",
      "Custom analytics dashboards",
      "Dedicated support",
      "Custom AI models",
      "Full API access",
      "SSO & team management",
      "SLA guarantee",
    ],
    limits: {
      messages: Infinity,
      documents: Infinity,
      knowledgeBases: Infinity,
      agents: Infinity,
    },
    cta: "Upgrade to Enterprise",
    current: false,
  },
];

const mockUsage = {
  messages: { used: 23, total: 50 },
  documents: { used: 4, total: 10 },
  knowledgeBases: { used: 1, total: 1 },
  agents: { used: 1, total: 1 },
};

const mockInvoices = [
  {
    id: "inv_001",
    date: "2025-01-01",
    amount: "$0.00",
    status: "paid",
    description: "Free Plan - January 2025",
  },
];

export default function BillingPage() {
  const { user } = useAuthStore();
  const [isUpgrading, setIsUpgrading] = React.useState<string | null>(null);

  const currentPlan = plans.find((p) => p.current) || plans[0];

  const usageStats = [
    {
      label: "AI Messages",
      used: mockUsage.messages.used,
      total: mockUsage.messages.total,
      icon: MessageSquare,
    },
    {
      label: "Documents",
      used: mockUsage.documents.used,
      total: mockUsage.documents.total,
      icon: FileText,
    },
    {
      label: "Knowledge Bases",
      used: mockUsage.knowledgeBases.used,
      total: mockUsage.knowledgeBases.total,
      icon: Database,
    },
    {
      label: "AI Agents",
      used: mockUsage.agents.used,
      total: mockUsage.agents.total,
      icon: Bot,
    },
  ];

  const handleUpgrade = (planId: string) => {
    setIsUpgrading(planId);
    setTimeout(() => {
      setIsUpgrading(null);
      alert(
        `Upgrade to ${planId} will redirect to payment. This is a demo.`
      );
    }, 1500);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Billing</h1>
        <p className="text-muted-foreground">
          Manage your subscription and view usage
        </p>
      </div>

      {/* Current Plan Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Current Plan
              </CardTitle>
              <CardDescription>
                Your current subscription plan
              </CardDescription>
            </div>
            <Badge variant="secondary" className="text-sm">
              {currentPlan.name}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-baseline gap-1 mb-4">
            <span className="text-3xl font-bold">{currentPlan.price}</span>
            <span className="text-muted-foreground">
              {currentPlan.period}
            </span>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            {currentPlan.description}
          </p>
          <Button variant="outline" disabled>
            {currentPlan.cta}
          </Button>
        </CardContent>
      </Card>

      {/* Usage */}
      <Card>
        <CardHeader>
          <CardTitle>Usage This Month</CardTitle>
          <CardDescription>
            Track your resource consumption
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2">
            {usageStats.map((stat) => {
              const percentage =
                stat.total === Infinity
                  ? 0
                  : Math.round((stat.used / stat.total) * 100);
              return (
                <div key={stat.label} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <stat.icon className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">
                        {stat.label}
                      </span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {stat.used} / {stat.total === Infinity ? "∞" : stat.total}
                    </span>
                  </div>
                  <Progress
                    value={percentage}
                    className="h-2"
                  />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Plan Comparison */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Available Plans</h2>
        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <Card
              key={plan.id}
              className={`relative ${
                plan.popular
                  ? "border-primary shadow-md"
                  : ""
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="px-3">
                    <Zap className="mr-1 h-3 w-3" />
                    Most Popular
                  </Badge>
                </div>
              )}
              <CardHeader className="text-center pt-8">
                <CardTitle>{plan.name}</CardTitle>
                <div className="flex items-baseline justify-center gap-1 mt-2">
                  <span className="text-3xl font-bold">{plan.price}</span>
                  <span className="text-muted-foreground text-sm">
                    {plan.period}
                  </span>
                </div>
                <CardDescription className="mt-2">
                  {plan.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Separator />
                <ul className="space-y-2">
                  {plan.features.map((feature) => (
                    <li
                      key={feature}
                      className="flex items-start gap-2 text-sm"
                    >
                      <Check className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button
                  className="w-full mt-4"
                  variant={plan.current ? "outline" : "default"}
                  disabled={plan.current || isUpgrading !== null}
                  onClick={() => handleUpgrade(plan.id)}
                >
                  {isUpgrading === plan.id ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : plan.current ? null : (
                    <ArrowUpRight className="mr-2 h-4 w-4" />
                  )}
                  {isUpgrading === plan.id
                    ? "Upgrading..."
                    : plan.cta}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Billing History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Billing History</CardTitle>
              <CardDescription>
                View your past invoices
              </CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <ExternalLink className="mr-2 h-4 w-4" />
              Manage Billing
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockInvoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell>
                    {new Date(invoice.date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>{invoice.description}</TableCell>
                  <TableCell className="font-medium">
                    {invoice.amount}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        invoice.status === "paid" ? "default" : "secondary"
                      }
                    >
                      {invoice.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
