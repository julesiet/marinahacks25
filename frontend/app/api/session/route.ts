import { NextResponse } from "next/server";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001";

export async function GET(req: Request) {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { cookie: req.headers.get("cookie") ?? "" },
  });

  if (res.status === 401) {
    return NextResponse.json({ authenticated: false }, { status: 200 });
  }
  if (!res.ok) {
    return NextResponse.json({ authenticated: false, error: "upstream_error" }, { status: 200 });
  }

  const me = await res.json();
  return NextResponse.json({ authenticated: true, user: me }, { status: 200 });
}
