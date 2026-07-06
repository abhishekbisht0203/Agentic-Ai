import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/api/webhooks/stripe")) {
    const response = NextResponse.next();
    response.headers.set("x-webhook-path", pathname);
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/webhooks/:path*"],
};
