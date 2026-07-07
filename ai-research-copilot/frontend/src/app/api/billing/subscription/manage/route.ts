import { NextRequest, NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";
import { prisma } from "@/lib/prisma";

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

export async function POST(request: NextRequest) {
  try {
    const userId = await getUserId(request);
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { action } = body;

    if (!["cancel", "resume"].includes(action)) {
      return NextResponse.json(
        { error: "Invalid action. Must be 'cancel' or 'resume'" },
        { status: 400 }
      );
    }

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

    const subs = (customer as any)?.subscriptions;
    if (!subs || subs.length === 0) {
      return NextResponse.json(
        { error: "No active subscription found" },
        { status: 404 }
      );
    }

    const activeSub = subs[0];

    if (action === "cancel") {
      await getStripe().subscriptions.update(
        activeSub.stripeSubscriptionId,
        {
          cancel_at_period_end: true,
        }
      );

      await prisma.subscription.update({
        where: { id: activeSub.id },
        data: { cancelAtPeriodEnd: true },
      });

      await prisma.billingHistory.create({
        data: {
          stripeCustomerId: customer!.stripeCustomerId,
          type: "subscription_canceled",
          description: "Subscription cancellation scheduled at period end",
        },
      });
    } else if (action === "resume") {
      if (!activeSub.cancelAtPeriodEnd) {
        return NextResponse.json(
          { error: "Subscription is not scheduled for cancellation" },
          { status: 400 }
        );
      }

      await getStripe().subscriptions.update(
        activeSub.stripeSubscriptionId,
        {
          cancel_at_period_end: false,
        }
      );

      await prisma.subscription.update({
        where: { id: activeSub.id },
        data: { cancelAtPeriodEnd: false },
      });

      await prisma.billingHistory.create({
        data: {
          stripeCustomerId: customer!.stripeCustomerId,
          type: "subscription_updated",
          description: "Subscription cancellation resumed",
        },
      });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Manage subscription error:", error);
    return NextResponse.json(
      { error: "Failed to manage subscription" },
      { status: 500 }
    );
  }
}
