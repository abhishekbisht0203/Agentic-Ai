import { NextRequest, NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe";
import { prisma } from "@/lib/prisma";
import { detectCountryFromRequest, getCurrencyForCountry } from "@/lib/billing";

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
    const { priceId, interval } = body;

    if (!priceId || !interval) {
      return NextResponse.json(
        { error: "priceId and interval are required" },
        { status: 400 }
      );
    }

    const detection = detectCountryFromRequest(request);
    const currency = getCurrencyForCountry(detection.country);

    let customer = await prisma.stripeCustomer.findUnique({
      where: { userId },
    });

    if (!customer) {
      const user = await prisma.stripeCustomer.findFirst({
        where: { userId },
      });

      if (!user) {
        const stripeCustomer = await getStripe().customers.create({
          metadata: { userId },
        });

        customer = await prisma.stripeCustomer.create({
          data: {
            userId,
            stripeCustomerId: stripeCustomer.id,
            country: detection.country,
            currency,
          },
        });
      } else {
        customer = user;
      }
    }

    const existingSub = await prisma.subscription.findFirst({
      where: {
        stripeCustomerId: customer.stripeCustomerId,
        status: { in: ["active", "trialing", "past_due"] },
      },
    });

    if (existingSub) {
      return NextResponse.json(
        { error: "You already have an active subscription. Please manage it from the billing portal." },
        { status: 400 }
      );
    }

    const successUrl =
      process.env.NEXT_PUBLIC_STRIPE_SUCCESS_URL ||
      `${process.env.NEXT_PUBLIC_APP_URL}/settings/billing?success=true`;
    const cancelUrl =
      process.env.NEXT_PUBLIC_STRIPE_CANCEL_URL ||
      `${process.env.NEXT_PUBLIC_APP_URL}/settings/billing?canceled=true`;

    const session = await getStripe().checkout.sessions.create({
      customer: customer.stripeCustomerId,
      mode: "subscription",
      payment_method_types: ["card"],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${successUrl}&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: cancelUrl,
      metadata: {
        userId,
        priceId,
        interval,
      },
      subscription_data: {
        metadata: {
          userId,
          priceId,
        },
      },
      billing_address_collection: "auto",
      tax_id_collection: { enabled: true },
      locale: "auto",
    });

    return NextResponse.json({
      sessionId: session.id,
      url: session.url,
    });
  } catch (error) {
    console.error("Checkout session error:", error);
    return NextResponse.json(
      { error: "Failed to create checkout session" },
      { status: 500 }
    );
  }
}
