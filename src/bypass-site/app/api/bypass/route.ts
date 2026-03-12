import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const url = body.url;
    const webhook_url = body.webhook_url;

    if (!url) {
      return NextResponse.json({ detail: "URL is required" }, { status: 400 });
    }

    const BACKEND_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
    const API_KEY = process.env.API_KEY;

    if (!API_KEY) {
      console.error("CRITICAL: API_KEY environment variable is missing!");
      return NextResponse.json({ detail: "Server Configuration Error" }, { status: 500 });
    }

    const response = await fetch(`${BACKEND_URL}/bypass`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
      body: JSON.stringify({ url, webhook_url }),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });

  } catch (error) {
    console.error("Proxy Bypass Error:", error);
    return NextResponse.json({ detail: "Internal Server Error" }, { status: 500 });
  }
}
