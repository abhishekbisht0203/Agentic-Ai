import { NextRequest, NextResponse } from "next/server";
import { stripe } from "@/lib/stripe";
import { prisma } from "@/lib/prisma";
import Stripe from "stripe";

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  const userId = session.metadata?.userId;
  const priceId = session.metadata?.priceId;

  if (!session.customer || !session.subscription) {
    console.error("Checkout completed without customer or subscription");
    return;
  }

  const subscription = await stripe.subscriptions.retrieve(
    session.subscription as string
  );

  const priceItem = subscription.items.data[0];
  if (!priceItem) {
    console.error("Subscription has no items");
    return;
  }

  const stripePriceId = priceItem.price.id;
  const stripeProductId = priceItem.price.product as string;

  let planRecord = await prisma.plan.findFirst({
    where: { stripeProductId },
  });

  if (!planRecord) {
    const product = await stripe.products.retrieve(stripeProductId);
    const slug =
      product.metadata?.slug ||
      product.name.toLowerCase().replace(/\s+/g, "-");

    planRecord = await prisma.plan.create({
      data: {
        stripeProductId,
        name: product.name,
        slug,
        description: product.description,
      },
    });
  }

  let planPrice = await prisma.planPrice.findFirst({
    where: { stripePriceId },
  });

  if (!planPrice) {
    planPrice = await prisma.planPrice.create({
      data: {
        planId: planRecord.id,
        stripePriceId,
        stripeProductId,
        currency: priceItem.price.currency,
        amount: priceItem.price.unit_amount || 0,
        interval: priceItem.price.recurring?.interval || "month",
        intervalCount: priceItem.price.recurring?.interval_count || 1,
      },
    });
  }

  const customerId = session.customer as string;

  let customer = await prisma.stripeCustomer.findFirst({
    where: { stripeCustomerId: customerId },
  });

  if (!customer && userId) {
    customer = await prisma.stripeCustomer.findUnique({
      where: { userId },
    });
    if (customer) {
      customer = await prisma.stripeCustomer.update({
        where: { id: customer.id },
        data: { stripeCustomerId: customerId },
      });
    }
  }

  if (!customer) {
    console.error("No customer found for checkout session");
    return;
  }

  await prisma.subscription.create({
    data: {
      stripeSubscriptionId: subscription.id,
      stripeCustomerId: customerId,
      stripePriceId,
      planId: planRecord.id,
      planPriceId: planPrice.id,
      status: subscription.status,
      interval: priceItem.price.recurring?.interval || "month",
      currency: priceItem.price.currency,
      amount: priceItem.price.unit_amount || 0,
      currentPeriodStart: new Date(
        (subscription as any).current_period_start * 1000
      ),
      currentPeriodEnd: new Date(
        (subscription as any).current_period_end * 1000
      ),
      cancelAtPeriodEnd: subscription.cancel_at_period_end || false,
      trialStart: subscription.trial_start
        ? new Date(subscription.trial_start * 1000)
        : null,
      trialEnd: subscription.trial_end
        ? new Date(subscription.trial_end * 1000)
        : null,
    },
  });

  await prisma.billingHistory.create({
    data: {
      stripeCustomerId: customerId,
      type: "subscription_created",
      description: `Subscribed to ${planRecord.name}`,
      metadata: {
        planId: planRecord.id,
        planName: planRecord.name,
        interval: priceItem.price.recurring?.interval,
      },
    },
  });
}

async function handleSubscriptionUpdated(subscription: Stripe.Subscription) {
  const sub = await prisma.subscription.findUnique({
    where: { stripeSubscriptionId: subscription.id },
  });

  if (!sub) {
    console.error("Subscription not found:", subscription.id);
    return;
  }

  const priceItem = subscription.items.data[0];
  const newPriceId = priceItem?.price.id;
  const newStatus = subscription.status;

  let newPlanId = sub.planId;
  let newPlanPriceId = sub.planPriceId;

  if (newPriceId && newPriceId !== sub.stripePriceId) {
    const newPlanPrice = await prisma.planPrice.findFirst({
      where: { stripePriceId: newPriceId },
    });
    if (newPlanPrice) {
      newPlanPriceId = newPlanPrice.id;
      newPlanId = newPlanPrice.planId;
    }
  }

  await prisma.subscription.update({
    where: { id: sub.id },
    data: {
      status: newStatus,
      stripePriceId: newPriceId || sub.stripePriceId,
      planId: newPlanId,
      planPriceId: newPlanPriceId,
      interval: priceItem?.price.recurring?.interval || sub.interval,
      currency: priceItem?.price.currency || sub.currency,
      amount: priceItem?.price.unit_amount || sub.amount,
      currentPeriodStart: new Date(
        (subscription as any).current_period_start * 1000
      ),
      currentPeriodEnd: new Date(
        (subscription as any).current_period_end * 1000
      ),
      cancelAtPeriodEnd: subscription.cancel_at_period_end || false,
      canceledAt: subscription.canceled_at
        ? new Date(subscription.canceled_at * 1000)
        : null,
    },
  });

  const eventType =
    newStatus === "canceled" ? "subscription_canceled" : "subscription_updated";
  const description =
    newStatus === "canceled"
      ? "Subscription canceled"
      : "Subscription updated";

  await prisma.billingHistory.create({
    data: {
      stripeCustomerId: sub.stripeCustomerId,
      type: eventType,
      description,
      metadata: {
        status: newStatus,
        cancelAtPeriodEnd: subscription.cancel_at_period_end,
      },
    },
  });
}

async function handleSubscriptionDeleted(subscription: Stripe.Subscription) {
  const sub = await prisma.subscription.findUnique({
    where: { stripeSubscriptionId: subscription.id },
  });

  if (!sub) return;

  await prisma.subscription.update({
    where: { id: sub.id },
    data: {
      status: "canceled",
      canceledAt: new Date(),
    },
  });

  await prisma.billingHistory.create({
    data: {
      stripeCustomerId: sub.stripeCustomerId,
      type: "subscription_canceled",
      description: "Subscription permanently canceled",
    },
  });
}

async function handleInvoicePaid(invoice: Stripe.Invoice) {
  const customerId = invoice.customer as string;
  const subscriptionId = (invoice as unknown as Record<string, unknown>).subscription as string | null;

  let dbSubId: string | null = null;
  if (subscriptionId) {
    const sub = await prisma.subscription.findUnique({
      where: { stripeSubscriptionId: subscriptionId },
    });
    dbSubId = sub?.id || null;
  }

  await prisma.invoice.create({
    data: {
      stripeInvoiceId: invoice.id,
      stripeCustomerId: customerId,
      subscriptionId: dbSubId,
      amount: invoice.amount_paid,
      currency: invoice.currency,
      status: "paid",
      invoiceNumber: invoice.number,
      invoiceUrl: invoice.hosted_invoice_url,
      pdfUrl: invoice.invoice_pdf,
      periodStart: invoice.period_start
        ? new Date(invoice.period_start * 1000)
        : null,
      periodEnd: invoice.period_end
        ? new Date(invoice.period_end * 1000)
        : null,
      paidAt: new Date(),
    },
  });

  await prisma.payment.create({
    data: {
      stripeInvoiceId: invoice.id,
      stripeCustomerId: customerId,
      subscriptionId: dbSubId,
      amount: invoice.amount_paid,
      currency: invoice.currency,
      status: "succeeded",
    },
  });

  await prisma.billingHistory.create({
    data: {
      stripeCustomerId: customerId,
      type: "payment_succeeded",
      description: `Payment of ${(invoice.amount_paid / 100).toFixed(2)} ${invoice.currency.toUpperCase()} received`,
      metadata: {
        invoiceId: invoice.id,
        amount: invoice.amount_paid,
        currency: invoice.currency,
      },
    },
  });
}

async function handleInvoicePaymentFailed(invoice: Stripe.Invoice) {
  const customerId = invoice.customer as string;
  const subscriptionId = (invoice as unknown as Record<string, unknown>).subscription as string | null;

  let dbSubId: string | null = null;
  if (subscriptionId) {
    const sub = await prisma.subscription.findUnique({
      where: { stripeSubscriptionId: subscriptionId },
    });
    dbSubId = sub?.id || null;
  }

  await prisma.payment.create({
    data: {
      stripeInvoiceId: invoice.id,
      stripeCustomerId: customerId,
      subscriptionId: dbSubId,
      amount: invoice.amount_due,
      currency: invoice.currency,
      status: "failed",
      failureReason: invoice.last_finalization_error?.message || "Payment failed",
    },
  });

  if (dbSubId) {
    await prisma.subscription.update({
      where: { id: dbSubId },
      data: { status: "past_due" },
    });
  }

  await prisma.billingHistory.create({
    data: {
      stripeCustomerId: customerId,
      type: "payment_failed",
      description: `Payment of ${(invoice.amount_due / 100).toFixed(2)} ${invoice.currency.toUpperCase()} failed`,
      metadata: {
        invoiceId: invoice.id,
        amount: invoice.amount_due,
        currency: invoice.currency,
        error: invoice.last_finalization_error?.message,
      },
    },
  });
}

async function handleTrialWillEnd(subscription: Stripe.Subscription) {
  const sub = await prisma.subscription.findUnique({
    where: { stripeSubscriptionId: subscription.id },
  });

  if (!sub) return;

  await prisma.billingHistory.create({
    data: {
      stripeCustomerId: sub.stripeCustomerId,
      type: "subscription_updated",
      description: "Trial period will end soon",
      metadata: {
        trialEnd: subscription.trial_end
          ? new Date(subscription.trial_end * 1000).toISOString()
          : null,
      },
    },
  });
}

const processedEvents = new Set<string>();

export async function POST(request: NextRequest) {
  const body = await request.text();
  const signature = request.headers.get("stripe-signature");

  if (!signature) {
    return NextResponse.json(
      { error: "Missing stripe-signature header" },
      { status: 400 }
    );
  }

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    console.error("Webhook signature verification failed:", err);
    return NextResponse.json(
      { error: "Invalid signature" },
      { status: 400 }
    );
  }

  if (processedEvents.has(event.id)) {
    return NextResponse.json({ received: true, duplicate: true });
  }

  try {
    switch (event.type) {
      case "checkout.session.completed":
        await handleCheckoutCompleted(
          event.data.object as Stripe.Checkout.Session
        );
        break;

      case "customer.subscription.created":
      case "customer.subscription.updated":
        await handleSubscriptionUpdated(
          event.data.object as Stripe.Subscription
        );
        break;

      case "customer.subscription.deleted":
        await handleSubscriptionDeleted(
          event.data.object as Stripe.Subscription
        );
        break;

      case "invoice.paid":
        await handleInvoicePaid(event.data.object as Stripe.Invoice);
        break;

      case "invoice.payment_failed":
        await handleInvoicePaymentFailed(
          event.data.object as Stripe.Invoice
        );
        break;

      case "customer.subscription.trial_will_end":
        await handleTrialWillEnd(
          event.data.object as Stripe.Subscription
        );
        break;

      case "customer.subscription.paused":
      case "customer.subscription.resumed": {
        const sub = event.data.object as Stripe.Subscription;
        const dbSub = await prisma.subscription.findUnique({
          where: { stripeSubscriptionId: sub.id },
        });
        if (dbSub) {
          await prisma.subscription.update({
            where: { id: dbSub.id },
            data: { status: sub.status },
          });
        }
        break;
      }

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    processedEvents.add(event.id);

    if (processedEvents.size > 10000) {
      const iterator = processedEvents.values();
      for (let i = 0; i < 1000; i++) {
        processedEvents.delete(iterator.next().value!);
      }
    }
  } catch (error) {
    console.error(`Error processing event ${event.type}:`, error);
    return NextResponse.json(
      { error: "Webhook processing failed" },
      { status: 500 }
    );
  }

  return NextResponse.json({ received: true });
}
