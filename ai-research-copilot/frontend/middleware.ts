import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedRoutes = ["/dashboard", "/chat", "/documents", "/knowledge", "/agents", "/workflows", "/analytics", "/settings", "/admin", "/reports", "/docs"];
const authRoutes = ["/login", "/register", "/forgot-password"];
const oauthCallbackRoutes = ["/auth/callback"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  const token = request.cookies.get("access_token")?.value || 
                request.headers.get("authorization")?.replace("Bearer ", "");

  const isProtectedRoute = protectedRoutes.some((route) => pathname.startsWith(route));
  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route));
  const isOAuthCallback = oauthCallbackRoutes.some((route) => pathname.startsWith(route));

  // Allow OAuth callback routes to pass through
  if (isOAuthCallback) {
    return NextResponse.next();
  }

  if (isProtectedRoute && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("redirect", pathname);
    return NextResponse.redirect(url);
  }

  if (isAuthRoute && token) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
