import { NextResponse } from 'next/server';

export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
    try {
        const { id } = await context.params;

        if (!id) {
            return NextResponse.json({ detail: "ID is required" }, { status: 400 });
        }

        const BACKEND_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000';
        const API_KEY = process.env.API_KEY;

        if (!API_KEY) {
            console.error("CRITICAL: API_KEY environment variable is missing!");
            return NextResponse.json({ detail: "Server Configuration Error" }, { status: 500 });
        }

        const response = await fetch(`${BACKEND_URL}/status/${id}`, {
            method: 'GET',
            headers: {
                'X-API-Key': API_KEY,
            },
        });

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });

    } catch (error) {
        console.error("Proxy Status Error:", error);
        return NextResponse.json({ detail: "Internal Server Error" }, { status: 500 });
    }
}
