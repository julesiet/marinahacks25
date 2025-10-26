'use client';

import { useEffect, useRef, useState } from 'react';
import Link from "next/link";
import Vinyl from "../components/vinyl";

// Message type representing either a user or assistant chat message.
// CHANGED: content can now be React nodes (so we can include an iframe)
type Msg = { id: string; role: 'user' | 'assistant'; content: React.ReactNode };

// Base URL for the backend API.  It reads from NEXT_PUBLIC_API_URL at build/runtime,
// but falls back to the local FastAPI default if not set.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:3001';

// Convert a regular Spotify playlist URL to an embeddable URL.
function toSpotifyEmbedSrc(url: string) {
  try {
    const u = new URL(url);
    const parts = u.pathname.split('/');
    const idx = parts.indexOf('playlist');
    const id = idx >= 0 ? parts[idx + 1] : undefined;
    if (id) return `https://open.spotify.com/embed/playlist/${id}`;
  } catch {
    // fall through
  }
  // last segment fallback
  const id = url.split('?')[0].split('/').pop();
  return `https://open.spotify.com/embed/playlist/${id}`;
}

export default function BuilderPage() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      id: 'intro',
      role: 'assistant',
      content: 'Welcome to DJ MegaJelli’s booth. Drop your vibe below.',
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  // Scroll to the bottom when new messages arrive.
  useEffect(() => {
    listRef.current?.lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  // Extract the user id from the URL on mount and persist it.  This allows API calls
  // to include the logged-in Spotify user’s id.
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const uid = params.get('user');
      if (uid) {
        localStorage.setItem('spotify_user_id', uid);
      }
    }
  }, []);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    const userMsg: Msg = { id: crypto.randomUUID(), role: 'user', content: text };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setSending(true);

    // Retrieve the Spotify user id; show a login prompt if missing.
    const userId = typeof window !== 'undefined' ? localStorage.getItem('spotify_user_id') : null;
    if (!userId) {
      const botMsg: Msg = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `You’re not logged in. Please return to the login page and authenticate with Spotify.`,
      };
      setMessages((m) => [...m, botMsg]);
      setSending(false);
      return;
    }

    try {
      // 1) Generate track suggestions for the vibe.
      const genResp = await fetch(`${API_BASE}/vibe/generate_llm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: userId, vibeText: text, count: 10 }),
      });
      const genData = await genResp.json();

      let trackSummary = '';
      if (genResp.ok && Array.isArray(genData.tracks) && genData.tracks.length > 0) {
        // Use the `artist` property returned by the backend; if unavailable, fall back to any
        // nested artists array or object.  This avoids blank artist fields.
        const lines = genData.tracks.map((t: any, idx: number) => {
          const artists: string =
            t.artist || (Array.isArray(t.artists) ? t.artists.join(', ') : (t.artists?.name ?? ''));
          return `${idx + 1}. ${t.name} – ${artists}`;
        });
        trackSummary = lines.join('\n');
      } else {
        trackSummary = 'Sorry, I couldn’t find any tracks for that vibe. Try refining your description.';
      }

      // 2) Create a playlist for the vibe and get the Spotify URL.
      const playlistResp = await fetch(`${API_BASE}/vibe/one_click_playlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: userId, vibeText: text, count: 10 }),
      });
      const plData = await playlistResp.json();
      const playlistUrl: string | undefined = (playlistResp.ok && plData?.url) ? plData.url : undefined;

      // Build one React node that includes the text summary and (optionally) the embedded player.
      const embedSrc = playlistUrl ? toSpotifyEmbedSrc(playlistUrl) : undefined;
      const responseNode = (
        <>
          <div className="whitespace-pre-wrap">{trackSummary}</div>
          {embedSrc && (
            <div className="mt-4">
              <iframe
                data-testid="embed-iframe"
                style={{ borderRadius: 12 }}
                src={embedSrc}
                width="100%"
                height="152"
                frameBorder={0}
                allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
                loading="lazy"
              />
            </div>
          )}
        </>
      );

      const botMsg: Msg = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: responseNode,
      };
      setMessages((m) => [...m, botMsg]);
    } catch (err) {
      const botMsg: Msg = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Oops! Something went wrong while generating your playlist. Please try again later.`,
      };
      setMessages((m) => [...m, botMsg]);
    }
    setSending(false);
  };

  return (
    <main className="grid min-h-dvh grid-cols-1 overflow-x-hidden lg:grid-cols-[380px_1fr]">
      {/* left side: vinyl art and back home link */}
      <section className="relative hidden bg-[#2A6F86] lg:block">
        <Link href="/" className="group absolute left-4 top-4 z-10" aria-label="Back home">
          <span
            className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-white/10 text-[#F9F0F2] ring-1 ring-white/20 backdrop-blur transition hover:bg-white/20"
          >
            <span aria-hidden>←</span>
            <span className="underline decoration-transparent group-hover:decoration-inherit">
              Back home
            </span>
          </span>
        </Link>
        <div className="absolute top-1/2 -translate-y-1/2 -left-80 md:-left-70">
          <Vinyl src="/jellyvinyl.png" alt="" size={620} speed={6} />
        </div>
      </section>

      {/* right side: chat interface */}
      <section className="relative min-h-dvh overflow-hidden">
        <div aria-hidden="true" className="absolute inset-0 z-0 backdrop-blur bg-black/10" />
        <div className="relative z-10 mx-auto flex h-dvh max-w-3xl flex-col gap-4 p-6 text-[#F9F0F2]">
          <h1
            className="text-6xl text-center font-extrabold drop-shadow"
            style={{ fontFamily: 'Bodega, system-ui, sans-serif' }}
          >
            DJ MEGAJELLI
          </h1>
          <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-1">
            {messages.map((m) => (
              <ChatBubble key={m.id} role={m.role}>
                {m.content}
              </ChatBubble>
            ))}
          </div>
          <ChatInput value={input} onChange={setInput} onSend={send} disabled={sending} />
        </div>
      </section>
    </main>
  );
}

function ChatBubble({ role, children }: { role: 'user' | 'assistant'; children: React.ReactNode }) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex items-end gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {isUser ? <UserAvatar /> : <RobotAvatar />}
        <div
          className={[
            'max-w-[70ch] whitespace-pre-wrap rounded-3xl px-5 py-3 shadow-md leading-relaxed',
            isUser ? 'bg-[#F9F0F2] text-slate-900' : 'bg-white/20 text-[#F9F0F2] backdrop-blur-md',
          ].join(' ')}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

function UserAvatar() {
  return (
    <div className="size-10 shrink-0 rounded-full bg-[#F9F0F2] ring-2 ring-white/20 shadow flex items-center justify-center">
      <svg viewBox="0 0 24 24" className="h-6 w-6" aria-hidden="true">
        <circle cx="12" cy="8" r="4" fill="#475569" />
        <path d="M4 20c0-3.3137 3.134-6 8-6s8 2.6863 8 6" fill="#475569" />
      </svg>
    </div>
  );
}

function RobotAvatar() {
  return (
    <div className="size-10 shrink-0 rounded-full bg-teal-600/80 ring-2 ring-white/30 shadow flex items-center justify-center">
      <svg viewBox="0 0 24 24" className="h-6 w-6" role="img" aria-label="Robot">
        <circle cx="12" cy="3" r="1.5" fill="white" />
        <rect x="11.5" y="4" width="1" height="2.5" fill="white" />
        <rect x="5" y="7" width="14" height="10" rx="2" fill="white" />
        <circle cx="9" cy="12" r="1.5" fill="#0f172a" />
        <circle cx="15" cy="12" r="1.5" fill="#0f172a" />
        <rect x="8" y="14.5" width="8" height="1.5" rx="0.75" fill="#0f172a" />
      </svg>
    </div>
  );
}

function ChatInput({
  value,
  onChange,
  onSend,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
}) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSend();
      }}
      className="flex items-center gap-3 rounded-full bg-[#F9F0F2] p-2 pl-5 shadow"
    >
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Type your message…"
        className="w-full bg-transparent text-slate-900 placeholder-slate-500 focus:outline-none"
      />
      <button
        type="submit"
        disabled={disabled}
        className="rounded-full px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-white/70 disabled:opacity-50"
        aria-label="Send message"
      >
        Send
      </button>
    </form>
  );
}
