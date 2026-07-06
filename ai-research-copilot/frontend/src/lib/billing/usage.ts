import { prisma } from "@/lib/prisma";
import { PLAN_LIMITS, type CurrencyCode } from "./constants";
import type { PlanLimits, UsageMetric } from "@/types/billing";

export async function getPlanLimits(planSlug: string): Promise<PlanLimits> {
  if (planSlug in PLAN_LIMITS) {
    return PLAN_LIMITS[planSlug as keyof typeof PLAN_LIMITS];
  }
  return PLAN_LIMITS.free;
}

export async function getUserSubscription(userId: string) {
  const customer = await prisma.stripeCustomer.findUnique({
    where: { userId },
    include: {
      subscriptions: {
        where: {
          status: { in: ["active", "trialing", "past_due"] },
        },
        include: {
          plan: true,
          planPrice: true,
        },
        orderBy: { createdAt: "desc" },
        take: 1,
      },
    },
  });

  const subs = (customer as any)?.subscriptions;
  if (!subs || subs.length === 0) {
    return null;
  }

  const sub = subs[0];
  return {
    id: sub.id,
    stripeSubscriptionId: sub.stripeSubscriptionId,
    status: sub.status,
    interval: sub.interval,
    currency: sub.currency,
    amount: sub.amount,
    currentPeriodStart: sub.currentPeriodStart.toISOString(),
    currentPeriodEnd: sub.currentPeriodEnd.toISOString(),
    cancelAtPeriodEnd: sub.cancelAtPeriodEnd,
    plan: {
      id: sub.plan.id,
      name: sub.plan.name,
      slug: sub.plan.slug,
    },
  };
}

export async function getCurrentUsage(userId: string): Promise<UsageMetric[]> {
  const customer = await prisma.stripeCustomer.findUnique({
    where: { userId },
    include: {
      subscriptions: {
        where: {
          status: { in: ["active", "trialing", "past_due"] },
        },
        include: { plan: true },
        orderBy: { createdAt: "desc" },
        take: 1,
      },
    },
  });

  const subs = (customer as any)?.subscriptions;
  const planSlug = subs?.[0]?.plan?.slug || "free";
  const limits = await getPlanLimits(planSlug);

  const now = new Date();
  const periodStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const periodEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);

  const usageRecords = await prisma.usageRecord.findMany({
    where: {
      stripeCustomerId: customer?.stripeCustomerId || "",
      periodStart: { gte: periodStart },
      periodEnd: { lte: periodEnd },
    },
  });

  const metrics: { metric: string; label: string; limit: number }[] = [
    { metric: "ai_messages", label: "AI Messages", limit: limits.messages },
    { metric: "documents", label: "Documents", limit: limits.documents },
    { metric: "knowledge_bases", label: "Knowledge Bases", limit: limits.knowledgeBases },
    { metric: "agents", label: "AI Agents", limit: limits.agents },
    { metric: "storage_bytes", label: "Storage", limit: limits.storageBytes },
  ];

  return metrics.map((m) => {
    const record = usageRecords.find((r: (typeof usageRecords)[number]) => r.metric === m.metric);
    const used = record?.quantity || 0;
    const isUnlimited = m.limit === -1;
    const percentage = isUnlimited ? 0 : m.limit > 0 ? Math.min((used / m.limit) * 100, 100) : 0;

    return {
      metric: m.metric,
      label: m.label,
      used,
      limit: m.limit,
      percentage,
    };
  });
}

export async function checkUsageLimit(
  userId: string,
  metric: string
): Promise<{ allowed: boolean; current: number; limit: number }> {
  const customer = await prisma.stripeCustomer.findUnique({
    where: { userId },
    include: {
      subscriptions: {
        where: {
          status: { in: ["active", "trialing", "past_due"] },
        },
        include: { plan: true },
        orderBy: { createdAt: "desc" },
        take: 1,
      },
    },
  });

  const subs = (customer as any)?.subscriptions;
  const planSlug = subs?.[0]?.plan?.slug || "free";
  const limits = await getPlanLimits(planSlug);

  const limitKey = metric as keyof PlanLimits;
  const limit = limits[limitKey] ?? -1;

  if (limit === -1) {
    return { allowed: true, current: 0, limit: -1 };
  }

  const now = new Date();
  const periodStart = new Date(now.getFullYear(), now.getMonth(), 1);

  const record = await prisma.usageRecord.findFirst({
    where: {
      stripeCustomerId: customer?.stripeCustomerId || "",
      metric,
      periodStart,
    },
  });

  const current = record?.quantity || 0;
  return {
    allowed: current < limit,
    current,
    limit,
  };
}

export async function incrementUsage(
  userId: string,
  metric: string,
  quantity: number = 1
): Promise<void> {
  const customer = await prisma.stripeCustomer.findUnique({
    where: { userId },
    include: {
      subscriptions: {
        where: {
          status: { in: ["active", "trialing", "past_due"] },
        },
        orderBy: { createdAt: "desc" },
        take: 1,
      },
    },
  });

  if (!customer) return;

  const subs = (customer as any).subscriptions;
  const activeSubId = subs?.[0]?.id || null;

  const now = new Date();
  const periodStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const periodEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);

  const existing = await prisma.usageRecord.findFirst({
    where: {
      stripeCustomerId: customer.stripeCustomerId,
      metric,
      periodStart,
    },
  });

  if (existing) {
    await prisma.usageRecord.update({
      where: { id: existing.id },
      data: { quantity: { increment: quantity } },
    });
  } else {
    await prisma.usageRecord.create({
      data: {
        stripeCustomerId: customer.stripeCustomerId,
        subscriptionId: activeSubId,
        metric,
        quantity,
        periodStart,
        periodEnd,
      },
    });
  }
}

export async function resetMonthlyUsage(): Promise<void> {
  const now = new Date();
  const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59);

  await prisma.usageRecord.deleteMany({
    where: {
      periodStart: { lt: lastMonth },
      periodEnd: { lt: lastMonthEnd },
    },
  });
}
