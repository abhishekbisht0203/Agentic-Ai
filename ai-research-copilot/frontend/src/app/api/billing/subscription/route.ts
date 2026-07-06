import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { getUserSubscription, getCurrentUsage } from "@/lib/billing/server";

async function getUserId(request: NextRequest): Promise<string | null> {
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
    const userId = await getUserId(request);
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const subscription = await getUserSubscription(userId);
    const usage = await getCurrentUsage(userId);

    const customer = await prisma.stripeCustomer.findUnique({
      where: { userId },
      include: {
        invoices: {
          orderBy: { createdAt: "desc" },
          take: 10,
        },
        billingHistory: {
          orderBy: { createdAt: "desc" },
          take: 20,
        },
      },
    });

    return NextResponse.json({
      subscription,
      usage,
      invoices: (customer as any)?.invoices || [],
      billingHistory: (customer as any)?.billingHistory || [],
    });
  } catch (error) {
    console.error("Get subscription error:", error);
    return NextResponse.json(
      { error: "Failed to get subscription" },
      { status: 500 }
    );
  }
}
