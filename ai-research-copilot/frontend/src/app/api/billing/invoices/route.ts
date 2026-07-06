import { NextRequest, NextResponse } from "next/server";
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

export async function GET(request: NextRequest) {
  try {
    const userId = await getUserId(request);
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const customer = await prisma.stripeCustomer.findUnique({
      where: { userId },
    });

    if (!customer) {
      return NextResponse.json({ invoices: [] });
    }

    const invoices = await prisma.invoice.findMany({
      where: { stripeCustomerId: customer.stripeCustomerId },
      orderBy: { createdAt: "desc" },
      take: 50,
    });

    return NextResponse.json({ invoices });
  } catch (error) {
    console.error("Get invoices error:", error);
    return NextResponse.json(
      { error: "Failed to get invoices" },
      { status: 500 }
    );
  }
}
