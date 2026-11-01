import { NextResponse, type NextRequest } from "next/server";

const PROTECTED = ["/dashboard", "/vocabulary", "/settings"];
const AUTH_PAGES = ["/login", "/register"];
const COOKIE = "sv_session";

// Fast redirect based on cookie presence. The API still validates every request;
// an expired cookie is caught there and the client redirects to /login.
export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const hasSession = Boolean(req.cookies.get(COOKIE)?.value);
  if (!hasSession && PROTECTED.some((p) => pathname.startsWith(p))) {
    const url = new URL("/login", req.url);
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }
  if (hasSession && AUTH_PAGES.includes(pathname)) {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/dashboard/:path*", "/vocabulary/:path*", "/settings/:path*", "/login", "/register"] };
