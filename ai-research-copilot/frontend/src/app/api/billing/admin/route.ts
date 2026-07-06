import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { formatCurrency } from "@/lib/billing";
import type { CurrencyCode } from "@/lib/billing";

async function getAdminUserId(request: NextRequest): Promise<string | null> {
  const token =
    request.cookies.get("access_token")?.value ||
    request.headers.get("authorization")?.replace("Bearer ", "");
  if (!token) return null;

  try {
    const payload = JSON.parse(
      Buffer.from(token.split(".")[1], "base64").toString()
    );
    return payload.sub || payload.user_id || null;
  } catch {
    return null;
  }
}

export async function GET(request: NextRequest) {
  try {
    const userId = await getAdminUserId(request);
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const customer = await prisma.stripeCustomer.findUnique({
      where: { userId },
    });

    const now = new Date();
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const [
      totalCustomers,
      activeSubscriptions,
      allSubscriptions,
      recentPayments,
      failedPayments,
      refunds,
    ] = await Promise.all([
      prisma.stripeCustomer.count(),
      prisma.subscription.count({
        where: { status: { in: ["active", "trialing"] } },
      }),
      prisma.subscription.findMany({
        where: { status: { in: ["active", "trialing"] } },
        include: { plan: true, planPrice: true },
      }),
      prisma.payment.findMany({
        where: { createdAt: { gte: thirtyDaysAgo } },
        orderBy: { createdAt: "desc" },
        take: 50,
      }),
      prisma.payment.count({
        where: { status: "failed", createdAt: { gte: thirtyDaysAgo } },
      }),
      prisma.payment.aggregate({
        where: {
          status: "refunded",
          createdAt: { gte: thirtyDaysAgo },
        },
        _sum: { refundAmount: true },
      }),
    ]);

    let mrr = 0;
    const revenueByPlan: Record<string, { count: number; revenue: number }> = {};
    const revenueByCountry: Record<string, { count: number; revenue: number }> = {};
    const revenueByCurrency: Record<string, { count: number; revenue: number }> = {};

    for (const sub of allSubscriptions) {
      const monthlyAmount =
        sub.interval === "year" ? sub.amount / 12 : sub.amount;
      mrr += monthlyAmount;

      const planName = sub.plan.name;
      if (!revenueByPlan[planName]) {
        revenueByPlan[planName] = { count: 0, revenue: 0 };
      }
      revenueByPlan[planName].count += 1;
      revenueByPlan[planName].revenue += monthlyAmount;

      const cur = sub.currency.toUpperCase();
      if (!revenueByCurrency[cur]) {
        revenueByCurrency[cur] = { count: 0, revenue: 0 };
      }
      revenueByCurrency[cur].count += 1;
      revenueByCurrency[cur].revenue += monthlyAmount;
    }

    const customerCountries = await prisma.stripeCustomer.groupBy({
      by: ["country"],
      _count: { country: true },
    });

    for (const cc of customerCountries) {
      if (cc.country) {
        revenueByCountry[cc.country] = {
          count: cc._count.country,
          revenue: 0,
        };
      }
    }

    const stats = {
      mrr,
      arr: mrr * 12,
      totalCustomers,
      activeSubscriptions,
      failedPayments,
      refunds: refunds._sum.refundAmount || 0,
      revenueByPlan: Object.entries(revenueByPlan).map(([plan, data]) => ({
        plan,
        ...data,
      })),
      revenueByCountry: Object.entries(revenueByCountry).map(
        ([country, data]) => ({
          country,
          ...data,
        })
      ),
      revenueByCurrency: Object.entries(revenueByCurrency).map(
        ([currency, data]) => ({
          currency,
          ...data,
        })
      ),
      recentPayments: recentPayments.map((p: (typeof recentPayments)[number]) => ({
        ...p,
        formattedAmount: formatCurrency(p.amount, p.currency as CurrencyCode),
      })),
    };

    return NextResponse.json(stats);
  } catch (error) {
    console.error("Admin billing stats error:", error);
    return NextResponse.json(
      { error: "Failed to get billing stats" },
      { status: 500 }
    );
  }
}
