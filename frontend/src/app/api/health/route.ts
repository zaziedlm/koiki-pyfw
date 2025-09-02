import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Basic health check response
    return NextResponse.json(
      {
        status: 'ok',
        timestamp: new Date().toISOString(),
        service: 'koiki-frontend',
        version: process.env.npm_package_version || '0.1.0',
      },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      {
        status: 'error',
        timestamp: new Date().toISOString(),
        service: 'koiki-frontend',
        error: 'Health check failed',
      },
      { status: 500 }
    );
  }
}