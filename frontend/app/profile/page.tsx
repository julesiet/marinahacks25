"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/app/lib/useSession";
import Link from "next/link";
import * as React from "react";

export default function ProfilePage() {
  const router = useRouter();
  const { authenticated, user, isLoading } = useSession();

  useEffect(() => {
    if (!isLoading && !authenticated) router.push("/login");
  }, [isLoading, authenticated, router]);

  if (isLoading) return <p className="p-6">Checking session…</p>;
  if (!authenticated) return null;

  return (
    <main className="p-6 space-y-3">
      <h1 className="text-2xl font-semibold">
        Hello{user?.display_name ? `, ${user.display_name}` : ""}!
      </h1>
      <p className="text-sm text-neutral-600">Signed in as {user?.email ?? user?.id}.</p>
      <Link href="/builder"> WOOHOO! A LINK TO CHAT! MAYBE! </Link>
      <TopArtists />

      <button
        onClick={async () => {
            await fetch("/api/logout", { method: "POST", credentials: "include" });
            window.location.href = "/login";
        }}
        className="rounded-full border px-4 py-2"
        >
        Log out
        </button>
    </main>
  );
}

function TopArtists() {
  const [data, setData] = React.useState<any>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    fetch("/api/spotify/top-artists", { credentials: "include" })
      .then(r => (r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`)))
      .then(setData)
      .catch(e => setError(String(e)));
  }, []);

  if (error) return <p className="text-red-600">Failed to load: {error}</p>;
  if (!data) return <p>Loading your top artists…</p>;

  return (
    <ul className="mt-4 space-y-2">
      {data.items?.map((a: any) => (
        <li key={a.id} className="rounded border p-3">{a.name}</li>
      ))}
    </ul>
  );
}
