"use client";

import * as React from "react";

type LoginButtonProps = {
  className?: string;
  children?: React.ReactNode; // custom label if you don't want the default text
  apiBaseUrl?: string;        // override for tests; otherwise uses NEXT_PUBLIC_API_URL or localhost
};

export default function LoginButton({
  className,
  children = "Log in with Spotify",
  apiBaseUrl,
}: LoginButtonProps) {
  const [isLoading, setIsLoading] = React.useState(false);

  const API_BASE =
    apiBaseUrl ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:3001";
    
const handleClick = () => {
  setIsLoading(true);
  // add redirect_to so backend knows where to return after Spotify auth
  window.location.href = `${API_BASE}/auth/login?redirect_to=/builder`;
};

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label="Log in with Spotify"
      disabled={isLoading}
      className={[
        "inline-flex items-center gap-2 rounded-full px-8 py-4",
        "font-medium tracking-tight",
        "bg-[#F9F0F2] text-[#061E23] text-xl hover:bg-blue-100",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-200",
        "disabled:opacity-60 disabled:cursor-not-allowed",
        className || "",
      ].join(" ")}
      data-testid="login-button"
    >
      {isLoading ? (
        <span
          aria-hidden
          className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
        />
      ) : (
        <SpotifyGlyph className="h-4 w-4" />
      )}
      <span>{children}</span>
    </button>
  );
}

// tiny spotify svg so i don't need a big ahh line 
function SpotifyGlyph(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
    <path d="M8 0a8 8 0 1 0 0 16A8 8 0 0 0 8 0m3.669 11.538a.5.5 0 0 1-.686.165c-1.879-1.147-4.243-1.407-7.028-.77a.499.499 0 0 1-.222-.973c3.048-.696 5.662-.397 7.77.892a.5.5 0 0 1 .166.686m.979-2.178a.624.624 0 0 1-.858.205c-2.15-1.321-5.428-1.704-7.972-.932a.625.625 0 0 1-.362-1.194c2.905-.881 6.517-.454 8.986 1.063a.624.624 0 0 1 .206.858m.084-2.268C10.154 5.56 5.9 5.419 3.438 6.166a.748.748 0 1 1-.434-1.432c2.825-.857 7.523-.692 10.492 1.07a.747.747 0 1 1-.764 1.288"/>
    </svg>
  );
}
