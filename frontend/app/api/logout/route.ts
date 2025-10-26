import { NextResponse } from "next/server";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001";

export async function POST(req: Request) {
  const res = await fetch(`${API_BASE}/auth/logout`, {
    method: "POST",
    headers: { cookie: req.headers.get("cookie") ?? "" },
  });
  return NextResponse.json({}, { status: res.ok ? 200 : res.status });
}
