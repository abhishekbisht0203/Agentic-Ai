import { NextRequest, NextResponse } from "next/server";
import { getCurrentUsage, checkUsageLimit, incrementUsage } from "@/lib/billing/server";

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

    const usage = await getCurrentUsage(userId);
    return NextResponse.json({ usage });
  } catch (error) {
    console.error("Get usage error:", error);
    return NextResponse.json(
      { error: "Failed to get usage" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const userId = await getUserId(request);
    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();
    const { metric, quantity = 1 } = body;

    if (!metric) {
      return NextResponse.json(
        { error: "metric is required" },
        { status: 400 }
      );
    }

    const limitCheck = await checkUsageLimit(userId, metric);
    if (!limitCheck.allowed) {
      return NextResponse.json(
        {
          error: "Usage limit exceeded",
          current: limitCheck.current,
          limit: limitCheck.limit,
        },
        { status: 429 }
      );
    }

    await incrementUsage(userId, metric, quantity);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Track usage error:", error);
    return NextResponse.json(
      { error: "Failed to track usage" },
      { status: 500 }
    );
  }
}
