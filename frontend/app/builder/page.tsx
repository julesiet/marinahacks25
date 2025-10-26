'use client';

import { useEffect, useRef, useState } from 'react';
import Link from "next/link";
import Vinyl from "../components/vinyl";

type Msg = { id: string; role: 'user' | 'assistant'; content: string };

export default function BuilderPage() {
  const [messages, setMessages] = useState<Msg[]>([
    { id: 'intro', role: 'assistant', content: 'Welcome to DJ Megajelli’s booth. Drop your vibe below.' },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listRef.current?.lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg: Msg = { id: crypto.randomUUID(), role: 'user', content: text };
    setMessages(m => [...m, userMsg]);
    setInput('');
    setSending(true);

    await new Promise(r => setTimeout(r, 500));
    const botMsg: Msg = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: `Echoing your groove: “${text}”. (mock reply)`,
    };
    setMessages(m => [...m, botMsg]);
    setSending(false);
  };

  return (
    <main className="grid min-h-dvh grid-cols-1 overflow-x-hidden lg:grid-cols-[380px_1fr]">
      {/* left side, vinyl + go back home + block — UNCHANGED */}
      <section className="relative hidden bg-[#2A6F86] lg:block">
        <Link href="/" className="underline">← Back home</Link>
        <div className="absolute top-1/2 -translate-y-1/2 -left-80 md:-left-70">
          <Vinyl
            src="/jellyvinyl.png"
            alt=""
            size={620}
            speed={6}
          />
        </div>
      </section>

      {/* right side, message + chat stuff with avatars */}
      <section className="relative min-h-dvh overflow-hidden">
        {/* Blur the GLOBAL backdrop behind this page (text stays crisp) */}
        <div aria-hidden="true" className="absolute inset-0 z-0 backdrop-blur bg-black/10" />

        {/* Chat surface */}
        <div className="relative z-10 mx-auto flex h-dvh max-w-3xl flex-col gap-4 p-6 text-[#F9F0F2]">
          <h1 className="text-6xl text-center font-extrabold drop-shadow" style={{ fontFamily: 'Bodega, system-ui, sans-serif' }}>DJ MEGAJELLI BUILDER</h1>

          {/* Messages */}
          <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-1">
            {messages.map(m => (
              <ChatBubble key={m.id} role={m.role}>
                {m.content}
              </ChatBubble>
            ))}
          </div>

          {/* Input */}
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={send}
            disabled={sending}
          />
        </div>
      </section>
    </main>
  );
}

function ChatBubble({
  role,
  children,
}: {
  role: 'user' | 'assistant';
  children: React.ReactNode;
}) {
  const isUser = role === 'user';

  // Layout: assistant (avatar left → bubble), user (bubble → avatar right)
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex items-end gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        {isUser ? <UserAvatar /> : <RobotAvatar />}

        {/* Bubble */}
        <div
          className={[
            'max-w-[70ch] whitespace-pre-wrap rounded-3xl px-5 py-3 shadow-md leading-relaxed',
            isUser
              ? 'bg-[#F9F0F2] text-slate-900'                // user: light bubble, dark text
              : 'bg-white/20 text-[#F9F0F2] backdrop-blur-md' // assistant: translucent bubble, light text
          ].join(' ')}
        >
          {children}
        </div>
      </div>
    </div>
  );
}

/** Neutral user silhouette (blank-ish avatar) */
function UserAvatar() {
  return (
    <div className="size-10 shrink-0 rounded-full bg-[#F9F0F2] ring-2 ring-white/20 shadow flex items-center justify-center">
      <svg viewBox="0 0 24 24" className="h-6 w-6" aria-hidden="true">
        <circle cx="12" cy="8" r="4" fill="#475569" />
        <path d="M4 20c0-3.3137 3.134  -6 8 -6s8 2.6863 8 6" fill="#475569" />
      </svg>
    </div>
  );
}

/** Simple friendly robot head (copyright-safe inline SVG) */
function RobotAvatar() {
  return (
    <div className="size-10 shrink-0 rounded-full bg-teal-600/80 ring-2 ring-white/30 shadow flex items-center justify-center">
      <svg viewBox="0 0 24 24" className="h-6 w-6" role="img" aria-label="Robot">
        {/* antenna */}
        <circle cx="12" cy="3" r="1.5" fill="white" />
        <rect x="11.5" y="4" width="1" height="2.5" fill="white" />
        {/* head */}
        <rect x="5" y="7" width="14" height="10" rx="2" fill="white" />
        {/* eyes */}
        <circle cx="9" cy="12" r="1.5" fill="#0f172a" />
        <circle cx="15" cy="12" r="1.5" fill="#0f172a" />
        {/* mouth */}
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
