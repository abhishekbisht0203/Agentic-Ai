import Stripe from "stripe";

const globalForStripe = globalThis as unknown as {
  stripe: Stripe | undefined;
};

export const stripe =
  globalForStripe.stripe ??
  new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: "2025-02-24.acacia",
    typescript: true,
    appInfo: {
      name: "ARC - AI Research Copilot",
      version: "1.0.0",
      url: process.env.NEXT_PUBLIC_APP_URL,
    },
  });

if (process.env.NODE_ENV !== "production") globalForStripe.stripe = stripe;
