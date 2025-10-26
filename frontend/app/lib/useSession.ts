"use client";
import useSWR from "swr";

type SessionData =
  | { authenticated: false; error?: string }
  | { authenticated: true; user: { id: string; display_name?: string; email?: string } };

const fetcher = (u: string) => fetch(u, { credentials: "include" }).then(r => r.json());

export function useSession() {
  const { data, error, isLoading, mutate } = useSWR<SessionData>("/api/session", fetcher, {
    shouldRetryOnError: false,
  });
  const authenticated = data?.authenticated === true;
  const user = authenticated ? (data as any).user : null;
  return { authenticated, user, isLoading, error, refresh: mutate };
}
