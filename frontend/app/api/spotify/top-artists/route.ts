import { NextResponse } from "next/server";
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3001";

export async function GET(req: Request) {
  const res = await fetch(`${API_BASE}/spotify/top-artists`, {
    headers: { cookie: req.headers.get("cookie") ?? "" },
  });

  if (res.status === 401) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
