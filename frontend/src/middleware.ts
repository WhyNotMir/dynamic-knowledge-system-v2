import { NextResponse, type NextRequest } from 'next/server'

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const PUBLIC_SEGMENTS = new Set(['projects'])

export function middleware(request: NextRequest) {
  const firstSegment = request.nextUrl.pathname.split('/').filter(Boolean)[0]
  if (!firstSegment || PUBLIC_SEGMENTS.has(firstSegment)) {
    return NextResponse.next()
  }

  if (!UUID_PATTERN.test(firstSegment)) {
    return NextResponse.redirect(new URL('/projects', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next|favicon.ico|.*\\..*).*)'],
}
