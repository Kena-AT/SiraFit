import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  // Define protected routes
  const protectedRoutes = ['/dashboard'];
  
  // Check if the current path is protected
  const isProtectedRoute = protectedRoutes.some(route => 
    request.nextUrl.pathname.startsWith(route)
  );

  if (isProtectedRoute) {
    // For now, allow access - in production, check for auth token
    // This would involve checking cookies, headers, or local storage
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/profile/:path*',
  ],
};
