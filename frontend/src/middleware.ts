import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  // Define protected routes
  const protectedRoutes = ['/dashboard'];
  
  // Check if the current path is protected
  const isProtectedRoute = protectedRoutes.some(route => 
    request.nextUrl.pathname.startsWith(route)
  );

  if (isProtectedRoute) {
    // Check for access_token cookie
    const token = request.cookies.get('access_token');
    
    if (!token) {
      const loginUrl = new URL('/login', request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/profile/:path*',
  ],
};
